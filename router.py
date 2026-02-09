import requests
import json
import re
import logging


OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
BLOCKED_NATIVE_MARKERS = ('RECITATION', 'SAFETY', 'BLOCKED', 'PROHIBITED', 'FILTER')


def _extract_content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text_part = part.get('text')
                if isinstance(text_part, str):
                    parts.append(text_part)
        return '\n'.join(parts)
    return ''


def _strip_markdown_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    cleaned = cleaned.strip()
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _extract_first_json_object(text: str) -> str | None:
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    return None


def _parse_choice_content(choice: dict) -> dict | None:
    message = choice.get('message')
    if not isinstance(message, dict):
        message = {}
    content_text = _extract_content_text(message.get('content'))
    print(f"API response content: '{content_text}'")
    if not content_text.strip():
        print("Content is empty")
        return None

    cleaned = _strip_markdown_fence(content_text)
    print(f"Cleaned content: '{cleaned}'")

    candidates = [cleaned]
    extracted_json = _extract_first_json_object(cleaned)
    if extracted_json and extracted_json != cleaned:
        candidates.append(extracted_json)

    parse_error = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            parsed['raw_answer_text'] = candidate
            return parsed
        except json.JSONDecodeError as e:
            parse_error = e
    if parse_error is not None:
        print(f"JSON decode error: {parse_error}")
    return None


def _is_blocked_choice(choice: dict) -> bool:
    finish_reason = str(choice.get('finish_reason', '')).lower()
    native_finish = str(choice.get('native_finish_reason', '')).upper()
    if finish_reason == 'error':
        return True
    return any(marker in native_finish for marker in BLOCKED_NATIVE_MARKERS)


def _post_openrouter(headers: dict, payload: dict, timeout_s: float) -> dict:
    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout_s)
    print(f"API response status: {response.status_code}")
    if response.status_code in [401, 403]:
        return {'error': 'auth'}  # Authentication error
    if response.status_code >= 500:
        return {'error': 'server'}  # Server error
    response.raise_for_status()
    return {'result': response.json()}


def call_openrouter(image_data_url: str, model: str, api_key: str, enable_reasoning: bool = False, timeout_s: float = 2.0) -> dict | None:
    base_system_prompt = 'You are a quiz parser. Input is a cropped screenshot of a quiz. Return ONLY strict JSON. If multiple questions are visible, answer the TOPMOST one.'
    if enable_reasoning and is_model_supported(model):
        base_system_prompt += " Use chain-of-thought: think step by step before outputting JSON."
    if enable_reasoning and not is_model_supported(model):
        logging.info(f"Reasoning requested but ignored for unsupported model: {model}")
    user_text = '''Extract the question and answers and decide the correct answer(s). If it's multiple-choice, return "mode":"mcq" and "answer_indices" as a list of 0-based indices (even for single answer). Do not use "answer_index" for multiple-choice questions. If it's true/false, return 'mode':'tf' and 'answer_index' as 0 for True or 1 for False. If it's fill-in, return "mode":"fitb" and "answer_text". If it's an accounting journal entry question (scenario at top, outline in middle, journal entry at bottom), return "mode":"journal" and "answer_entries" as an array of strings in format "Account D/C Amount". Focus ONLY on the journal entry part at the bottom. If negation words like NOT/EXCEPT/LEAST appear, still pick the correct answer(s). JSON schema: {"mode": "mcq|fitb|journal|tf", "question": "string", "choices": ["string"], "answer_indices": [0], "answer_index": 0, "answer_text": "string", "answer_entries": ["string"], "confidence": 0.0}. Always include a 'confidence' field as a float from 0.0 to 1.0 estimating your confidence in the answer based on your reasoning. Output ONLY JSON.'''
    anti_recitation_suffix = " Do not copy quiz text verbatim. Paraphrase question and choices briefly in your own words and still return valid JSON only."
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'HTTP-Referer': 'https://quizpeek.app',
        'X-Title': 'QuizPeek'
    }

    blocked_seen = False
    parse_seen = False
    system_prompts = [base_system_prompt, base_system_prompt + anti_recitation_suffix]

    try:
        for attempt_idx, system_prompt in enumerate(system_prompts, start=1):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ]
            data = {
                'model': model,
                'messages': messages,
                'temperature': 0.0,
                'max_tokens': 15000
            }

            print(f"OpenRouter attempt {attempt_idx}/{len(system_prompts)}")
            api_result = _post_openrouter(headers, data, timeout_s)
            if 'error' in api_result:
                return api_result

            result = api_result['result']
            print(f"Full API result: {result}")
            if 'choices' not in result or not result['choices']:
                print("No choices in result")
                parse_seen = True
                continue

            choice = result['choices'][0]
            if _is_blocked_choice(choice):
                blocked_seen = True
                logging.warning(
                    "Model output was blocked/truncated (finish_reason=%s, native_finish_reason=%s)",
                    choice.get('finish_reason'),
                    choice.get('native_finish_reason')
                )

            parsed = _parse_choice_content(choice)
            if parsed is not None:
                return parsed
            parse_seen = True

            if blocked_seen and attempt_idx < len(system_prompts):
                logging.info("Retrying OpenRouter request with anti-recitation prompt")
                continue
            if attempt_idx < len(system_prompts):
                logging.info("Retrying OpenRouter request after parse failure")

        if blocked_seen:
            return {'error': 'blocked'}
        if parse_seen:
            return {'error': 'parse'}
        return {'error': 'parse'}
    except requests.exceptions.Timeout:
        print("API timeout")
        return {'error': 'timeout'}
    except requests.exceptions.RequestException as e:
        print(f"API network error: {e}")
        return {'error': 'network'}

def validate_result(obj: dict) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "Object is not a dict"
    
    required_keys = ['mode', 'question']
    for key in required_keys:
        if key not in obj:
            logging.warning(f"Missing or invalid key: {key} in response")
            return False, f"Missing key: {key}"
    
    if 'confidence' not in obj:
        logging.warning("Confidence field missing in response; defaulting to 1.0")
        obj['confidence'] = 1.0
    if not isinstance(obj['confidence'], (int, float)) or not (0.0 <= obj['confidence'] <= 1.0):
        logging.warning(f"Missing or invalid key: confidence in response")
        obj['confidence'] = 1.0
    
    if obj['mode'] not in ['mcq', 'fitb', 'journal', 'tf']:
        return False, "Invalid mode"
    
    if not isinstance(obj['question'], str):
        return False, "Question is not a string"
    
    
    if obj['mode'] == 'mcq':
        if 'choices' not in obj or not isinstance(obj['choices'], list) or not all(isinstance(c, str) for c in obj['choices']):
            return False, "Choices is not a list of strings"
        if 'answer_indices' not in obj or not isinstance(obj['answer_indices'], list) or not all(isinstance(i, int) and 0 <= i < len(obj['choices']) for i in obj['answer_indices']):
            return False, "Invalid answer_indices"
        # For backward compatibility, if answer_index exists, convert to list
        if 'answer_index' in obj and isinstance(obj['answer_index'], int):
            obj['answer_indices'] = [obj['answer_index']]
    elif obj['mode'] == 'fitb':
        if 'answer_text' not in obj or not isinstance(obj['answer_text'], str):
            return False, "Answer_text is not a string"
    elif obj['mode'] == 'journal':
        if 'answer_entries' not in obj or not isinstance(obj['answer_entries'], list) or not all(isinstance(entry, str) for entry in obj['answer_entries']):
            return False, "Answer_entries is not a list of strings"
    elif obj['mode'] == 'tf':
        if 'answer_index' not in obj or not isinstance(obj['answer_index'], int) or obj['answer_index'] not in [0, 1]:
            return False, "Invalid answer_index for tf"
        if 'choices' in obj:
            if not isinstance(obj['choices'], list) or len(obj['choices']) != 2 or not all(isinstance(c, str) for c in obj['choices']):
                return False, "Choices must be exactly two strings for tf"
            choices_lower = [c.lower() for c in obj['choices']]
            if not (('true' in choices_lower and 'false' in choices_lower) or ('t' in choices_lower and 'f' in choices_lower)):
                return False, "Choices must match True/False for tf"


    return True, ""


def is_model_supported(model: str) -> bool:
    vision_only_pattern = r'(llava|vision-only|image-only)'
    return not re.search(vision_only_pattern, model.lower())

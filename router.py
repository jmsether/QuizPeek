import requests
import json
import re
import logging

def call_openrouter(image_data_url: str, model: str, api_key: str, enable_reasoning: bool = False, timeout_s: float = 2.0) -> dict | None:
    system_prompt = 'You are a quiz parser. Input is a cropped screenshot of a quiz. Return ONLY strict JSON. If multiple questions are visible, answer the TOPMOST one.'
    if enable_reasoning and is_model_supported(model):
        system_prompt += " Use chain-of-thought: think step by step before outputting JSON."
    if enable_reasoning and not is_model_supported(model):
        logging.info(f"Reasoning requested but ignored for unsupported model: {model}")
    user_text = '''Extract the question and answers and decide the correct answer(s). If it's multiple-choice, return "mode":"mcq" and "answer_indices" as a list of 0-based indices (even for single answer). Do not use "answer_index" for multiple-choice questions. If it's true/false, return 'mode':'tf' and 'answer_index' as 0 for True or 1 for False. If it's fill-in, return "mode":"fitb" and "answer_text". If it's an accounting journal entry question (scenario at top, outline in middle, journal entry at bottom), return "mode":"journal" and "answer_entries" as an array of strings in format "Account D/C Amount". Focus ONLY on the journal entry part at the bottom. If negation words like NOT/EXCEPT/LEAST appear, still pick the correct answer(s). JSON schema: {"mode": "mcq|fitb|journal|tf", "question": "string", "choices": ["string"], "answer_indices": [0], "answer_index": 0, "answer_text": "string", "answer_entries": ["string"], "confidence": 0.0}. Always include a 'confidence' field as a float from 0.0 to 1.0 estimating your confidence in the answer based on your reasoning. Output ONLY JSON.'''
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ]}
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'HTTP-Referer': 'https://quizpeek.app',
        'X-Title': 'QuizPeek'
    }
    
    data = {
        'model': model,
        'messages': messages,
        'temperature': 0.0,
        'max_tokens': 15000
    }
    
    try:
        response = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=data, timeout=timeout_s)
        print(f"API response status: {response.status_code}")
        if response.status_code in [401, 403]:
            return {'error': 'auth'}  # Authentication error
        if response.status_code >= 500:
            return {'error': 'server'}  # Server error
        response.raise_for_status()
        result = response.json()
        print(f"Full API result: {result}")
        if 'choices' not in result or not result['choices']:
            print("No choices in result")
            return {'error': 'parse'}
        content = result['choices'][0]['message']['content']
        print(f"API response content: '{content}'")
        if not content.strip():
            print("Content is empty")
            return {'error': 'parse'}
        # Strip markdown code blocks
        if content.strip().startswith('```json'):
            content = content.strip()[7:]  # Remove ```json
            if content.endswith('```'):
                content = content[:-3]  # Remove ```
            content = content.strip()
        elif content.strip().startswith('```'):
            content = content.strip()[3:]  # Remove ```
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
        print(f"Cleaned content: '{content}'")
        try:
            parsed = json.loads(content)
            parsed['raw_answer_text'] = content
            return parsed
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
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
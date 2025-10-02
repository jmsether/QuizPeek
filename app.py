from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, QThread, Signal
import sys
import time
import logging
from ui_main import MainWindow
from config import load_config
from hotkey import register, unregister
from capture import detect_monitor_under_mouse, capture_monitor, crop_percent, downscale_max_width, encode_png_base64
from router import call_openrouter, validate_result
from overlay import show_notification

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
print("Logging configured")

class Worker(QThread):
    finished = Signal(dict, float)
    error = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        print("Worker thread started")
        logging.info("Worker thread started")
        start_time = time.time()
        try:
            print("Detecting monitor")
            mon = detect_monitor_under_mouse()
            print("Capturing monitor")
            img = capture_monitor(mon)
            print("Cropping image")
            img = crop_percent(img, self.config['top_crop_pct'], self.config['bottom_crop_pct'])
            print("Downscaling image")
            img = downscale_max_width(img, self.config['max_width'])
            print("Encoding image")
            data_url = encode_png_base64(img)
            print("Calling OpenRouter API")
            result = call_openrouter(data_url, self.config['model'], self.config['api_key'], 2.0)
            print("API call completed")
            if result is None or (isinstance(result, dict) and 'error' in result):
                if isinstance(result, dict):
                    if result['error'] == 'auth':
                        print("API auth error")
                        logging.error("API authentication error")
                        self.error.emit('auth')
                        return
                    elif result['error'] in ['server', 'timeout', 'network']:
                        print("No response from API")
                        logging.error("No response from API")
                        self.error.emit('no_response')
                        return
                    elif result['error'] == 'parse':
                        print("Parse error")
                        logging.error("Parse error in API response")
                        self.error.emit('parse_error')
                        return
                else:
                    print("No response")
                    logging.error("No response from API")
                    self.error.emit('no_response')
                    return
            print("Validating result")
            valid, msg = validate_result(result)
            if not valid:
                print("Validation failed")
                logging.error("Validation failed for API result")
                self.error.emit('parse_error')
                return
            inference_time = (time.time() - start_time) * 1000
            print(f"Worker completed in {inference_time:.0f} ms")
            logging.info(f"Worker completed successfully in {inference_time:.0f} ms")
            self.finished.emit(result, inference_time)
        except Exception as e:
            print(f"Exception in worker: {e}")
            logging.error(f"Exception in worker thread: {e}")
            self.error.emit('error')

def hotkey_callback(window):
    print("Hotkey callback entered")
    print("Hotkey triggered, starting worker thread")
    logging.info("Hotkey triggered, starting worker thread")
    if hasattr(window, 'current_worker') and window.current_worker and window.current_worker.isRunning():
        print("Previous worker still running, skipping new worker")
        logging.warning("Previous worker still running, skipping new worker")
        print("Hotkey callback exited early")
        return
    try:
        worker = Worker(window.config)
        window.current_worker = worker
        worker.finished.connect(window.answerReady)
        worker.error.connect(lambda msg: on_error(window, msg))
        worker.start()
        print("Worker thread started")
        logging.debug("Worker thread started")
    except Exception as e:
        print(f"Exception in hotkey_callback: {e}")
        logging.error(f"Exception in hotkey_callback: {e}")
        window.current_worker = None
    print("Hotkey callback exited")

def on_finished(window, result, inference_time):
    logging.info("Worker finished successfully")
    print("on_finished called")
    window.current_worker = None
    logging.info("Worker completed, app continues running")
    confidence = result['confidence']
    threshold = window.config['confidence_threshold']
    bypass = window.config.get('bypass_confidence', False)
    print(f"Confidence: {confidence}, Threshold: {threshold}, Bypass: {bypass}")
    if bypass or confidence >= threshold:
        print("Showing dialog")
        # Show answer dialog
        dialog = QDialog(window)
        dialog.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        dialog.setWindowTitle("Quiz Answer")
        layout = QVBoxLayout(dialog)
        if result['mode'] == 'mcq':
            if 'answer_indices' in result and result['answer_indices']:
                answers = ', '.join(chr(65 + i) for i in sorted(result['answer_indices']))
                answer_text = f"Answer: {answers}"
            elif 'answer_index' in result:
                answer_text = f"Answer: {chr(65 + result['answer_index'])}"
            else:
                answer_text = "Answer: Unknown"
        elif result['mode'] == 'journal':
            if 'answer_entries' in result and result['answer_entries']:
                answer_text = "Journal Entries:\n" + "\n".join(result['answer_entries'])
            else:
                answer_text = "Answer: No journal entries found"
        elif result['mode'] == 'tf':
            if 'answer_index' in result:
                answer = 'T' if result['answer_index'] == 0 else 'F'
                answer_text = f"Answer: {answer}"
            else:
                answer_text = "Answer: Unknown"
        else:  # fitb
            answer_text = f"Answer: {result.get('answer_text', result['raw_answer_text'])}"
        layout.addWidget(QLabel(answer_text))
        layout.addWidget(QLabel(f"Confidence: {confidence:.2f}"))
        layout.addWidget(QLabel(f"Inference time: {inference_time:.0f} ms"))
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        dialog.show()
        dialog.raise_()
        QApplication.processEvents()
        print("Dialog shown")
    else:
        print("Not showing dialog")
    window.status_bar.showMessage(f'Inference: {inference_time:.0f} ms, Confidence: {confidence:.2f}')

def on_error(window, msg):
    logging.error(f"Worker error: {msg}")
    window.current_worker = None
    logging.info("Error handled, app continues running")
    if msg == 'auth':
        QMessageBox.warning(window, 'Invalid API Key', 'Invalid OpenRouter API key')
        return
    elif msg == 'no_response':
        color = "amber"
        text = "No response"
    elif msg == 'parse_error':
        color = "red"
        text = "Parse error"
    else:
        color = "red"
        text = "Error"
    screen = QApplication.primaryScreen()
    geometry = screen.geometry()
    show_notification(text, color)
    window.status_bar.showMessage('Error')

if __name__ == '__main__':
    logging.info("Starting QuizPeek application")
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        logging.info("QApplication created successfully")
    except Exception as e:
        logging.error(f"Failed to create QApplication: {e}")
        sys.exit(1)
    window = MainWindow()
    window.hotkeyStartRequested.connect(lambda combo: register(combo, lambda: hotkey_callback(window)))
    window.hotkeyStopRequested.connect(lambda: unregister(window.hotkey_input.text()))
    window.hide()
    sys.exit(app.exec())
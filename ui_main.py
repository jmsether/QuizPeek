from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QLabel, QStatusBar, QHBoxLayout, QVBoxLayout, QWidget, QDialog, QApplication
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCloseEvent, QPixmap, QImage
from PIL import Image
from PIL.ImageQt import ImageQt
from config import load_config, save_config
from hotkey import HotkeyInput
from overlay import show_notification
from capture import detect_monitor_under_mouse, capture_monitor, crop_percent, downscale_max_width

class MainWindow(QMainWindow):
    hotkeyStartRequested = Signal(str)
    hotkeyStopRequested = Signal()
    answerReady = Signal(dict, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('QuizPeek')
        self.config = load_config()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # API Key
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel('API Key:'))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(self.config.get('api_key', ''))
        self.api_key_edit.textChanged.connect(self.save_config)
        api_layout.addWidget(self.api_key_edit)
        self.save_key_checkbox = QCheckBox('Save key')
        self.save_key_checkbox.setChecked(self.config.get('save_key', False))
        self.save_key_checkbox.stateChanged.connect(self.save_config)
        api_layout.addWidget(self.save_key_checkbox)
        layout.addLayout(api_layout)

        # Model
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('Model:'))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItem('meta-llama/llama-3.2-90b-vision-instruct')
        self.model_combo.setCurrentText(self.config.get('model', 'meta-llama/llama-3.2-90b-vision-instruct'))
        self.model_combo.currentTextChanged.connect(self.save_config)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Hotkey
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel('Hotkey:'))
        self.hotkey_input = HotkeyInput()
        self.hotkey_input.setText(self.config.get('hotkey', 'ctrl'))
        self.hotkey_input.comboChanged.connect(self.save_config)
        hotkey_layout.addWidget(self.hotkey_input)
        layout.addLayout(hotkey_layout)

        # Top Crop %
        top_crop_layout = QHBoxLayout()
        top_crop_layout.addWidget(QLabel('Top Crop %:'))
        self.top_crop_spin = QSpinBox()
        self.top_crop_spin.setRange(0, 50)
        self.top_crop_spin.setValue(self.config.get('top_crop_pct', 8))
        self.top_crop_spin.valueChanged.connect(self.save_config)
        top_crop_layout.addWidget(self.top_crop_spin)
        layout.addLayout(top_crop_layout)

        # Bottom Crop %
        bottom_crop_layout = QHBoxLayout()
        bottom_crop_layout.addWidget(QLabel('Bottom Crop %:'))
        self.bottom_crop_spin = QSpinBox()
        self.bottom_crop_spin.setRange(0, 50)
        self.bottom_crop_spin.setValue(self.config.get('bottom_crop_pct', 6))
        self.bottom_crop_spin.valueChanged.connect(self.save_config)
        bottom_crop_layout.addWidget(self.bottom_crop_spin)
        layout.addLayout(bottom_crop_layout)

        # Max Width
        max_width_layout = QHBoxLayout()
        max_width_layout.addWidget(QLabel('Max Width:'))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(512, 2048)
        self.max_width_spin.setValue(self.config.get('max_width', 1024))
        self.max_width_spin.valueChanged.connect(self.save_config)
        max_width_layout.addWidget(self.max_width_spin)
        layout.addLayout(max_width_layout)

        # Bypass Confidence
        bypass_layout = QHBoxLayout()
        bypass_layout.addWidget(QLabel('Bypass Confidence:'))
        self.bypass_checkbox = QCheckBox()
        self.bypass_checkbox.setChecked(self.config.get('bypass_confidence', False))
        self.bypass_checkbox.stateChanged.connect(self.save_config)
        bypass_layout.addWidget(self.bypass_checkbox)
        layout.addLayout(bypass_layout)

        # Show Notifications
        notifications_layout = QHBoxLayout()
        notifications_layout.addWidget(QLabel('Show Notifications:'))
        self.notifications_checkbox = QCheckBox()
        self.notifications_checkbox.setChecked(self.config.get('show_notifications', False))
        self.notifications_checkbox.stateChanged.connect(self.save_config)
        notifications_layout.addWidget(self.notifications_checkbox)
        layout.addLayout(notifications_layout)

        # Show Raw Answer
        show_raw_layout = QHBoxLayout()
        show_raw_layout.addWidget(QLabel('Show Raw Answer:'))
        self.show_raw_checkbox = QCheckBox()
        self.show_raw_checkbox.setChecked(self.config.get('show_raw_answer', False))
        self.show_raw_checkbox.stateChanged.connect(self.save_config)
        show_raw_layout.addWidget(self.show_raw_checkbox)
        layout.addLayout(show_raw_layout)

        # Show Confidence Rating
        show_confidence_layout = QHBoxLayout()
        show_confidence_layout.addWidget(QLabel('Show Confidence Rating:'))
        self.show_confidence_checkbox = QCheckBox()
        self.show_confidence_checkbox.setChecked(self.config.get('show_confidence_rating', False))
        self.show_confidence_checkbox.stateChanged.connect(self.save_config)
        show_confidence_layout.addWidget(self.show_confidence_checkbox)
        layout.addLayout(show_confidence_layout)

        # Test Dialog Button
        self.test_button = QPushButton('Test Dialog')
        self.test_button.clicked.connect(self.show_test_dialog)

        # Test Pill Button
        self.test_pill_button = QPushButton('Test Pill')
        self.test_pill_button.clicked.connect(self.show_test_pill)

        # Horizontal layout for test buttons
        test_buttons_layout = QHBoxLayout()
        test_buttons_layout.addWidget(self.test_button)
        test_buttons_layout.addWidget(self.test_pill_button)
        layout.addLayout(test_buttons_layout)

        # Test Screenshot Button
        self.test_screenshot_button = QPushButton('Test Screenshot')
        self.test_screenshot_button.clicked.connect(self.show_test_screenshot)
        layout.addWidget(self.test_screenshot_button)

        # Start/Stop Button
        self.start_stop_button = QPushButton('Start')
        self.start_stop_button.clicked.connect(self.toggle_hotkey)
        layout.addWidget(self.start_stop_button)

        # Status Bar
        self.status_bar = self.statusBar()
        self.inference_label = QLabel('Last inference: 0 ms')
        self.status_bar.addWidget(self.inference_label)
        self.confidence_label = QLabel('Confidence: 0.00')
        self.status_bar.addWidget(self.confidence_label)

        # Connect answer ready signal
        self.answerReady.connect(self.show_answer_dialog)

    def toggle_hotkey(self):
        if self.start_stop_button.text() == 'Start':
            combo = self.hotkey_input.text()
            self.hotkeyStartRequested.emit(combo)
            self.start_stop_button.setText('Stop')
        else:
            self.hotkeyStopRequested.emit()
            self.start_stop_button.setText('Start')

    def show_test_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Test")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Test"))
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_test_pill(self):
        text = "Test Pill"
        color = "green"
        show_notification(text, color)

    def show_test_screenshot(self):
        monitor = detect_monitor_under_mouse()
        img = capture_monitor(monitor)
        top_pct = self.config.get('top_crop_pct', 8)
        bot_pct = self.config.get('bottom_crop_pct', 6)
        img = crop_percent(img, top_pct, bot_pct)
        max_w = self.config.get('max_width', 1024)
        img = downscale_max_width(img, max_w)
        # Convert to QPixmap
        img_qt = ImageQt(img)
        pixmap = QPixmap.fromImage(img_qt)
        dialog = QDialog(self)
        dialog.setWindowTitle("Test Screenshot")
        layout = QVBoxLayout(dialog)
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_answer_dialog(self, result, inference_time):
        print("show_answer_dialog called")
        confidence = result['confidence']
        threshold = self.config['confidence_threshold']
        bypass = self.config.get('bypass_confidence', False)
        show_notifications = self.config.get('show_notifications', False)
        show_confidence = self.config.get('show_confidence_rating', False)
        print(f"Confidence: {confidence}, Threshold: {threshold}, Bypass: {bypass}, Show Notifications: {show_notifications}")
        if bypass or confidence >= threshold:
            if result['mode'] == 'mcq':
                if 'answer_indices' in result and result['answer_indices']:
                    answers = ', '.join(chr(65 + i) for i in sorted(result['answer_indices']))
                    base_text = answers
                elif 'answer_index' in result:
                    base_text = chr(65 + result['answer_index'])
                else:
                    base_text = "Unknown"
            elif result['mode'] == 'journal':
                if 'answer_entries' in result and result['answer_entries']:
                    first_entry = result['answer_entries'][0][:15]
                    remaining_count = len(result['answer_entries']) - 1
                    if remaining_count > 0:
                        base_text = f"{first_entry}(+{remaining_count})"
                    else:
                        base_text = first_entry
                else:
                    base_text = "No entries"
            elif result['mode'] == 'tf':
                if 'answer_index' in result:
                    answer = 'T' if result['answer_index'] == 0 else 'F'
                    base_text = answer
                else:
                    base_text = "Unknown"
            else:
                base_text = result.get('answer_text', result['raw_answer_text'][:20])
            if show_confidence:
                text = f"{base_text}\n{confidence:.2f}"
            else:
                text = base_text
            color = "green" if confidence >= threshold else "amber"
            if show_notifications:
                print("Showing notification")
                show_notification(text, color)
            else:
                print("Showing dialog")
                dialog = QDialog(self)
                dialog.setWindowTitle("Answer")
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel(text))
                close_button = QPushButton("Close")
                close_button.clicked.connect(dialog.close)
                layout.addWidget(close_button)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
        else:
            print("Not showing answer")
        self.status_bar.showMessage(f'Inference: {inference_time:.0f} ms, Confidence: {confidence:.2f}')

    def save_config(self):
        self.config['model'] = self.model_combo.currentText()
        self.config['hotkey'] = self.hotkey_input.text()
        self.config['top_crop_pct'] = self.top_crop_spin.value()
        self.config['bottom_crop_pct'] = self.bottom_crop_spin.value()
        self.config['max_width'] = self.max_width_spin.value()
        self.config['save_key'] = self.save_key_checkbox.isChecked()
        self.config['bypass_confidence'] = self.bypass_checkbox.isChecked()
        self.config['show_notifications'] = self.notifications_checkbox.isChecked()
        self.config['show_raw_answer'] = self.show_raw_checkbox.isChecked()
        self.config['show_confidence_rating'] = self.show_confidence_checkbox.isChecked()
        if self.save_key_checkbox.isChecked():
            self.config['api_key'] = self.api_key_edit.text()
        else:
            self.config['api_key'] = ''
        save_config(self.config)

    def update_inference_time(self, ms):
        self.inference_label.setText(f'Last inference: {ms} ms')

    def update_confidence(self, conf):
        self.confidence_label.setText(f'Confidence: {conf:.2f}')

    def closeEvent(self, event: QCloseEvent):
        # Wait for any running workers
        if hasattr(self, 'current_worker') and self.current_worker.isRunning():
            self.current_worker.wait()
        save_config(self.config)
        super().closeEvent(event)
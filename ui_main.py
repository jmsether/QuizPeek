from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QLabel, QStatusBar, QHBoxLayout, QVBoxLayout, QWidget, QDialog, QApplication
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCloseEvent
from config import load_config, save_config
from hotkey import HotkeyInput
from overlay import show_pill

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

        # Use Overlay Pill
        pill_layout = QHBoxLayout()
        pill_layout.addWidget(QLabel('Use Overlay Pill:'))
        self.pill_checkbox = QCheckBox()
        self.pill_checkbox.setChecked(self.config.get('use_overlay_pill', False))
        self.pill_checkbox.stateChanged.connect(self.save_config)
        pill_layout.addWidget(self.pill_checkbox)
        layout.addLayout(pill_layout)

        # Test Dialog Button
        self.test_button = QPushButton('Test Dialog')
        self.test_button.clicked.connect(self.show_test_dialog)
        layout.addWidget(self.test_button)

        # Test Pill Button
        self.test_pill_button = QPushButton('Test Pill')
        self.test_pill_button.clicked.connect(self.show_test_pill)
        layout.addWidget(self.test_pill_button)

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
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()
        show_pill(text, color, geometry)

    def show_answer_dialog(self, result, inference_time):
        print("show_answer_dialog called")
        confidence = result['confidence']
        threshold = self.config['confidence_threshold']
        bypass = self.config.get('bypass_confidence', False)
        use_pill = self.config.get('use_overlay_pill', False)
        print(f"Confidence: {confidence}, Threshold: {threshold}, Bypass: {bypass}, Use Pill: {use_pill}")
        if bypass or confidence >= threshold:
            if use_pill:
                print("Showing pill")
                if result['mode'] == 'mcq':
                    if 'answer_indices' in result and result['answer_indices']:
                        answers = ', '.join(chr(65 + i) for i in sorted(result['answer_indices']))
                        text = f"{answers} {confidence:.2f}"
                    elif 'answer_index' in result:
                        text = f"{chr(65 + result['answer_index'])} {confidence:.2f}"
                    else:
                        text = f"Unknown {confidence:.2f}"
                elif result['mode'] == 'journal':
                    if 'answer_entries' in result and result['answer_entries']:
                        first_entry = result['answer_entries'][0][:15]
                        remaining_count = len(result['answer_entries']) - 1
                        if remaining_count > 0:
                            text = f"{first_entry}(+{remaining_count}) {confidence:.2f}"
                        else:
                            text = f"{first_entry} {confidence:.2f}"
                    else:
                        text = f"No entries {confidence:.2f}"
                elif result['mode'] == 'tf':
                    if 'answer_index' in result:
                        answer = 'T' if result['answer_index'] == 0 else 'F'
                        text = f"{answer} {confidence:.2f}"
                    else:
                        text = f"Unknown {confidence:.2f}"
                else:
                    text = f"{result['answer_text'][:20]} {confidence:.2f}"
                color = "green" if confidence >= threshold else "amber"
                screen = QApplication.primaryScreen()
                geometry = screen.geometry()
                show_pill(text, color, geometry)
            else:
                print("Showing answer dialog")
                dialog = QDialog(self)
                dialog.setWindowTitle("Quiz Answer")
                dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
                dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
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
                else:
                    answer_text = f"Answer: {result['answer_text']}"
                layout.addWidget(QLabel(answer_text))
                layout.addWidget(QLabel(f"Confidence: {confidence:.2f}"))
                layout.addWidget(QLabel(f"Inference time: {inference_time:.0f} ms"))
                close_button = QPushButton("Close")
                close_button.clicked.connect(dialog.close)
                layout.addWidget(close_button)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
                QApplication.processEvents()
                print("Answer dialog shown")
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
        self.config['use_overlay_pill'] = self.pill_checkbox.isChecked()
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
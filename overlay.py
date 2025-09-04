from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import QTimer, Qt, QRect
from PySide6.QtGui import QColor


class PillOverlay(QWidget):
    def __init__(self, text: str, color: str, screen_geometry: QRect):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFixedSize(200, 50)

        # Set background color based on color parameter
        if color == "green":
            bg_color = "rgba(0, 128, 0, 0.8)"
        elif color == "amber":
            bg_color = "rgba(255, 193, 7, 0.8)"
        elif color == "red":
            bg_color = "rgba(220, 53, 69, 0.8)"
        else:
            bg_color = "rgba(0, 0, 0, 0.8)"  # default semi-transparent black

        self.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 18px;
        """)

        # Create label for text
        label = QLabel(text, self)
        label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setGeometry(0, 0, 200, 50)

        # Position the window in center
        x = (screen_geometry.width() - 200) // 2
        y = (screen_geometry.height() - 50) // 2
        self.move(x, y)

        # Auto-hide after 2.5 seconds
        QTimer.singleShot(2500, self.close)


def show_pill(text: str, color: str, screen_geometry: QRect) -> None:
    print(f"Showing pill: {text}, color: {color}, geometry: {screen_geometry}")
    pill = PillOverlay(text, color, screen_geometry)
    pill.show()
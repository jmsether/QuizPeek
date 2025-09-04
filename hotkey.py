import platform
import keyboard
import logging
from pynput import keyboard as pynput_keyboard
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt

# Detect platform
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

# Global storage for registered hotkeys
_registered_hotkeys = {}

def _normalize_combo(combo: str) -> str:
    """Normalize combo string to canonical format."""
    parts = combo.replace(' ', '').split('+')
    # Sort modifiers, keep order for keys
    modifiers = []
    keys = []
    for part in parts:
        if part.lower() in ['ctrl', 'control', 'alt', 'shift', 'cmd', 'command', 'super', 'win']:
            modifiers.append(part.lower())
        else:
            keys.append(part.lower())
    modifiers.sort()
    return '+'.join(modifiers + keys)

def register(combo: str, callback: callable) -> bool:
    """Register a hotkey combo with callback. Returns True on success."""
    combo = _normalize_combo(combo)
    logging.info(f"Attempting to register hotkey: {combo}")
    try:
        if IS_WINDOWS:
            # Use keyboard library on Windows
            keyboard.add_hotkey(combo, callback)
            logging.info(f"Hotkey {combo} registered successfully on Windows")
        else:
            # Use pynput on macOS/Linux
            with pynput_keyboard.Listener(on_press=lambda key: _pynput_callback(key, combo, callback)) as listener:
                listener.join()
        _registered_hotkeys[combo] = callback
        return True
    except Exception as e:
        logging.error(f"Failed to register hotkey {combo}: {e}")
        return False

def unregister(combo: str) -> None:
    """Unregister a hotkey combo."""
    combo = _normalize_combo(combo)
    if combo in _registered_hotkeys:
        try:
            if IS_WINDOWS:
                keyboard.remove_hotkey(combo)
            else:
                # pynput doesn't have direct unregister, but we can stop listener
                pass  # For simplicity, assume listener is managed externally
            del _registered_hotkeys[combo]
        except Exception as e:
            print(f"Failed to unregister hotkey {combo}: {e}")

def _pynput_callback(key, combo: str, callback: callable):
    """Internal callback for pynput."""
    # This is a simplified version; actual implementation would need to track combo state
    # For full implementation, would need to track pressed keys
    pass

class HotkeyInput(QLineEdit):
    """PySide6 widget for capturing hotkey combos."""

    comboChanged = Signal(str)  # Emitted when combo changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText('Ctrl')  # Default combo
        self._pressed_keys = set()
        self.setFocusPolicy(Qt.StrongFocus)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._pressed_keys.clear()
        self.setText('')  # Clear on focus

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.text():
            self.setText('Ctrl')  # Reset to default if empty

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        # Build combo string
        combo_parts = []
        if modifiers & Qt.ControlModifier:
            combo_parts.append('Ctrl')
        if modifiers & Qt.AltModifier:
            combo_parts.append('Alt')
        if modifiers & Qt.ShiftModifier:
            combo_parts.append('Shift')
        if IS_MACOS and modifiers & Qt.MetaModifier:
            combo_parts.append('Cmd')

        # Add the key
        if key == Qt.Key_Space:
            combo_parts.append('Space')
        elif key >= Qt.Key_A and key <= Qt.Key_Z:
            combo_parts.append(chr(key).upper())
        elif key >= Qt.Key_0 and key <= Qt.Key_9:
            combo_parts.append(chr(key))
        elif key == Qt.Key_F1:
            combo_parts.append('F1')
        # Add more function keys as needed
        else:
            # Ignore other keys
            return

        combo = '+'.join(combo_parts)
        self.setText(combo)
        self.comboChanged.emit(combo)
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent):
        # Clear pressed keys on release
        self._pressed_keys.clear()
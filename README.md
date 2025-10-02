# QuizPeek

QuizPeek is a desktop application that uses AI to help users answer quiz questions by capturing screenshots and providing instant answers via an overlay.

## Features

- **Screenshot Capture**: Automatically captures quiz questions from your screen
- **AI-Powered Answers**: Integrates with OpenRouter API for intelligent question answering
- **Customizable Hotkeys**: Configure global hotkeys for quick activation
- **Overlay Display**: Shows answers in a non-intrusive overlay window
- **Flexible Configuration**: Adjust crop percentages, max width, and other settings
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jmsether/quizpeek.git
   cd quizpeek
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Enter your OpenRouter API key in the UI
3. Select your preferred AI model
4. Configure the hotkey (default: Ctrl)
5. Adjust crop percentages and max width as needed
6. Click "Start" to enable the hotkey
7. Press the hotkey while viewing a quiz question to get an instant answer in the overlay

## Configuration

- **API Key**: Securely enter and save your OpenRouter API key
- **Model Selection**: Choose from available AI models via dropdown
- **Hotkey**: Customize the global hotkey for screenshot capture
- **Crop Settings**: Adjust top/bottom crop percentages to focus on question area
- **Max Width**: Set maximum width for the overlay display

## Screenshots

![QuizPeek Application Interface](Screenshots/Program%20screenshot%201.png)

## Dependencies

This project relies on the following Python packages:

- PySide6: GUI framework
- mss: Screenshot capture
- Pillow: Image processing
- requests: HTTP requests for API calls
- keyboard: Hotkey detection
- pynput: Input monitoring
- pyautogui: GUI automation

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Known Limitations

- Some operating systems require administrator/root privileges for global hotkeys
- macOS requires Accessibility permissions for keyboard monitoring
- Ensure your display settings allow for proper screenshot capture
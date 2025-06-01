# Oneko - Desktop Cat Companion

A cute desktop cat that chases your mouse cursor around the screen, inspired by the classic Neko program.

![Oneko Demo](demo.gif) <!-- To be added -->

## Features

- 🐱 Animated cat that follows your cursor
- 😴 Idle animations (sitting, washing, sleeping)
- 🕳️ Digging animation when cursor goes off-screen
- 🎯 System tray integration
- 🚀 Auto-start with system option
- 🖥️ Multi-monitor support
- 🍎 Native macOS app bundle

## Installation

### Option 1: Download from Releases (Recommended)
1. Go to [Releases](https://github.com/Sky-creates/Oneko/releases)
2. Download the latest `Oneko-Installer.dmg`
3. Open the DMG file
4. Drag Oneko.app to Applications folder
5. Launch from Applications or Spotlight

### Option 2: Build from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/oneko.git
cd oneko

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install PyQt6 pillow pyinstaller

# Run directly
python oneko.py

# Or build app bundle
pyinstaller oneko.spec
```

## Usage

1. Launch Oneko
2. The cat will appear and start following your cursor
3. Right-click the system tray icon for options:
   - Hide/Show cat
   - Enable auto-start
   - Quit application

## Cat Behaviors

- **Chasing**: Follows your cursor when it moves
- **Sitting**: Rests when cursor is nearby
- **Washing**: Occasional grooming animation
- **Sleeping**: Falls asleep after being idle
- **Digging**: Tries to find you when cursor goes off-screen
- **Surprised**: Reacts when you move cursor after being idle

## Requirements

- macOS 10.14+ (for app bundle)
- Python 3.8+ (for source)
- PyQt6

## Building

### Create App Bundle
```bash
pyinstaller oneko.spec
```

### Create DMG Installer
```bash
# Install create-dmg
brew install create-dmg

# Create installer
create-dmg \
  --volname "Oneko Installer" \
  --volicon "oneko.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Oneko.app" 175 120 \
  --hide-extension "Oneko.app" \
  --app-drop-link 425 120 \
  "Oneko-Installer.dmg" \
  "dist/"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original Neko program for X11
- Cat sprites adapted from [here](https://github.com/jeebuscrossaint/oneko.git)
- Built with PyQt6

## Troubleshooting

### Cat doesn't appear
- Check if system tray icon is visible
- Try running from terminal to see error messages
- Grant accessibility permissions in System Preferences

### Performance issues
- Close other resource-intensive applications
- Check Activity Monitor for CPU usage

### System tray icon missing
- Enable "Show system tray" in your desktop environment
- Try restarting the application

## Changelog

### v1.0.0
- Initial release
- Basic cursor following
- System tray integration
```

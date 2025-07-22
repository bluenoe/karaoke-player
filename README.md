# Karaoke Rich 🎤🎵

A comprehensive terminal-based karaoke application built with Python and Rich library, featuring synchronized lyrics display, audio playback, themes, and modern UI.

## Features ✨

### Core Features
- 🎵 **Real-time lyrics synchronization** - Words highlight as they should be sung
- 🔊 **Audio playback support** - Play audio files alongside lyrics (MP3, WAV, OGG, M4A)
- 🌈 **Beautiful terminal UI** - Colorful and modern interface using Rich
- ⏱️ **Precise timing** - Millisecond-accurate word synchronization
- 📊 **Progress tracking** - Visual progress bar and time information
- 🎤 **Multiple songs support** - Easy to add new songs via JSON files

### Advanced Features
- 🎨 **Multiple themes** - Switch between different color schemes
- ⚙️ **Configurable settings** - Customize display, audio, and playback options
- 🎛️ **Audio controls** - Volume control, pause/resume, seek functionality
- 📱 **Interactive menus** - Easy navigation through songs and settings
- 💾 **Persistent configuration** - Settings saved between sessions
- 🔄 **Real-time theme switching** - Change themes without restarting

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install rich
```

### Download Project

```bash
git clone <repository-url>
cd karaoke
```

Or download and extract the project files to a directory.

## 🚀 Quick Start

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Select a song** from the available list

3. **Press Enter** to start karaoke

4. **Follow the lyrics** as they highlight in real-time

5. **Press Ctrl+C** to stop playback

## 📁 Project Structure

```
karaoke/
├── main.py                # Entry point and application management
├── karaoke_player.py      # Core playback engine and session management
├── layout_builder.py      # Rich UI components and rendering
├── lyrics_data.py         # Data models and JSON lyrics loader
├── utils.py               # Helper functions and utilities
├── lyrics/                # Directory for song lyrics
│   └── anh_vui.json      # Example song file
├── README.md              # This file
└── ai_meta.yaml          # AI development metadata
```

## 🎵 Adding New Songs

### JSON Format

Create a new JSON file in the `lyrics/` directory with this structure:

```json
{
  "title": "Song Title",
  "artist": "Artist Name",
  "sentences": {
    "sentence1": [
      { "time": 0, "text": "First" },
      { "time": 500, "text": "word" },
      { "time": 1000, "text": "timing" }
    ],
    "sentence2": [
      { "time": 2000, "text": "Second" },
      { "time": 2500, "text": "sentence" }
    ]
  }
}
```

### Timing Guidelines

- **Time values** are in milliseconds
- **Start from 0** for the first word
- **Increment timing** based on when each word should be sung
- **Group words** into logical sentences
- **Test timing** by running the karaoke to ensure synchronization

## 🎮 Controls

| Key | Action |
|-----|--------|
| `Enter` | Start karaoke |
| `Ctrl+C` | Stop playback |
| `1-9` | Select song from menu |
| `q` | Quit application |

## 🏗️ Architecture

### Core Components

- **`main.py`** - Application entry point, handles startup and song selection
- **`karaoke_player.py`** - Core playback logic and timing management
- **`layout_builder.py`** - Rich UI components and visual rendering
- **`lyrics_data.py`** - Data models and JSON file loading
- **`utils.py`** - Helper functions for time formatting and navigation

### Data Models

```python
@dataclass
class Word:
    time: int  # Milliseconds
    text: str  # Word content

@dataclass
class Sentence:
    words: List[Word]

@dataclass
class Song:
    title: str
    artist: str
    sentences: Dict[str, Sentence]
```

## 🔧 Development

### Code Style

- **Type hints** for all functions
- **Comprehensive docstrings** following Google style
- **Dataclass models** for structured data
- **External configuration** via JSON files
- **Error handling** with user-friendly messages

### Adding Features

The modular architecture makes it easy to extend:

1. **New UI components** → Add to `layout_builder.py`
2. **Playback features** → Extend `karaoke_player.py`
3. **Data formats** → Modify `lyrics_data.py`
4. **Utility functions** → Add to `utils.py`

## 🚀 Future Features

- 🎵 **Audio playback** with pygame.mixer
- 📱 **Web interface** for remote control
- 🎨 **Custom themes** and color schemes
- 📤 **Export to LRC** subtitle format
- ⏯️ **Pause/resume/seek** functionality
- 🎼 **Playlist support** for multiple songs
- 🎚️ **Volume control** and audio effects
- 📝 **Real-time lyrics editing**

## 🐛 Troubleshooting

### Common Issues

**"Rich library not found"**
```bash
pip install rich
```

**"No songs found"**
- Ensure JSON files are in the `lyrics/` directory
- Check JSON format is valid
- Verify file permissions

**"Timing is off"**
- Adjust time values in the JSON file
- Test with different timing increments
- Consider adding buffer time between words

### Debug Mode

For development, you can add debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Follow the existing code style
5. Submit a pull request

## 📞 Support

For questions, issues, or feature requests:

- Create an issue in the repository
- Check the troubleshooting section
- Review the code documentation

---

**Made with ❤️ and Python**

*Enjoy your karaoke experience! 🎤🎵*
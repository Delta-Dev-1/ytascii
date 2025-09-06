# ytascii

Real-time YouTube video to ASCII converter with synchronized audio playback.

![Demo](demo.gif)

## Technical Overview

Downloads YouTube streams via yt-dlp, processes video frames through FFmpeg, converts RGB data to ASCII using brightness mapping, and displays synchronized output with separate audio playback. Includes automatic subtitle parsing and real-time user controls.

![Fastfetch Demo](fastfetch-demo.gif)

## Implementation Details

**Video Pipeline:**
- FFmpeg extracts frames at configurable FPS (default 10fps)
- PIL converts RGB24 raw frames to ASCII using luminance-based character mapping
- ANSI color codes preserve original RGB values per character
- Separate FFplay process handles audio synchronization

**Control System:**
- Non-blocking keyboard input via termios/tty manipulation
- Threaded control handler for real-time pause/skip functionality
- Global state management for playback coordination

**Subtitle Processing:**
- Automatic extraction of JSON3 subtitle format
- Time-synchronized caption display with configurable offset
- Toggle support for caption visibility

## Features

- Real-time ASCII video streaming with color preservation
- Synchronized audio playback (FFplay backend)
- Live subtitle integration from YouTube's auto-generated captions
- Interactive playback controls (pause, skip forward/backward, quit)
- Fastfetch system info overlay mode
- Configurable output dimensions and loop playback
- Progress bar with time display

## Installation

### Quick Install
```bash
curl -s https://raw.githubusercontent.com/Delta-Dev-1/ytascii/main/install.sh | bash
```

### Manual Setup
```bash
git clone https://github.com/Delta-Dev-1/ytascii.git
cd ytascii
chmod +x ytascii.py
sudo ln -s $PWD/ytascii.py /usr/local/bin/ytascii
```

## Dependencies

**Required System Tools:**
- `yt-dlp` - YouTube stream extraction
- `ffmpeg` - video frame processing
- `ffplay` - audio playback backend
- `python3` - runtime environment

**Python Dependencies:**
```bash
pip install Pillow colorama numpy
```

### Platform Installation

**Arch Linux:**
```bash
sudo pacman -S ffmpeg python-pip
pip install yt-dlp Pillow colorama numpy
```

**Debian/Ubuntu:**
```bash
sudo apt install ffmpeg python3-pip
pip3 install yt-dlp Pillow colorama numpy
```

**macOS:**
```bash
brew install ffmpeg
pip3 install yt-dlp Pillow colorama numpy
```

## Usage

```bash
ytascii [options] <YouTube_URL>
```

### Examples
```bash
# Basic playback
ytascii "https://youtu.be/dQw4w9WgXcQ"

# Custom dimensions with system info overlay
ytascii "https://youtu.be/NyanCat" --fastfetch-mode --width 100 --height 40

# Looped playback
ytascii "https://youtu.be/example" --loop
```

### Command Options
- `--fastfetch-mode` - Display system information alongside video
- `--loop` - Continuous playback mode
- `--width <int>` - Set ASCII output width
- `--height <int>` - Set ASCII output height

### Runtime Controls
- `p` - Toggle pause/resume
- `q` - Exit player
- `f` - Skip forward 5 seconds
- `b` - Skip backward 5 seconds
- `c` - Toggle caption display

## Technical Configuration

**ASCII Character Mapping:**
Uses brightness-based character selection: `@%#*+=-:. `
Characters mapped by luminance value: `brightness * (len(ASCII_CHARS) - 1) // 255`

**Color Rendering:**
RGB values converted to ANSI 24-bit color codes: `\033[38;2;{r};{g};{b}m`

**Performance:**
Frame processing scales with terminal dimensions. Default 10fps provides balance between visual quality and system load. CPU usage increases proportionally with output resolution.

## Platform Support

- Linux (native termios support)
- macOS (tested with Homebrew dependencies)
- Windows via WSL2 or Git Bash environment

## Architecture Notes

This implements a dual-process architecture: FFmpeg handles video frame extraction while FFplay manages audio synchronization. The Python process coordinates both streams and handles user interface.

The subtitle system parses YouTube's JSON3 caption format with configurable time offsets to account for processing delays. Real-time controls use terminal raw mode for immediate response without buffering.

## License

MIT License

## Attribution

Displays YouTube content under fair use provisions for educational demonstration. Original video content remains property of respective creators.

Nyan Cat video/audio © 2011 Chris Torres - used under fair use for demonstrative and educational purposes.
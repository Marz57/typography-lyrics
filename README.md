🎬 Typography Lyrics

<p align="center">
  <strong>Turn lyrics into a cinematic coding experience.</strong>
  <br>
  A Python-based lyric visualizer featuring animated code typography, cinematic camera movements, and atmospheric visual effects.
</p><p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Pygame-CE-green?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge" />
</p>---

✨ Overview

Typography Lyrics is a cinematic lyric visualization project that transforms ordinary song lyrics into animated programming-style text.

Instead of displaying conventional subtitles, lyrics are presented as lines of code with syntax highlighting, smooth typing animations, dynamic camera movements, and atmospheric cinematic effects.

Built with Python and Pygame, this project is designed to create a unique visual experience for music, typography, and creative video projects.

🚀 Features

- Code Typography – Automatically transforms ordinary lyrics into programming-style syntax.
- Syntax Highlighting – Different colors for keywords, functions, strings, objects, and numbers.
- Typewriter Animation – Lyrics appear character by character.
- Timestamp Synchronization – Supports LRC-style timestamps for synchronizing lyrics with music.
- Cinematic Camera – Dynamic zoom, pan, tilt, rotation, and smooth camera transitions.
- Glow Effects – Ambient lighting and glowing text.
- Bokeh Particles – Floating atmospheric particles.
- Light Streaks – Animated cinematic light effects.
- Reflection – Mirrored text reflections.
- Depth of Field – Blur and scaling effects for previous lyric lines.
- Chromatic Aberration – RGB color separation effects.
- Responsive Window – Resizable display with fullscreen support.
- Audio Playback – Plays background music directly through Pygame.
- Automatic Audio Conversion – Uses FFmpeg when the original audio format cannot be loaded.

🛠️ Requirements

- Python 3.x
- Pygame
- FFmpeg (optional, for audio conversion)

📦 Installation

Clone the repository:
```
git clone https://github.com/Marz57/typography-lyrics.git
```
Navigate into the project directory:
```
cd typography-lyrics
```
Install the required dependency:
```
pip install pygame
```
Alternatively, you can use Pygame Community Edition:
```
pip install pygame-ce
```
▶️ Usage

Run the application:
```
python3 cine.py
```
Make sure the following files are located in the same directory:

typography-lyrics/
├── cine.py
├── lirik.txt
├── lagu.mp3
└── README.md

The application will automatically load the lyrics and audio file.

🎵 Customizing Lyrics

Edit "lirik.txt" to use your own lyrics.

Without timestamps

Simply write each lyric line separately:

Koyo ngene
Yen nandhang loro asmoro
Jroning nala
Dahat rasaku
Sesandhing marang sliramu

With timestamps

You can synchronize lyrics with music using LRC-style timestamps:

[00:01] Koyo ngene
[00:03] Yen nandhang loro asmoro
[00:08] Jroning nala
[00:16] Dahat rasaku
[00:18] Sesandhing marang sliramu

Timestamp format:

[mm:ss.xx] Lyrics

When every lyric line has a valid timestamp, the application automatically switches to timestamp-based playback.

⚙️ Configuration

You can customize the visualizer directly inside "cine.py".

Variable| Description
"AUDIO_FILE"| Background music filename
"CODIFY"| Enable or disable automatic code conversion
"TYPE_SPEED"| Typing speed without timestamps
"LINE_PAUSE"| Delay between lyric lines
"LOOP"| Automatically restart playback
"WINDOW_SIZE"| Initial window resolution
"FPS"| Target frame rate
"CINEMATIC"| Enable or disable visual effects

Cinematic Effects

The "CINEMATIC" configuration allows individual effects to be enabled or disabled:

CINEMATIC = {
    "glow": True,
    "reflection": True,
    "bokeh": True,
    "streaks": True,
    "flowers": True,
    "dense_code": True,
    "aberration": True,
    "shake": True,
}

Set any effect to "False" to disable it.

⌨️ Keyboard Controls

Key| Action
"SPACE"| Pause / Resume
"R"| Restart playback
"F"| Toggle fullscreen
"ESC"| Exit application

🎨 Technology Stack

- Python – Core programming language.
- Pygame – Graphics rendering, animation, window management, and audio playback.
- FFmpeg – Optional audio format conversion.



📁 Project Structure

typography-lyrics/
│
├── cine.py          # Main cinematic lyric visualizer
├── lirik.txt        # Lyrics and timestamps
├── lagu.mp3         # Background audio
├── lagu_conv.ogg    # Converted audio (optional)
└── README.md        # Project documentation

👨‍💻 Author

Official Marz57

- GitHub: "@Marz57" (https://github.com/Marz57)
- TikTOk: @marz.57 (https://tiktok.com/@marz.57)

---

<p align="center">
  <strong>Made with Python, creativity, and a little bit of code.</strong>
  <br>
  © Official Marz57
</p>
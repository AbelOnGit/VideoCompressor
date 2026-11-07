# Video Compressor

Pick a video, pick a size, get a video that fits. Video Compressor is a Windows desktop app that squeezes a video down to a target file size (like 20 MB for Discord) using two-pass H.264 encoding.

No FFmpeg install needed. It's bundled right in the app.

## Features

- **Hit a target size.** Choose from 5, 8, 10, 15, 20, 25, 50, or 100 MB, or type in a custom size.
- **Drag and drop.** Drop a video on the window or click to browse. Supports MP4, MOV, MKV, AVI, WebM, FLV, WMV, M4V, and TS.
- **Two-pass encoding.** Pass one analyzes the video, pass two spends the bitrate where it matters, so you get better quality at the same size than a single pass.
- **Auto-retry.** If the result lands over your target, the app lowers the bitrate and tries again (up to 3 retries) instead of handing you a file that's too big.
- **Smart downscaling.** When the target is really tight, it drops the resolution (down to 240p) and frame rate so the video stays watchable instead of turning into a blocky mess. It never upscales.
- **Progress and cancel.** Live progress bar with time remaining, and a Cancel button that stops the job cleanly.
- **Never overwrites.** Outputs are saved as `<name> Compressed.mp4`, and a number gets added if that name is already taken.
- **Run logs.** Every run writes a `.log` next to the output showing what it did and why (resolution, frame rate, audio, each attempt, final size).
- **Already small enough?** If your video is already under the target, the app asks whether to just copy it or re-encode anyway.
- **Remembers your target size** between launches.

## Download

1. Go to the [Releases](../../releases) page.
2. Download `VideoCompressorSetup.exe` and run it.

The installer is per-user, so it doesn't need admin rights. It adds a Start Menu shortcut, and you can optionally add a desktop shortcut during setup.

> The installer isn't code-signed yet, so Windows SmartScreen may warn you. Click **More info**, then **Run anyway**.

## How to use

1. Open Video Compressor.
2. Drag in a video or click the drop area to choose one.
3. Pick a target size.
4. Click **Compress**.
5. When it's done, use **Open folder** or **Open file** to grab your video.

Compressed videos and their logs go in the `Outputs` folder inside the install directory. Anything in there is kept if you uninstall the app.

## How it works

1. **Probe.** `ffprobe` reads the duration, resolution, frame rate, and audio track.
2. **Budget.** The app works out the video bitrate that fits your target size, leaving about 4% headroom for container overhead and reserving 96 kbps for audio if there is any.
3. **Adjust for tight targets.** The lower the bitrate, the more it scales things down:

   | Video bitrate | What changes |
   | --- | --- |
   | under 1000 kbps | scale to 720p max |
   | under 500 kbps | scale to 480p max |
   | under 250 kbps | scale to 360p max |
   | under 120 kbps | scale to 240p max, frame rate capped at 15 fps |
   | under 50 kbps | audio drops to 32 kbps mono |

4. **Encode.** Two-pass H.264 (`libx264`, slow preset) with AAC audio, saved as an MP4 with `faststart` so it plays right away when shared online.
5. **Verify.** If the output is still over the target, it lowers the bitrate and re-encodes.

## Build from source

You'll need Windows, Python 3.11+, [Inno Setup 7](https://jrsoftware.org/isdl.php), and an internet connection.

```bat
cd Source
build.bat
```

The script will:

1. Install the Python dependencies from `requirements.txt`.
2. Download the Gyan.dev FFmpeg essentials build if `Source\bin` doesn't have the binaries yet.
3. Package everything into a single `VideoCompressor.exe` with PyInstaller.
4. Build `VideoCompressorSetup.exe` with Inno Setup.

Both files end up in the repository root.

To run it straight from source without building:

```bat
cd Source
pip install -r requirements.txt
python main.py
```

You'll need `ffmpeg.exe` and `ffprobe.exe` in `Source\bin` for that. Running `download_ffmpeg.ps1` will fetch them.

## Project layout

```
VideoCompressor/
├── Source/
│   ├── main.py               # entry point
│   ├── ui.py                 # CustomTkinter window, drag and drop
│   ├── compressor.py         # probing, bitrate math, two-pass encode, logs
│   ├── build.bat             # one-step build script
│   ├── download_ffmpeg.ps1   # fetches FFmpeg and ffprobe
│   ├── VideoCompressor.iss   # Inno Setup installer script
│   ├── requirements.txt
│   └── VideoCompressor.ico / .png / .svg
└── Outputs/                  # compressed videos and logs land here
```

## Built with

- [Python](https://www.python.org/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the UI
- [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) for drag and drop
- [FFmpeg](https://ffmpeg.org/) (Gyan.dev Windows essentials build) for encoding
- [PyInstaller](https://pyinstaller.org/) and [Inno Setup](https://jrsoftware.org/isinfo.php) for packaging

## Notes

- Windows only for now.
- Hitting a size target is a bitrate estimate, so the result usually lands a little under what you asked for, not exactly on it.
- Very tight targets on long videos will look rough. That's physics, not a bug.

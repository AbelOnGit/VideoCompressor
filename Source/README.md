# Video Compressor 1.5.0

A Windows desktop app that targets an output size using two-pass H.264 encoding. Target sizes use decimal megabytes (1 MB = 1,000,000 bytes). Choose a custom output folder and the app remembers it between launches. Installed copies check GitHub for stable updates on startup and show an in-app download, verification, and install flow with restart choices. The portable app and per-user installer bundle FFmpeg, so they work offline after download.

## Build

Requirements: Python 3.11 or newer, Inno Setup 7, and an internet connection for Python packages.

1. Keep `bin\ffmpeg.exe` and `bin\ffprobe.exe` in place.
2. Run `build.bat` from this folder.
3. The build creates `..\VideoCompressor.exe` and `..\VideoCompressorSetup.exe`.

The app uses PyInstaller one-file, windowed mode and bundles FFmpeg. Inno Setup creates a per-user installer from that standalone executable.

The installer is per-user: it creates a Start Menu shortcut for Windows Search and an entry in Installed Apps. It does not require administrator rights. A desktop shortcut can be selected in the installer. Outputs remain in the installed app's `Outputs` folder and are preserved if the app is uninstalled.

`VideoCompressor.svg` is the editable vector logo; `VideoCompressor.ico` is used for the app, window, and installer icons.

## Use

Open the app, select or drop a video, choose a target size, and click **Compress**. Output is saved in the `Outputs` folder as `<name>_compressed.mp4`; existing files are preserved and a number is added to avoid overwriting. Timestamped `.log` files for each run are saved in the same folder. Preferences are saved under `%APPDATA%\VideoCompressor`.

The bundled FFmpeg tools come from the Gyan.dev Windows essentials build.

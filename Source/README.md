# Video Compressor 1.1.0

A Windows desktop app that targets an output size using two-pass H.264 encoding. Choose a custom output folder and the app remembers it between launches. Installed copies check GitHub for stable updates on startup and install verified releases over the current version. FFmpeg and ffprobe are bundled; users do not need to install them.

## Build

Requirements: Python 3.11 or newer, Inno Setup 7, and an internet connection for Python packages.

1. Keep `bin\ffmpeg.exe` and `bin\ffprobe.exe` in place.
2. Run `build.bat` from this folder.
3. The standalone app is created as `..\VideoCompressor.exe` and the install wizard as `..\VideoCompressorSetup.exe`.

The build uses PyInstaller one-file, windowed mode. On first launch, the bundled tools are extracted to PyInstaller's temporary directory.

The installer is per-user: it creates a Start Menu shortcut for Windows Search and an entry in Installed Apps. It does not require administrator rights. A desktop shortcut can be selected in the installer. Outputs remain in the installed app's `Outputs` folder and are preserved if the app is uninstalled.

`VideoCompressor.svg` is the editable vector logo; `VideoCompressor.ico` is used for the app, window, and installer icons.

## Use

Open the app, select or drop a video, choose a target size, and click **Compress**. Output is saved in the `Outputs` folder as `<name>_compressed.mp4`; existing files are preserved and a number is added to avoid overwriting. Timestamped `.log` files for each run are saved in the same folder. Preferences are saved under `%APPDATA%\VideoCompressor`.

The bundled FFmpeg binaries are from the Gyan.dev Windows essentials build.

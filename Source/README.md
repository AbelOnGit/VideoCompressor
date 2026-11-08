# Video Compressor 2.0.0-beta.1

This is the local V2 beta UI redesign. It is intentionally built as a separate application and installer. The beta uses the same compression engine as the stable app, with a separate preferences directory and no automatic update checks.

## Build the beta

Requirements: Python 3.11 or newer, Inno Setup 7, and an internet connection for Python packages. Keep `bin\ffmpeg.exe` and `bin\ffprobe.exe` in place, then run `build_beta.bat` from this folder.

The script creates `build\beta\VideoCompressorBeta.exe` and `..\VideoCompressorBetaSetup.exe`. It does not build the online installer or stable installer payload. The beta installer has a distinct AppId, installs under `%LOCALAPPDATA%\Programs\VideoCompressor-Beta`, creates a `Video Compressor Beta` Start Menu entry, and saves settings under `%APPDATA%\VideoCompressor-Beta`.

On first launch, the beta may read `%APPDATA%\VideoCompressor\settings.json` once to import the stable target and output folder preferences. It writes beta preferences only to the beta directory. Beta outputs and logs use the beta installation's own `Outputs` folder unless a custom output folder is selected.

The visible version is `2.0.0-beta.1`. Automatic update checks and updater dialogs are disabled in this build. No release, tag, upload, or publishing step is part of `build_beta.bat`.

## Use

Choose a target size and select or drop a supported video (`MP4`, `MOV`, `MKV`, `AVI`, `WEBM`, `FLV`, `WMV`, `M4V`, or `TS`). The app probes the video's name, size, duration and resolution before compression. Compression and probing continue to use the existing FFmpeg-based engine. Progress displays percent, estimated time remaining, and the current pass/attempt. Each run writes its log beside the output.

The stable app remains available from the repository's existing stable artifacts and `build.bat`. Do not use `build.bat` for this beta workflow; use `build_beta.bat`.

`VideoCompressor.svg` is the editable vector logo; `VideoCompressor.ico` is used for the app and installer icons. FFmpeg comes from the Gyan.dev Windows essentials build.

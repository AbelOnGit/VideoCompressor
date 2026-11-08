# Video Compressor 2.0.0

Video Compressor V2 is the stable release of the redesigned interface. It keeps the existing FFmpeg compression engine and adds a navigation rail with Compress, Settings, and About pages. Settings support search and include output folder and supported format options.

The V2 installer uses the stable per-user install identity and folder, replacing the installed V1 app while preserving its `Outputs` folder. Existing stable settings remain available. If stable settings do not exist, V2 imports the preferences from an installed V2 beta.

## Build

Requirements: Python 3.11 or newer, Inno Setup 7, and an internet connection. Keep `bin\ffmpeg.exe` and `bin\ffprobe.exe` in place, then run `build.bat`.

The build creates `..\VideoCompressor.exe`, the small `..\VideoCompressorSetup.exe` online installer, and `..\DO_NOT_DOWNLOAD_THIS__VideoCompressorInstallerPayload.exe`. Setup downloads and verifies the payload from the stable GitHub release. Users should download only `VideoCompressorSetup.exe` (or the portable executable for portable use); the payload is labeled **DON'T DOWNLOAD THIS - Setup downloads it**.

The portable app and full installer payload bundle FFmpeg. Future V2 updates are listed on GitHub Releases and can be installed with Setup.

## Use

Choose a target size and select or drop a supported video (`MP4`, `MOV`, `MKV`, `AVI`, `WEBM`, `FLV`, `WMV`, `M4V`, or `TS`). The app probes the video's name, size, duration, and resolution before compression. Progress displays percent, estimated time remaining, and the current pass or attempt. Each run writes a log beside the output.

`VideoCompressor.svg` is the editable vector logo; `VideoCompressor.ico` is used for the app and installer icons. FFmpeg comes from the Gyan.dev Windows essentials build.

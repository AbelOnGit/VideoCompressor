# Video Compressor

A Windows desktop app for compressing a video to a target file size. The installer is published under **Releases**.

## Download

Open the [Releases](../../releases) page and download `VideoCompressorSetup.exe`. The installer is per-user and creates a Start Menu shortcut. Compressed videos and matching `.log` files go in the app's `Outputs` folder.

The current installer is not code-signed, so Windows may show a SmartScreen warning.

## Build from source

Requirements: Python 3.11+, Inno Setup 7, and an internet connection. Run `Source\build.bat`. It installs the Python requirements, downloads the Gyan.dev FFmpeg essentials build when the binaries are absent, then creates the standalone executable and installer in the repository root.

FFmpeg and ffprobe are bundled inside the app at build time; end users do not need a separate FFmpeg installation.

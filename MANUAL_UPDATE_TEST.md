# Manual update test checklist

1. Install and launch the previous stable version (currently v1.1.1) using `VideoCompressorSetup.exe` from its GitHub release.
2. Start Video Compressor with an internet connection and wait for the startup update check to download and run the newer installer.
3. Confirm the old app closes, setup replaces it, and the updated app relaunches.
4. Confirm the footer shows the new version (v1.2.0) and the app remains usable.
5. Optional failure-path check: make the installer launch fail, then confirm the app shows an update error dialog and its **Open GitHub Releases** button opens the releases page.

Do not mark the update flow as passed until this checklist has actually been performed on the target Windows machine.

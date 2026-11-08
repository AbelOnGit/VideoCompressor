# Manual update test checklist

The official v1.2.0 predates the new update popup. To test the new flow from an older version, make a test-only installer from this source with `APP_VERSION` temporarily set to `1.2.0`, install it, then restore `version.py` to `1.3.0` before building the production release.

1. Launch the test-only v1.2.0 build with an internet connection.
2. Choose **Ignore** in the update popup. Confirm it closes and does not reappear during that launch.
3. Launch the test build again. Choose **Update** and watch the percentage, verification, and installation statuses.
4. Confirm **Update installed** appears. Choose **Restart now** and confirm the new version (v1.3.0) opens.
5. Confirm `%LOCALAPPDATA%\VideoCompressor\updates\v1.3.0\VideoCompressorSetup.exe` and its release folder are gone.
6. Repeat from the test-only v1.2.0 build, choose **Update**, then **Restart later**. Confirm its current window stays open and launching Video Compressor again starts v1.3.0.
7. Optional failure-path check: make installer launch fail and confirm an error popup with **Open GitHub Releases**.

Do not mark the update flow as passed until this checklist has actually been performed on the target Windows machine.

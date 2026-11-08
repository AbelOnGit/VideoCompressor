# Manual update test checklist

The previous v1.4.0 app can test updating through the online setup bootstrapper.

1. Install and launch v1.4.0 with an internet connection.
2. Choose **Ignore** in the update popup. Confirm it closes and does not reappear during that launch.
3. Launch the old version again. Choose **Update** and watch the download, verification, and installation statuses.
4. Confirm **Update installed** appears. Choose **Restart now** and confirm the new version (v1.4.1) opens.
5. Confirm `%LOCALAPPDATA%\VideoCompressor\updates\v1.4.1\VideoCompressorSetup.exe` and its folder are gone. Confirm the new app can probe a video without downloading tools separately.
6. Repeat from v1.4.0, choose **Update**, then **Restart later**. Confirm the old running window stays open and launching Video Compressor again starts v1.4.1.
7. Optional failure-path check: make installer launch fail and confirm an error popup with **Open GitHub Releases**.

Do not mark the update flow as passed until this checklist has actually been performed on the target Windows machine.

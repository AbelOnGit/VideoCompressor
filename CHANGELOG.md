# Changelog

## 1.4.1

- Added the small online setup that downloads and verifies the full installer payload from GitHub.
- Kept FFmpeg bundled in the portable app and installer payload, so no separate tools archive is needed.
- Renamed the setup payload to `DO_NOT_DOWNLOAD_THIS__VideoCompressorInstallerPayload.exe` and labeled it “Don't download this; Setup downloads it.”

## 1.4.0

- Replaced the roughly 100 MB setup download with a small online bootstrapper that downloads and SHA-256 verifies the full installer payload from GitHub.
- Removed FFmpeg binaries from the app executable. On first launch, the app downloads and verifies a separate tools archive, extracts it into `%LOCALAPPDATA%\VideoCompressor\tools`, and reuses it on later launches.
- Added progress and error dialogs for first-run tools setup.

## 1.3.0

- Added a modal update prompt with current/new version details and Ignore/Update actions.
- Added download percentage, verification and installation statuses, followed by Restart now / Restart later choices.
- The installer no longer tries to close the running app: the updater renames its executable, starts setup detached with a clean environment, and records `%LOCALAPPDATA%\VideoCompressor\update-install.log`.
- Successful updates remove their downloaded setup folder; startup cleanup removes stale update caches and old executable names.
- Update failures show an explanation and a button to open GitHub Releases.

## 1.2.0

- Target sizes now use decimal megabytes: 1 MB = 1,000,000 bytes. The existing 4% headroom and retry behavior are unchanged.
- File size labels and compression logs now describe sizes using decimal MB consistently.
- If Windows cannot start an automatically downloaded update installer, the app now offers a button to open the GitHub Releases page.

# Changelog

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

"""HTTPS release checks and SHA-256 verified installer downloads."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

RELEASE_API = "https://api.github.com/repos/AbelOnGit/VideoCompressor/releases/latest"
ASSET_NAME = "VideoCompressorSetup.exe"
MAX_ASSET_BYTES = 300 * 1024 * 1024


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    return tuple(map(int, match.groups())) if match else None


def check_for_update(current_version: str) -> dict | None:
    """Return the latest stable release when it is newer than this build."""
    request = urllib.request.Request(
        RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"VideoCompressor/{current_version}",
        },
    )
    with urllib.request.urlopen(request, timeout=6) as response:
        release = json.loads(response.read().decode("utf-8"))

    if release.get("draft") or release.get("prerelease"):
        return None
    current = _version_tuple(current_version)
    latest = _version_tuple(release.get("tag_name", ""))
    if current is None or latest is None or latest <= current:
        return None
    return release


def download_update(release: dict) -> Path:
    """Download the official installer and require GitHub's published SHA-256."""
    tag = str(release.get("tag_name", ""))
    if _version_tuple(tag) is None:
        raise ValueError("The release has an invalid version tag.")

    asset = next((item for item in release.get("assets", [])
                  if item.get("name") == ASSET_NAME), None)
    if not asset:
        raise ValueError(f"The release does not contain {ASSET_NAME}.")

    digest = str(asset.get("digest", ""))
    match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", digest)
    if not match:
        raise ValueError("The release installer does not have a verifiable SHA-256 digest.")
    expected_hash = match.group(1).lower()

    url = str(asset.get("browser_download_url", ""))
    prefix = "https://github.com/AbelOnGit/VideoCompressor/releases/download/"
    if not url.startswith(prefix):
        raise ValueError("The release installer URL was not on the official project repository.")

    expected_size = int(asset.get("size", 0))
    if expected_size <= 0 or expected_size > MAX_ASSET_BYTES:
        raise ValueError("The release installer size is invalid.")

    update_root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VideoCompressor" / "updates" / tag
    update_root.mkdir(parents=True, exist_ok=True)
    destination = update_root / ASSET_NAME
    if destination.is_file() and destination.stat().st_size == expected_size:
        if _sha256(destination) == expected_hash:
            return destination

    request = urllib.request.Request(url, headers={"User-Agent": "VideoCompressor-Updater"})
    temporary_path: Path | None = None
    hasher = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix="VideoCompressor-", suffix=".download",
                dir=update_root, delete=False,
            ) as output:
                temporary_path = Path(output.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_ASSET_BYTES:
                        raise ValueError("The update download exceeded the allowed size.")
                    hasher.update(chunk)
                    output.write(chunk)

        if total != expected_size:
            raise ValueError("The downloaded installer size did not match the release.")
        if hasher.hexdigest() != expected_hash:
            raise ValueError("The downloaded installer failed SHA-256 verification.")

        temporary_path.replace(destination)
        return destination
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

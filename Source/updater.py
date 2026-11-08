"""HTTPS release checks and SHA-256 verified installer downloads."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

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


def download_update(release: dict, on_progress: Callable[[int, int], None] | None = None,
                   on_status: Callable[[str], None] | None = None) -> Path:
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
        if on_status:
            on_status("Verifying...")
        if _sha256(destination) == expected_hash:
            if on_progress:
                on_progress(expected_size, expected_size)
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
                    if on_progress:
                        on_progress(total, expected_size)

        if on_status:
            on_status("Verifying...")
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


def cleanup_obsolete_updates(current_version: str,
                             update_root: Path | None = None) -> None:
    """Remove cached release folders already installed by this app version."""
    current = _version_tuple(current_version)
    if current is None:
        return
    root = update_root or (Path(os.environ.get("LOCALAPPDATA", Path.home()))
                           / "VideoCompressor" / "updates")
    if not root.is_dir():
        return
    for child in root.iterdir():
        if not child.is_dir():
            continue
        downloaded = _version_tuple(child.name)
        if downloaded is not None and current >= downloaded:
            shutil.rmtree(child, ignore_errors=True)
    try:
        root.rmdir()
    except OSError:
        pass


def cleanup_previous_executables(install_dir: Path) -> None:
    """Remove app images renamed by a completed update, if Windows permits."""
    candidates = [install_dir / "VideoCompressor.old.exe"]
    candidates.extend(install_dir.glob("VideoCompressor.old-*.exe"))
    for old_exe in candidates:
        try:
            old_exe.unlink(missing_ok=True)
        except OSError:
            pass

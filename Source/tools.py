"""Download and verify the FFmpeg tools on first launch."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from updater import RELEASE_API

TOOLS_ASSET_NAME = "VideoCompressorTools.zip"
MAX_TOOLS_BYTES = 300 * 1024 * 1024
RELEASE_URL_PREFIX = "https://github.com/AbelOnGit/VideoCompressor/releases/download/"
REQUIRED_TOOLS = ("ffmpeg.exe", "ffprobe.exe")


def tools_directory() -> Path:
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent / "bin"
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return local_app_data / "VideoCompressor" / "tools"


def tools_are_ready() -> bool:
    directory = tools_directory()
    return all((directory / name).is_file() and (directory / name).stat().st_size > 0
               for name in REQUIRED_TOOLS)


def ensure_tools(on_progress: Callable[[int, int], None] | None = None,
                 on_status: Callable[[str], None] | None = None) -> Path:
    """Fetch the stable release's tools zip, verify it, and install both tools."""
    destination = tools_directory()
    if tools_are_ready():
        return destination

    if on_status:
        on_status("Checking GitHub for the video tools...")
    request = urllib.request.Request(
        RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "VideoCompressor-Tools"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        release = json.loads(response.read().decode("utf-8"))
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("GitHub did not return a stable Video Compressor release.")

    asset = next((item for item in release.get("assets", [])
                  if item.get("name") == TOOLS_ASSET_NAME), None)
    if not asset:
        raise ValueError(f"The latest stable release does not contain {TOOLS_ASSET_NAME}.")
    match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", str(asset.get("digest", "")))
    if not match:
        raise ValueError("The tools archive has no valid GitHub SHA-256 digest.")
    expected_hash = match.group(1).lower()
    expected_size = int(asset.get("size", 0))
    if expected_size <= 0 or expected_size > MAX_TOOLS_BYTES:
        raise ValueError("The tools archive size is invalid.")
    url = str(asset.get("browser_download_url", ""))
    if not url.startswith(RELEASE_URL_PREFIX):
        raise ValueError("The tools archive URL is not from the official GitHub repository.")

    version = str(release.get("tag_name", "unknown"))
    app_data = destination.parent
    cache_dir = app_data / "tools-downloads" / version
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / TOOLS_ASSET_NAME
    if archive_path.is_file() and archive_path.stat().st_size == expected_size:
        if _sha256(archive_path) != expected_hash:
            archive_path.unlink()
    if not archive_path.is_file():
        download_request = urllib.request.Request(url, headers={"User-Agent": "VideoCompressor-Tools"})
        temporary_path: Path | None = None
        hasher = hashlib.sha256()
        total = 0
        if on_status:
            on_status("Downloading video tools... 0%")
        try:
            with urllib.request.urlopen(download_request, timeout=45) as response:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix="VideoCompressor-tools-", suffix=".download",
                    dir=cache_dir, delete=False,
                ) as output:
                    temporary_path = Path(output.name)
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_TOOLS_BYTES:
                            raise ValueError("The tools download exceeded the allowed size.")
                        hasher.update(chunk)
                        output.write(chunk)
                        if on_progress:
                            on_progress(total, expected_size)
            if total != expected_size:
                raise ValueError("The downloaded tools size does not match the GitHub release.")
            if hasher.hexdigest() != expected_hash:
                raise ValueError("The downloaded tools failed SHA-256 verification.")
            temporary_path.replace(archive_path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()

    if on_status:
        on_status("Verifying video tools...")
    if archive_path.stat().st_size != expected_size or _sha256(archive_path) != expected_hash:
        raise ValueError("The cached tools archive failed size or SHA-256 verification.")

    if on_status:
        on_status("Installing video tools...")
    staging = app_data / f"tools-install-{os.getpid()}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = {Path(info.filename).name.lower(): info
                       for info in archive.infolist()
                       if not info.is_dir() and Path(info.filename).name.lower() in REQUIRED_TOOLS
                       and Path(info.filename).parent == Path(".")}
            if any(name not in members for name in REQUIRED_TOOLS):
                raise ValueError("The verified tools archive is missing ffmpeg.exe or ffprobe.exe.")
            for name in REQUIRED_TOOLS:
                extracted = archive.extract(members[name], staging)
                if Path(extracted).name.lower() != name:
                    raise ValueError("The tools archive contains an unexpected file path.")
        if any(not (staging / name).is_file() or (staging / name).stat().st_size == 0
               for name in REQUIRED_TOOLS):
            raise ValueError("The extracted tools files are incomplete.")
        previous = app_data / f"tools-old-{os.getpid()}"
        if destination.exists():
            shutil.rmtree(previous, ignore_errors=True)
            destination.replace(previous)
        staging.replace(destination)
        shutil.rmtree(previous, ignore_errors=True)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
        try:
            cache_dir.parent.rmdir()
        except OSError:
            pass

    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

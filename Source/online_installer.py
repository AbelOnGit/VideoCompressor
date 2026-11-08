"""Small bootstrap installer that downloads the verified full setup from GitHub."""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk

RELEASE_API = "https://api.github.com/repos/AbelOnGit/VideoCompressor/releases/latest"
PAYLOAD_NAME = "DO_NOT_DOWNLOAD_THIS__VideoCompressorInstallerPayload.exe"
MAX_PAYLOAD_BYTES = 300 * 1024 * 1024
RELEASE_URL_PREFIX = "https://github.com/AbelOnGit/VideoCompressor/releases/download/"


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    return tuple(map(int, match.groups())) if match else None


def _app_data() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VideoCompressor"


def _clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in list(environment):
        upper = name.upper()
        if (upper in {"_MEIPASS", "_MEIPASS2"}
                or upper.startswith("_PYI_")
                or upper.startswith("PYINSTALLER_")):
            environment.pop(name, None)
    return environment


def _latest_payload(on_progress=None, on_status=None) -> tuple[Path, str]:
    request = urllib.request.Request(
        RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "VideoCompressor-OnlineInstaller"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        release = json.loads(response.read().decode("utf-8"))
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("GitHub did not return a stable Video Compressor release.")
    version = str(release.get("tag_name", ""))
    if _version_tuple(version) is None:
        raise ValueError("The latest GitHub release has an invalid version tag.")

    asset = next((item for item in release.get("assets", [])
                  if item.get("name") == PAYLOAD_NAME), None)
    if not asset:
        raise ValueError(f"The stable release does not contain {PAYLOAD_NAME}.")
    match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", str(asset.get("digest", "")))
    if not match:
        raise ValueError("The installer payload has no valid GitHub SHA-256 digest.")
    expected_hash = match.group(1).lower()
    expected_size = int(asset.get("size", 0))
    if expected_size <= 0 or expected_size > MAX_PAYLOAD_BYTES:
        raise ValueError("The installer payload size is invalid.")
    url = str(asset.get("browser_download_url", ""))
    if not url.startswith(RELEASE_URL_PREFIX):
        raise ValueError("The installer payload URL is not from the official project repository.")

    payload_dir = _app_data() / "online-installer" / version
    payload_dir.mkdir(parents=True, exist_ok=True)
    payload = payload_dir / PAYLOAD_NAME
    if payload.is_file() and payload.stat().st_size == expected_size:
        if _sha256(payload) == expected_hash:
            if on_status:
                on_status("Verifying installer...")
            return payload, version
        payload.unlink()

    if on_status:
        on_status("Downloading installer... 0%")
    temporary: Path | None = None
    digest = hashlib.sha256()
    total = 0
    try:
        download_request = urllib.request.Request(url, headers={"User-Agent": "VideoCompressor-OnlineInstaller"})
        with urllib.request.urlopen(download_request, timeout=60) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix="VideoCompressor-installer-", suffix=".download",
                dir=payload_dir, delete=False,
            ) as output:
                temporary = Path(output.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_PAYLOAD_BYTES:
                        raise ValueError("The installer download exceeded the size limit.")
                    digest.update(chunk)
                    output.write(chunk)
                    if on_progress:
                        on_progress(total, expected_size)
        if on_status:
            on_status("Verifying installer...")
        if total != expected_size:
            raise ValueError("The installer download size did not match the release metadata.")
        if digest.hexdigest() != expected_hash:
            raise ValueError("The installer download failed SHA-256 verification.")
        temporary.replace(payload)
        return payload, version
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _installer_args(arguments: list[str]) -> list[str]:
    passed = []
    for argument in arguments:
        upper = argument.upper()
        if upper.startswith("/CLOSEAPPLICATIONS"):
            continue
        if (upper in {"/VERYSILENT", "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"}
                or upper.startswith("/DIR=") or upper.startswith("/LOG=")):
            passed.append(argument)
    return passed


def _run_installer(payload: Path, arguments: list[str]) -> int:
    environment = _clean_environment()
    cwd = str(payload.parent)
    if any(arg.upper() in {"/VERYSILENT", "/SILENT"} for arg in arguments):
        flags = (getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                 | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200))
    else:
        flags = 0
    process = subprocess.Popen([str(payload), *arguments], cwd=cwd, env=environment,
                               creationflags=flags, close_fds=True)
    return process.wait()


def _write_progress(stage: str, percent: int = 0) -> None:
    try:
        path = _app_data() / "online-installer-progress.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"stage": stage, "percent": percent}), encoding="utf-8")
    except OSError:
        pass


def _append_failure_log(arguments: list[str], message: str) -> None:
    log_path = next((arg[5:].strip('"') for arg in arguments if arg.upper().startswith("/LOG=")), None)
    if not log_path:
        return
    try:
        log = Path(log_path)
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8", errors="replace") as output:
            output.write(f"\nOnline installer failure: {message}\n")
    except OSError:
        pass


class InstallerWindow:
    def __init__(self, arguments: list[str]):
        self.arguments = _installer_args(arguments)
        self.events: queue.Queue = queue.Queue()
        self.exit_code = 1
        self.root = tk.Tk()
        self.root.title("Video Compressor Setup")
        self.root.geometry("500x230")
        self.root.resizable(False, False)
        self.root.configure(background="#202020")
        self.root.protocol("WM_DELETE_WINDOW", lambda:None)

        body = tk.Frame(self.root, background="#202020")
        body.pack(fill="both", expand=True, padx=28, pady=24)
        tk.Label(body, text="Video Compressor", font=("Segoe UI", 20, "bold"),
                 foreground="white", background="#202020").pack(anchor="w", pady=(0, 8))
        tk.Label(body, text="Online setup downloads and verifies the latest stable installer.",
                 font=("Segoe UI", 10), foreground="#c7c7c7", background="#202020").pack(anchor="w", pady=(0, 18))
        self.status = tk.Label(body, text="Checking GitHub releases...", anchor="w",
                               font=("Segoe UI", 10), foreground="white", background="#202020")
        self.status.pack(fill="x", pady=(0, 10))
        self.progress = ttk.Progressbar(body, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        self.error_text = tk.Label(body, text="", justify="left", wraplength=440,
                                   foreground="#ff9b9b", background="#202020")
        self.error_text.pack(fill="x", pady=(10, 0))
        self.buttons = tk.Frame(body, background="#202020")
        self.buttons.pack(side="bottom", fill="x", pady=(14, 0))
        self.release_button = tk.Button(self.buttons, text="Open GitHub Releases", command=self.open_releases)
        self.close_button = tk.Button(self.buttons, text="Close", command=self.close)
        self.root.after(100, self.process_events)
        threading.Thread(target=self.install_worker, daemon=True).start()

    def install_worker(self):
        try:
            payload, version = _latest_payload(
                on_progress=lambda received, total:self.events.put(("progress", (received, total))),
                on_status=lambda status:self.events.put(("status", status)),
            )
            self.events.put(("status", f"Starting Video Compressor {version} setup..."))
            _write_progress("Installing update...", 100)
            exit_code = _run_installer(payload, self.arguments)
            if exit_code != 0:
                raise RuntimeError(f"The full installer exited with code {exit_code}.")
            shutil.rmtree(payload.parent, ignore_errors=True)
            try:
                payload.parent.parent.rmdir()
            except OSError:
                pass
            self.events.put(("success", version))
        except Exception as error:
            self.events.put(("error", str(error)))
        finally:
            try:(_app_data() / "online-installer-progress.json").unlink(missing_ok=True)
            except OSError:pass

    def process_events(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "status":
                    self.status.configure(text=value)
                    if value.startswith("Verifying"):
                        _write_progress("Verifying...", int(self.progress["value"]))
                    elif value.startswith("Downloading"):
                        _write_progress("Downloading update...", int(self.progress["value"]))
                elif event == "progress":
                    received, total = value
                    percent = int(min(100, received / max(total, 1) * 100))
                    self.progress.configure(value=percent)
                    self.status.configure(text=f"Downloading installer... {percent}%")
                    _write_progress("Downloading update...", percent)
                elif event == "success":
                    self.exit_code = 0
                    self.status.configure(text=f"Video Compressor {value} setup completed.")
                    self.progress.configure(value=100)
                    self.root.protocol("WM_DELETE_WINDOW", self.close)
                    self.close_button.pack(side="right")
                    self.root.after(1500, self.close)
                elif event == "error":
                    self.exit_code = 1
                    self.status.configure(text="Setup could not be completed.")
                    self.error_text.configure(text=value)
                    self.root.protocol("WM_DELETE_WINDOW", self.close)
                    self.release_button.pack(side="right", padx=(0, 8))
                    self.close_button.pack(side="right")
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self.process_events)

    def open_releases(self):
        webbrowser.open("https://github.com/AbelOnGit/VideoCompressor/releases")

    def close(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main() -> None:
    arguments = sys.argv[1:]
    silent = any(arg.upper() in {"/VERYSILENT", "/SILENT"} for arg in arguments)
    if silent:
        args = _installer_args(arguments)
        progress_path = _app_data() / "online-installer-progress.json"
        try:
            payload, _ = _latest_payload(
                on_progress=lambda received, total:_write_progress("Downloading update...",
                                                                    int(min(100, received / max(total, 1) * 100))),
                on_status=lambda status:_write_progress(status, 0),
            )
            _write_progress("Installing update...", 100)
            exit_code = _run_installer(payload, args)
            if exit_code == 0:
                shutil.rmtree(payload.parent, ignore_errors=True)
                try:payload.parent.parent.rmdir()
                except OSError:pass
            else:
                _append_failure_log(arguments, f"The full installer exited with code {exit_code}.")
            raise SystemExit(exit_code)
        except SystemExit:
            raise
        except Exception as error:
            _append_failure_log(arguments, str(error))
            raise SystemExit(1)
        finally:
            try:progress_path.unlink(missing_ok=True)
            except OSError:pass
    window = InstallerWindow(arguments)
    window.root.mainloop()
    raise SystemExit(window.exit_code)


if __name__ == "__main__":
    main()

"""FFprobe metadata and cancellable two-pass H.264 compression."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def app_root() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def output_directory() -> Path:
    folder = app_root() / "Outputs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def next_output_path(source: str, extension: str = ".mp4") -> Path:
    """Return an unused output path and reserve its matching log name logically."""
    src = Path(source)
    folder = output_directory()
    stem = f"{src.stem} Compressed"
    number = 1
    while True:
        suffix = "" if number == 1 else f" {number}"
        candidate = folder / f"{stem}{suffix}{extension}"
        log_path = candidate.with_suffix(".log")
        if (not candidate.exists() and not log_path.exists()
                and os.path.normcase(str(candidate)) != os.path.normcase(str(src))):
            return candidate
        number += 1


def human_size(size: int) -> str:
    """Format a file size as a readable rounded number and unit."""
    units = [(1024 ** 3, "gigabyte"), (1024 ** 2, "megabyte"), (1024, "kilobyte")]
    for divisor, unit in units:
        if size >= divisor:
            amount = size / divisor
            value = round(amount)
            return f"{value} {unit if value == 1 else unit + 's'}"
    return f"{size} bytes"


def format_fps(fps: float) -> str:
    return f"{fps:.1f}".rstrip("0").rstrip(".")


def write_run_log(source: str, target_mb: float, result: dict | None,
                  output_path: str | None = None, meta: dict | None = None,
                  steps: list[str] | None = None, started: datetime | None = None) -> str:
    folder = output_directory()
    if output_path:
        path = Path(output_path).with_suffix(".log")
    else:
        path = next_output_path(source, ".mp4").with_suffix(".log")

    local_time = (started or datetime.now().astimezone()).astimezone()
    hour = local_time.hour % 12 or 12
    meridiem = "a.m." if local_time.hour < 12 else "p.m."
    lines = [
        "VIDEO COMPRESSION LOG",
        f"Date and time: {local_time.month}/{local_time.day}/{local_time:%y} at {hour}:{local_time:%M} {meridiem} (local time)",
        "",
        "VIDEO DETAILS",
        f"Source: {source}",
        f"Original size: {human_size(os.path.getsize(source)) if os.path.exists(source) else 'Unavailable'}",
        f"Target size: {target_mb:g} megabytes",
    ]
    if meta:
        mins, secs = divmod(int(meta["duration"]), 60)
        lines.extend([
            f"Duration: {mins}:{secs:02d}",
            f"Resolution: {meta['width']} x {meta['height']}",
            f"Frame rate: {format_fps(meta['fps'])} fps" if meta.get("fps") else "Frame rate: unavailable",
            f"Audio: {meta.get('audio_description', 'None')}",
        ])
    lines += ["", "COMPRESSION STEPS"]
    if steps:
        lines.extend(f"{i}. {step}" for i, step in enumerate(steps, 1))
    else:
        lines.append("No encoding steps were completed.")

    lines += ["", "RESULT"]
    if result and result.get("cancelled"):
        lines.append("Status: Cancelled")
    elif result and result.get("error"):
        lines.extend(["Status: Error", f"Details: {result['error']}"])
    elif result:
        lines.extend([
            "Status: Done",
            f"Output: {result.get('path', '')}",
            f"Final size: {human_size(result.get('size', 0))}",
        ])
    else:
        lines.append("Status: Incomplete")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def binary_path(name: str) -> str:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(root / "bin" / name)


def _ratio(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    try:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(path: str) -> dict:
    args = [binary_path("ffprobe.exe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path]
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ffprobe could not read this video.")
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise RuntimeError("No video stream was found in this file.")
    duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("Could not determine the video duration.")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    audio_description = "None"
    if audio:
        audio_description = f"{audio.get('codec_name', 'unknown')}"
        if audio.get("channels"):
            audio_description += f", {audio['channels']} channel(s)"
        if audio.get("sample_rate"):
            audio_description += f", {audio['sample_rate']} Hz"
    return {
        "duration": duration,
        "width": int(video.get("width", 0)),
        "height": int(video.get("height", 0)),
        "fps": _ratio(video.get("avg_frame_rate")) or _ratio(video.get("r_frame_rate")),
        "has_audio": audio is not None,
        "audio_description": audio_description,
    }


class CompressionJob:
    def __init__(self, source: str, target_mb: float, on_progress: Callable, on_status: Callable, on_done: Callable):
        self.source, self.target_mb = source, target_mb
        self.on_progress, self.on_status, self.on_done = on_progress, on_status, on_done
        self.cancel_event = threading.Event()
        self.process: subprocess.Popen | None = None
        self.temp_dir: str | None = None
        self.steps: list[str] = []
        self.meta: dict | None = None
        self.started = datetime.now().astimezone()
        self.output_path: str | None = None

    def cancel(self):
        self.cancel_event.set()
        p = self.process
        if p and p.poll() is None:
            try:
                p.kill()
            except OSError:
                pass

    def run(self):
        result = None
        try:
            self.meta = probe(self.source)
            target_bytes = int(self.target_mb * 1024 * 1024)
            source_size = os.path.getsize(self.source)
            self.output_path = str(next_output_path(self.source, ".mp4"))
            if source_size < target_bytes:
                self.steps.append("The source is already smaller than the target; encoding anyway as requested.")

            self.temp_dir = tempfile.mkdtemp(prefix="videocompressor_")
            tmp_out = str(Path(self.temp_dir) / "result.mp4")
            audio_kbps = 96 if self.meta["has_audio"] else 0
            total_kbps = target_bytes * 0.96 * 8 / self.meta["duration"] / 1000
            video_kbps = max(20, total_kbps - audio_kbps)
            scale, fps, channels = None, None, None
            if video_kbps < 1000: scale = 720
            if video_kbps < 500: scale = 480
            if video_kbps < 250: scale = 360
            if video_kbps < 120: scale = 240
            if video_kbps < 120 and self.meta["fps"] > 15: fps = 15
            if video_kbps < 50 and self.meta["has_audio"]: audio_kbps, channels = 32, 1

            output_height = min(self.meta["height"], scale) if scale else self.meta["height"]
            if output_height < self.meta["height"]:
                self.steps.append(f"Reduced resolution from {self.meta['width']} x {self.meta['height']} to about {output_height}p because the target bitrate is low.")
            else:
                self.steps.append(f"Kept the source resolution at {self.meta['width']} x {self.meta['height']} (no upscaling).")
            if fps:
                self.steps.append(f"Reduced frame rate from {self.meta['fps']:g} fps to {fps} fps to fit the low target bitrate.")
            else:
                self.steps.append(f"Kept the source frame rate at {format_fps(self.meta['fps'])} fps." if self.meta["fps"] else "Kept the source frame rate; ffprobe did not report a rate.")
            if self.meta["has_audio"]:
                self.steps.append(f"Encoded audio as AAC at {audio_kbps} kbps" + (", mono." if channels == 1 else "."))
            else:
                self.steps.append("The source has no audio stream; skipped audio encoding.")

            for attempt in range(4):
                if self.cancel_event.is_set(): raise InterruptedError("Cancelled")
                self.steps.append(f"Attempt {attempt + 1}: set video bitrate to {video_kbps:.0f} kbps; encoder H.264 (libx264), slow preset.")
                self._encode(self.meta, video_kbps, audio_kbps, scale, fps, channels, tmp_out, attempt)
                actual = os.path.getsize(tmp_out)
                if actual <= target_bytes:
                    self.steps.append(f"Attempt {attempt + 1}: output measured {human_size(actual)}, within the target.")
                    break
                if attempt == 3:
                    raise RuntimeError(f"Output remained over the target after 3 retries ({human_size(actual)}).")
                overshoot = (actual - target_bytes) / target_bytes
                lower_bitrate = max(20, video_kbps * (1 - overshoot - 0.05))
                self.steps.append(f"Attempt {attempt + 1}: output was {human_size(actual)}, over target; lowered video bitrate from {video_kbps:.0f} to {lower_bitrate:.0f} kbps and retried both passes.")
                video_kbps = lower_bitrate
                self.on_status(f"Over target; retrying at a lower bitrate ({attempt + 1}/3).")
            os.replace(tmp_out, self.output_path)
            result = {"path": self.output_path, "size": os.path.getsize(self.output_path)}
        except InterruptedError:
            result = {"cancelled": True}
        except Exception as e:
            result = {"error": str(e)}
        finally:
            if self.temp_dir:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            try:
                result["log_path"] = write_run_log(self.source, self.target_mb, result, self.output_path, self.meta, self.steps, self.started)
            except OSError:
                pass
            self.on_done(result)

    def _encode(self, meta, video_kbps, audio_kbps, scale, fps, channels, output, attempt):
        ff = binary_path("ffmpeg.exe")
        passlog = str(Path(self.temp_dir) / "passlog")
        common = [ff, "-hide_banner", "-y", "-i", self.source, "-map", "0:v:0", "-c:v", "libx264", "-preset", "slow",
                  "-b:v", f"{video_kbps:.0f}k", "-maxrate", f"{video_kbps*1.5:.0f}k", "-bufsize", f"{video_kbps*1.5:.0f}k",
                  "-pix_fmt", "yuv420p"]
        if scale:
            common += ["-vf", f"scale='if(gt(ih,{scale}),-2,iw)':'if(gt(ih,{scale}),{scale},ih)'"]
        if fps: common += ["-r", str(fps)]
        if meta["has_audio"]:
            common += ["-map", "0:a:0?", "-c:a", "aac", "-b:a", f"{audio_kbps}k"]
            if channels: common += ["-ac", str(channels)]
        else: common += ["-an"]
        for pass_no, label in ((1, "Pass 1/2"), (2, "Pass 2/2")):
            if self.cancel_event.is_set(): raise InterruptedError("Cancelled")
            if pass_no == 1:
                self.steps.append(f"Attempt {attempt + 1}, Pass 1/2: analyzed video for two-pass bitrate distribution at {video_kbps:.0f} kbps; no output video was written.")
            else:
                audio_step = f" plus {audio_kbps} kbps AAC audio" if meta["has_audio"] else "; no audio stream"
                self.steps.append(f"Attempt {attempt + 1}, Pass 2/2: encoded the MP4 at {video_kbps:.0f} kbps video{audio_step} with H.264 (libx264).")
            self.on_status(f"{label} · attempt {attempt + 1}")
            args = common + ["-pass", str(pass_no), "-passlogfile", passlog, "-progress", "pipe:1", "-nostats"]
            if pass_no == 1: args += ["-an", "-f", "null", "NUL"]
            else: args += ["-movflags", "+faststart", output]
            self._run_ffmpeg(args, meta["duration"], (pass_no - 1) / 2)

    def _run_ffmpeg(self, args, duration, progress_offset):
        self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW, bufsize=1)
        stderr_lines = []
        def read_err():
            for line in self.process.stderr:
                stderr_lines.append(line.rstrip())
                if len(stderr_lines) > 30: del stderr_lines[:10]
        reader = threading.Thread(target=read_err, daemon=True); reader.start()
        started = time.monotonic()
        for line in self.process.stdout:
            if self.cancel_event.is_set(): self.process.kill(); break
            if line.startswith("out_time_ms="):
                try:
                    seconds = int(line.split("=", 1)[1]) / 1_000_000
                    fraction = min(1, seconds / duration)
                    done = progress_offset + fraction / 2
                    elapsed = max(.1, time.monotonic() - started)
                    remaining = max(0, (duration - seconds) / max(.01, seconds / elapsed))
                    self.on_progress(done, remaining)
                except (ValueError, ZeroDivisionError): pass
        code = self.process.wait(); reader.join(timeout=2); self.process = None
        if self.cancel_event.is_set(): raise InterruptedError("Cancelled")
        if code:
            raise RuntimeError("FFmpeg failed:\n" + "\n".join(stderr_lines[-12:]))

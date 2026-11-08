"""Create the separately downloadable FFmpeg tools release archive."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

source = Path(__file__).resolve().parent / "bin"
destination = Path(__file__).resolve().parent.parent / "VideoCompressorTools.zip"
required = ("ffmpeg.exe", "ffprobe.exe")
missing = [name for name in required if not (source / name).is_file()]
if missing:
    raise SystemExit("Missing tools: " + ", ".join(missing))
with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
    for name in required:
        archive.write(source / name, arcname=name)
print(f"Created {destination} ({destination.stat().st_size:,} bytes)")

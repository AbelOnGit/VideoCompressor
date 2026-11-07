$ErrorActionPreference = 'Stop'
$bin = Join-Path $PSScriptRoot 'bin'
$ffmpegPath = Join-Path $bin 'ffmpeg.exe'
$ffprobePath = Join-Path $bin 'ffprobe.exe'
if ((Test-Path -LiteralPath $ffmpegPath) -and (Test-Path -LiteralPath $ffprobePath)) { exit 0 }
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$tempDir = Join-Path $env:TEMP ('VideoCompressorFFmpeg-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir | Out-Null
try {
    $archive = Join-Path $tempDir 'ffmpeg.zip'
    $extract = Join-Path $tempDir 'extracted'
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $archive
    Expand-Archive -LiteralPath $archive -DestinationPath $extract
    $ffmpeg = Get-ChildItem -LiteralPath $extract -Filter 'ffmpeg.exe' -File -Recurse | Select-Object -First 1
    $ffprobe = Get-ChildItem -LiteralPath $extract -Filter 'ffprobe.exe' -File -Recurse | Select-Object -First 1
    if (-not $ffmpeg -or -not $ffprobe) { throw 'The Gyan.dev archive did not contain both ffmpeg.exe and ffprobe.exe.' }
    Copy-Item -LiteralPath $ffmpeg.FullName -Destination $ffmpegPath -Force
    Copy-Item -LiteralPath $ffprobe.FullName -Destination $ffprobePath -Force
} finally {
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}

@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if not exist "bin\ffmpeg.exe" powershell -NoProfile -ExecutionPolicy Bypass -File download_ffmpeg.ps1
if errorlevel 1 exit /b 1
if not exist "bin\ffprobe.exe" powershell -NoProfile -ExecutionPolicy Bypass -File download_ffmpeg.ps1
if errorlevel 1 exit /b 1
for /f "usebackq delims=" %%V in (`python -c "from version import APP_VERSION; print(APP_VERSION)"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION (
  echo Could not read APP_VERSION from version.py.
  exit /b 1
)
python -m PyInstaller --noconfirm --clean --onefile --noconsole --windowed --name VideoCompressor --icon "VideoCompressor.ico" --distpath .. --collect-all customtkinter --collect-all tkinterdnd2 --add-data "VideoCompressor.ico;." main.py
if errorlevel 1 exit /b 1
python package_tools.py
if errorlevel 1 exit /b 1
if not exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" (
  echo Inno Setup 7 is required to build the installer.
  echo Install it from https://jrsoftware.org/isdl.php
  exit /b 1
)
"%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" /DMyAppVersion=%APP_VERSION% /DSetupFileName=VideoCompressorInstallerPayload VideoCompressor.iss
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --noconsole --windowed --name VideoCompressorSetup --icon "VideoCompressor.ico" --distpath .. --workpath "build\online_installer" --specpath "build\online_installer_spec" online_installer.py
if errorlevel 1 exit /b 1
echo Built ..\VideoCompressor.exe, ..\VideoCompressorSetup.exe, ..\VideoCompressorInstallerPayload.exe, and ..\VideoCompressorTools.zip

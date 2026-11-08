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
if not "%APP_VERSION%"=="2.0.0-beta.1" (
  echo Unexpected beta version: %APP_VERSION%
  exit /b 1
)

python -m PyInstaller --noconfirm --clean --onefile --noconsole --windowed --name VideoCompressorBeta --distpath "build\beta" --workpath "build\beta-work" --specpath "build\beta-spec" --icon "%CD%\VideoCompressor.ico" --collect-all customtkinter --collect-all tkinterdnd2 --add-data "%CD%\VideoCompressor.ico;." --add-binary "%CD%\bin\ffmpeg.exe;bin" --add-binary "%CD%\bin\ffprobe.exe;bin" main.py
if errorlevel 1 exit /b 1

if not exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" (
  echo Inno Setup 7 is required to build the beta installer.
  exit /b 1
)
"%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" VideoCompressorBeta.iss
if errorlevel 1 exit /b 1

echo Built the local beta only: ..\VideoCompressorBetaSetup.exe
echo Nothing was uploaded, published, tagged, or released.

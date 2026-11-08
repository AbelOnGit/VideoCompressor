#define MyAppVersion "2.0.0-beta.1"
#define MyAppFileVersion "2.0.0.1"

[Setup]
AppId={{D84891A2-6C7D-4B5E-9819-3F5AD76B2D34}
AppName=Video Compressor Beta
AppVersion={#MyAppVersion}
AppPublisher=Video Compressor
DefaultDirName={localappdata}\Programs\VideoCompressor-Beta
DefaultGroupName=Video Compressor Beta
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=no
RestartApplications=no
UninstallDisplayName=Video Compressor Beta
UninstallDisplayIcon={app}\VideoCompressorBeta.exe
SetupIconFile=VideoCompressor.ico
VersionInfoVersion={#MyAppFileVersion}
VersionInfoTextVersion={#MyAppVersion}
OutputDir=..
OutputBaseFilename=VideoCompressorBetaSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Dirs]
Name: "{app}\Outputs"; Flags: uninsneveruninstall

[Files]
Source: "build\beta\VideoCompressorBeta.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Video Compressor Beta"; Filename: "{app}\VideoCompressorBeta.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Video Compressor Beta"; Filename: "{app}\VideoCompressorBeta.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\VideoCompressorBeta.exe"; Description: "Launch Video Compressor Beta"; Flags: nowait postinstall skipifsilent

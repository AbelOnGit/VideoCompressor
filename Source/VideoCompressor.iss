[Setup]
AppId={{AC80A442-00CA-4F68-A157-C19BC21665AF}
AppName=Video Compressor
AppVersion={#MyAppVersion}
AppPublisher=Video Compressor
DefaultDirName={localappdata}\Programs\VideoCompressor
DefaultGroupName=Video Compressor
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=no
RestartApplications=no
UninstallDisplayName=Video Compressor
UninstallDisplayIcon={app}\VideoCompressor.exe
SetupIconFile=VideoCompressor.ico
VersionInfoVersion={#MyAppVersion}.0
OutputDir=..
OutputBaseFilename=VideoCompressorSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Dirs]
Name: "{app}\Outputs"; Flags: uninsneveruninstall

[Files]
Source: "..\VideoCompressor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Video Compressor"; Filename: "{app}\VideoCompressor.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Video Compressor"; Filename: "{app}\VideoCompressor.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\VideoCompressor.exe"; Description: "Launch Video Compressor"; Flags: nowait postinstall skipifsilent

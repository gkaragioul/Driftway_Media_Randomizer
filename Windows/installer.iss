; GKMediaRandomizer — Inno Setup installer script
; Builds from PyInstaller one-dir output in Windows\dist\GKMediaRandomizer\

#define MyAppName "GKMediaRandomizer"
#define MyAppVersion "2.1.2"
#define MyAppPublisher "George Karagioules"
#define MyAppExeName "GKMediaRandomizer.exe"
#define MyAppId "{{B8F2D3A1-7C4E-4F5A-9B6D-2E8F1A3C5D7E}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=assets\license.txt
OutputDir=dist-installer
OutputBaseFilename=GKMediaRandomizer_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico
WizardStyle=modern
ArchitecturesAllowed=x64
PrivilegesRequired=admin
CloseApplications=force

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenu"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; PyInstaller one-dir output
Source: "dist\GKMediaRandomizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icon
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: startmenu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch GKMediaRandomizer"; Flags: nowait postinstall skipifsilent

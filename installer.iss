#define MyAppName "Pato Recordatorio"
#define MyAppVersion "1.0"
#define MyAppPublisher "ll"
#define MyAppExeName "PatoRecordatorio.exe"

[Setup]
AppId={{E20E1A1D-57B3-4E99-9897-90A1B0E2C0D8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=PatoRecordatorio-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
english.CreateDesktopShortcut=Create a desktop shortcut
english.AddStartupShortcut=Add shortcut to Startup
english.OpenApp=Open {#MyAppName}
spanish.CreateDesktopShortcut=Crear acceso directo en el escritorio
spanish.AddStartupShortcut=Agregar acceso directo a Inicio
spanish.OpenApp=Abrir {#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopShortcut}"; Flags: unchecked
Name: "startupshortcut"; Description: "{cm:AddStartupShortcut}"; Flags: unchecked

[Files]
Source: "dist\PatoRecordatorio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "a9378435ab8cf241898a33b66964051ffb3c9a0f.gif"; DestDir: "{app}"; Flags: ignoreversion
Source: "duck_transparent.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "locales\*.json"; DestDir: "{app}\locales"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--startup"; Tasks: startupshortcut; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--language={language}"; Description: "{cm:OpenApp}"; Flags: nowait postinstall skipifsilent

[Code]
function AppLanguageCode(): String;
begin
  if ActiveLanguage = 'spanish' then
    Result := 'es'
  else
    Result := 'en';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LanguageConfig: String;
begin
  if CurStep = ssPostInstall then
  begin
    LanguageConfig := '{' + #13#10 +
      '  "language": "' + AppLanguageCode() + '"' + #13#10 +
      '}';
    SaveStringToFile(ExpandConstant('{app}\installer_language.json'), LanguageConfig, False);
  end;
end;

; Local preview installer. No release or code-signing claim.
#ifndef BuildVersion
  #define BuildVersion "0.1.7-dev"
#endif

[Setup]
AppId=Gruterra-Installer-Preview
AppName=Gruterra (test)
AppVersion={#BuildVersion}
AppPublisher=Gruterra
AppPublisherURL=https://github.com/Botaneo-project/gruterra
DefaultDirName={localappdata}\Programs\Gruterra-Test
UsePreviousAppDir=no
AppendDefaultDirName=no
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UninstallFilesDir={app}\_uninstall
UninstallDisplayName=Gruterra (test)
#ifdef SmokeTest
CreateUninstallRegKey=no
#endif
OutputDir={#OutputDirectory}
OutputBaseFilename={#OutputName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
CloseApplications=no
RestartApplications=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
french.DesktopShortcut=Créer un raccourci sur le Bureau
english.DesktopShortcut=Create a desktop shortcut
french.Preparing=Préparation de Python et des composants de Gruterra…
english.Preparing=Preparing Python and Gruterra dependencies…
french.PreparationFailed=La préparation de Gruterra a échoué. Consultez le journal local :
english.PreparationFailed=Gruterra preparation failed. Check the local log:
french.RunDemo=Ouvrir la démonstration de Gruterra
english.RunDemo=Open the Gruterra demo
french.InstallationLocked=Fermez Gruterra pour ce dossier, puis réessayez. Aucun fichier du programme n'a été remplacé. Vérifiez aussi les droits d'accès au dossier si le problème persiste.
english.InstallationLocked=Close Gruterra for this folder, then retry. No program file has been replaced. Also check folder permissions if the problem persists.
french.UpdateRecoveryRequired=Une mise à jour ou récupération est en cours ou reste inachevée. Attendez sa fin, puis utilisez le lanceur Gruterra habituel pour récupérer une interruption avant de réessayer l'installation. Conservez les sauvegardes.
english.UpdateRecoveryRequired=An update or recovery is running or unfinished. Wait for it to finish, then use the normal Gruterra launcher to recover any interruption before retrying setup. Keep the backups.

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; Flags: unchecked

[Files]
#include FileList

[Icons]
#ifdef SmokeTest
Name: "{app}\_test_shortcuts\Gruterra"; Filename: "{app}\Lancer_Gruterra.bat"; WorkingDir: "{app}"
Name: "{app}\_test_shortcuts\Gruterra Demo"; Filename: "{app}\Lancer_Demo.bat"; WorkingDir: "{app}"
#else
Name: "{userprograms}\Gruterra (test)\Gruterra"; Filename: "{app}\Lancer_Gruterra.bat"; WorkingDir: "{app}"
Name: "{userprograms}\Gruterra (test)\Gruterra Demo"; Filename: "{app}\Lancer_Demo.bat"; WorkingDir: "{app}"
Name: "{userprograms}\Gruterra (test)\Desinstaller Gruterra"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Gruterra (test)"; Filename: "{app}\Lancer_Gruterra.bat"; WorkingDir: "{app}"; Tasks: desktopicon
#endif

[Run]
Filename: "{app}\Lancer_Demo.bat"; Description: "{cm:RunDemo}"; Flags: shellexec postinstall skipifsilent unchecked

[Code]
const
  InvalidLockHandle = -1;
var
  InstallationLock: THandle;
  UpdateLock: THandle;

function CreateFileW(Name: String; Access, Sharing, Security, Creation, Attributes, Template: Cardinal): THandle;
  external 'CreateFileW@kernel32.dll stdcall';
function LockFile(Handle: THandle; OffsetLow, OffsetHigh, CountLow, CountHigh: Cardinal): Boolean;
  external 'LockFile@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';

procedure ReleaseInstallationLock;
begin
  if UpdateLock <> InvalidLockHandle then begin
    CloseHandle(UpdateLock);
    UpdateLock := InvalidLockHandle;
  end;
  if InstallationLock <> InvalidLockHandle then begin
    CloseHandle(InstallationLock);
    InstallationLock := InvalidLockHandle;
  end;
end;

function InitializeSetup(): Boolean;
begin
  InstallationLock := InvalidLockHandle;
  UpdateLock := InvalidLockHandle;
  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  LockPath: String;
begin
  Result := '';
  ReleaseInstallationLock;
  LockPath := ExpandConstant('{app}\_config\botaneo.instance.lock');
  if not ForceDirectories(ExtractFileDir(LockPath)) then begin
    Result := CustomMessage('InstallationLocked');
    Exit;
  end;
  InstallationLock := CreateFileW(LockPath, $C0000000, 7, 0, 4, $80, 0);
  if InstallationLock = InvalidLockHandle then begin
    Result := CustomMessage('InstallationLocked');
    Exit;
  end;
  if not LockFile(InstallationLock, 0, 0, 1, 0) then begin
    ReleaseInstallationLock;
    Result := CustomMessage('InstallationLocked');
    Exit;
  end;
  LockPath := ExpandConstant('{app}\_config\gruterra-update.lock');
  UpdateLock := CreateFileW(LockPath, $C0000000, 7, 0, 4, $80, 0);
  if UpdateLock = InvalidLockHandle then begin
    ReleaseInstallationLock;
    Result := CustomMessage('InstallationLocked');
    Exit;
  end;
  if not LockFile(UpdateLock, 0, 0, 1, 0) then begin
    ReleaseInstallationLock;
    Result := CustomMessage('UpdateRecoveryRequired');
    Exit;
  end;
  if FileExists(ExpandConstant('{app}\_security_backups\update-pending.json')) then begin
    ReleaseInstallationLock;
    Result := CustomMessage('UpdateRecoveryRequired');
  end;
end;

procedure DeinitializeSetup();
begin
  ReleaseInstallationLock;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExitCode: Integer;
  LogPath, Command: String;
begin
  if CurStep = ssPostInstall then begin
    WizardForm.StatusLabel.Caption := CustomMessage('Preparing');
    LogPath := ExpandConstant('{app}\_config\installation-windows.log');
    ForceDirectories(ExtractFileDir(LogPath));
    Command := '/D /S /C ""' + ExpandConstant('{app}\Installer_Gruterra.bat') +
      '" --non-interactive > "' + LogPath + '" 2>&1"';
    if not Exec(ExpandConstant('{cmd}'), Command, ExpandConstant('{app}'),
      SW_HIDE, ewWaitUntilTerminated, ExitCode) then
      RaiseException(CustomMessage('PreparationFailed') + #13#10 + LogPath);
    if ExitCode <> 0 then
      RaiseException(CustomMessage('PreparationFailed') + #13#10 + LogPath);
    ReleaseInstallationLock;
  end;
end;

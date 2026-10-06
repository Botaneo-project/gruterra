@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"
set "TARGET_SCRIPT=Lancer_Gruterra.py"

echo ============================================
echo Gruterra - lancement
echo ============================================
echo.

call :ensure_environment
if errorlevel 1 goto :fail_environment

echo Ouverture de Gruterra...
"%VENV_PY%" "%TARGET_SCRIPT%"
if errorlevel 1 (
    echo.
    echo ERREUR - Gruterra ne s'est pas lance correctement.
    echo Copiez les lignes ci-dessus si vous demandez de l'aide.
    echo.
    pause
    exit /b 1
)

exit /b 0

:ensure_environment
if exist "%VENV_PY%" exit /b 0

echo Environnement local introuvable : %VENV_PY%
echo Gruterra va lancer Installer_Gruterra.bat, puis reessayer automatiquement.
echo.
if not exist "Installer_Gruterra.bat" (
    echo ERREUR - Installer_Gruterra.bat est introuvable dans ce dossier.
    echo Verifiez que l'archive Gruterra a ete extraite entierement.
    exit /b 1
)
call "Installer_Gruterra.bat"
if errorlevel 1 exit /b 1
if exist "%VENV_PY%" exit /b 0

echo ERREUR - l'installation s'est terminee mais %VENV_PY% reste introuvable.
echo Vous etes peut-etre dans une autre copie du dossier Gruterra.
exit /b 1

:fail_environment
echo.
echo Impossible de preparer l'environnement Gruterra.
echo Copiez les lignes ci-dessus si vous demandez de l'aide.
echo.
pause
exit /b 1

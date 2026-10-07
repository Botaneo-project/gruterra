@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"
set "TARGET_SCRIPT=Lancer_Demo.py"

echo ============================================
echo Gruterra - lancement demo
echo ============================================
echo.

call :ensure_environment
if errorlevel 1 goto :fail_environment

echo Ouverture de Gruterra en mode demo... une fenetre peut mettre quelques secondes a apparaitre.
"%VENV_PY%" "%TARGET_SCRIPT%"
if errorlevel 1 (
    echo.
    echo ERREUR - Gruterra demo ne s'est pas lance correctement.
    echo Copiez toute cette fenetre si vous demandez de l'aide.
    echo.
    pause
    exit /b 1
)

exit /b 0

:ensure_environment
if exist "%VENV_PY%" exit /b 0

echo Preparation locale Gruterra introuvable : %VENV_PY%
echo Gruterra va lancer l'installateur, puis reessayer automatiquement.
echo.
if not exist "Installer_Gruterra.bat" (
    echo ERREUR - Installer_Gruterra.bat est introuvable dans ce dossier.
    echo Verifiez que l'archive Gruterra a ete extraite entierement.
    exit /b 1
)
call "Installer_Gruterra.bat"
if errorlevel 1 exit /b 1
if exist "%VENV_PY%" exit /b 0

echo ERREUR - l'installation s'est terminee, mais la preparation locale reste introuvable.
echo Verifiez que vous lancez le fichier depuis le dossier Gruterra extrait.
exit /b 1

:fail_environment
echo.
echo Impossible de preparer Gruterra sur ce PC.
echo Copiez toute cette fenetre si vous demandez de l'aide.
echo.
pause
exit /b 1

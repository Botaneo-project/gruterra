@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

echo ============================================
echo Gruterra - lancement demo
echo ============================================
echo.

if not exist "%VENV_PY%" (
    echo Environnement local introuvable : %VENV_PY%
    echo.
    echo Lancez d'abord Installer_Gruterra.bat, puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)

echo Ouverture de Gruterra en mode demo...
"%VENV_PY%" Lancer_Demo.py
if errorlevel 1 (
    echo.
    echo ERREUR - Gruterra demo ne s'est pas lance correctement.
    echo Copiez les lignes ci-dessus si vous demandez de l'aide.
    echo.
    pause
    exit /b 1
)

exit /b 0

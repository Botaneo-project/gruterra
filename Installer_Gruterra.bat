@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "MIN_PYTHON=3.10"
set "PYTHON_CMD="
set "VENV_PY=.venv\Scripts\python.exe"
set "PYTHON_VERSION=3.12.10"
set "PYTHON_INSTALLER=%TEMP%\gruterra-python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_EXPECTED_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo ============================================
echo Gruterra - installation Windows
echo ============================================
echo.
echo Objectif : preparer ce PC pour lancer Gruterra et verifier que la demo peut demarrer.
echo.

echo [1/6] Recherche de Python sur ce PC
call :detect_python
if errorlevel 1 (
    call :install_python
    if errorlevel 1 goto :python_missing
    call :detect_python
    if errorlevel 1 goto :python_missing
)

echo Python trouve : %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print('Version Python : ' + sys.version.split()[0])"
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo.
    echo ERREUR - Python %MIN_PYTHON% ou plus recent est necessaire.
    echo L'installation automatique peut installer Python %PYTHON_VERSION% si Python est absent,
    echo mais elle ne remplace pas une ancienne version deja detectee.
    echo.
    goto :fail
)

echo.
echo [2/6] Preparation du dossier local de Gruterra
if not exist requirements.txt (
    echo ERREUR - requirements.txt est introuvable.
    echo Lancez Installer_Gruterra.bat depuis la racine du dossier Gruterra.
    echo.
    goto :fail
)

if not exist "%VENV_PY%" (
    echo Premiere preparation locale de Gruterra... cela peut prendre un moment.
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERREUR - impossible de preparer le dossier local de Gruterra.
        echo Relancez l'installation. Si le probleme revient, copiez toute cette fenetre pour demander de l'aide.
        echo.
        goto :fail
    )
) else (
    echo Dossier local Gruterra deja pret.
)

echo.
echo [3/6] Verification du gestionnaire de modules Python
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo Gestionnaire de modules absent, tentative de reparation automatique...
    "%VENV_PY%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo.
        echo ERREUR - impossible de reparer le gestionnaire de modules Python.
        echo Installez ou reparez Python, puis relancez Installer_Gruterra.bat.
        echo.
        goto :fail
    )
)

echo Gestionnaire de modules OK.

echo.
echo [4/6] Installation des composants necessaires a Gruterra
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERREUR - l'installation des composants Gruterra a echoue.
    echo Copiez toute cette fenetre si vous demandez de l'aide.
    echo.
    goto :fail
)

echo.
echo [5/6] Verification finale de Gruterra
"%VENV_PY%" -c "import tkinter, requests, bleak; print('Imports essentiels OK : tkinter, requests, bleak')"
if errorlevel 1 (
    echo.
    echo ERREUR - installation incomplete : un composant indispensable manque.
    echo Gruterra n'a pas pu charger tous les composants necessaires.
    echo.
    goto :fail
)

"%VENV_PY%" -c "from pathlib import Path; assert Path('Lancer_Demo.py').exists(); assert Path('_app').exists(); print('Fichiers Gruterra OK')"
if errorlevel 1 (
    echo.
    echo ERREUR - Gruterra semble incomplet.
    echo Verifiez que l'archive ZIP a bien ete extraite entierement avant de lancer Gruterra.
    echo.
    goto :fail
)

echo.
echo [6/6] Gruterra est pret sur ce PC.
echo.
echo Pour tester sans materiel :
echo   double-cliquez sur Lancer_Demo.bat
echo.
echo Pour commencer une vraie utilisation locale :
echo   double-cliquez sur Lancer_Gruterra.bat
echo.
pause
exit /b 0

:detect_python
where py >nul 2>nul
if not errorlevel 1 (
    py -c "import sys; raise SystemExit(0)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py"
        exit /b 0
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
        exit /b 0
    )
)
if exist "%PYTHON_EXPECTED_EXE%" (
    "%PYTHON_EXPECTED_EXE%" -c "import sys; raise SystemExit(0)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=%PYTHON_EXPECTED_EXE%"
        exit /b 0
    )
)
exit /b 1

:install_python
echo Python est introuvable. Gruterra va tenter de l'installer automatiquement.
echo Version cible : Python %PYTHON_VERSION% pour Windows 64 bits.
echo.
echo Telechargement de Python depuis python.org...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_DOWNLOAD_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo ERREUR - impossible de telecharger Python automatiquement.
    exit /b 1
)
echo Installation de Python en cours...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1 Include_tcltk=1 Include_test=0 SimpleInstall=1
if errorlevel 1 (
    echo.
    echo ERREUR - l'installation automatique de Python a echoue.
    exit /b 1
)
if exist "%PYTHON_EXPECTED_EXE%" set "PYTHON_CMD=%PYTHON_EXPECTED_EXE%"
echo Python installe. Gruterra reprend la preparation...
echo.
exit /b 0

:python_missing
echo Python est introuvable sur ce PC.
echo.
echo L'installation automatique de Python a echoue ou a ete bloquee.
echo Installez Python manuellement depuis :
echo https://www.python.org/downloads/windows/
echo.
echo Pendant l'installation, cochez l'option qui ajoute Python au PATH si elle est proposee.
echo Gardez aussi le lanceur Python Windows active si possible.
echo.
goto :fail

:fail
echo Installation arretee avant la fin.
echo La fenetre reste ouverte : copiez son contenu si vous demandez de l'aide.
echo.
pause
exit /b 1

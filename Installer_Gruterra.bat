@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "MIN_PYTHON=3.10"
set "PYTHON_CMD="
set "VENV_PY=.venv\Scripts\python.exe"

echo ============================================
echo Gruterra - installation Windows
echo ============================================
echo.
echo Objectif : installer les dependances puis verifier que la demo peut demarrer.
echo.

echo [1/5] Verification de Python
call :detect_python
if errorlevel 1 goto :python_missing

echo Python detecte : %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print('Version Python : ' + sys.version.split()[0])"
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo.
    echo ERREUR - Python %MIN_PYTHON% ou plus recent est necessaire.
    echo Installez une version recente depuis :
    echo https://www.python.org/downloads/windows/
    echo.
    goto :fail
)

echo.
echo [2/5] Verification de l'environnement local
if not exist requirements.txt (
    echo ERREUR - requirements.txt est introuvable.
    echo Lancez Installer_Gruterra.bat depuis la racine du dossier Gruterra.
    echo.
    goto :fail
)

if not exist "%VENV_PY%" (
    echo Creation de l'environnement local .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERREUR - impossible de creer l'environnement Python local .venv.
        echo Verifiez que Python est installe avec le module venv.
        echo.
        goto :fail
    )
) else (
    echo Environnement .venv deja present.
)

echo.
echo [3/5] Verification de pip
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo pip indisponible dans .venv, tentative d'activation avec ensurepip...
    "%VENV_PY%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo.
        echo ERREUR - pip est indisponible et ensurepip a echoue.
        echo Installez ou reparez Python, puis relancez Installer_Gruterra.bat.
        echo.
        goto :fail
    )
)

echo Mise a jour de pip, non bloquante...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo AVERTISSEMENT - la mise a jour de pip a echoue.
    echo L'installation continue avec la version de pip deja disponible.
)

echo.
echo [4/5] Installation des dependances Gruterra
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERREUR - l'installation des dependances Gruterra a echoue.
    echo Copiez les lignes d'erreur ci-dessus si vous demandez de l'aide.
    echo.
    goto :fail
)

echo.
echo [5/5] Verification de Gruterra
"%VENV_PY%" -c "import tkinter, requests, bleak; print('Imports essentiels OK : tkinter, requests, bleak')"
if errorlevel 1 (
    echo.
    echo ERREUR - installation incomplete : une dependance essentielle est absente.
    echo Dependances attendues : tkinter, requests, bleak.
    echo.
    goto :fail
)

"%VENV_PY%" -c "from pathlib import Path; assert Path('Lancer_Demo.py').exists(); assert Path('_app').exists(); print('Fichiers Gruterra OK')"
if errorlevel 1 (
    echo.
    echo ERREUR - verification Gruterra incomplete.
    echo Verifiez que le dossier a ete extrait entierement.
    echo.
    goto :fail
)

echo.
echo Installation terminee avec succes.
echo.
echo Pour tester sans materiel :
echo   double-cliquez sur Lancer_Demo.py
echo.
echo Pour commencer une vraie utilisation locale :
echo   double-cliquez sur Lancer_Gruterra.py
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
exit /b 1

:python_missing
echo Python est introuvable sur ce PC.
echo.
echo Installez Python depuis :
echo https://www.python.org/downloads/windows/
echo.
echo Pendant l'installation, cochez l'option qui ajoute Python au PATH si elle est proposee.
echo Gardez aussi le lanceur Python Windows active si possible.
echo.
goto :fail

:fail
echo Installation interrompue ou incomplete.
echo La fenetre reste ouverte pour permettre de copier le message.
echo.
pause
exit /b 1

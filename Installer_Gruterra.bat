@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo Gruterra - installation des dependances
echo ============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo Python est introuvable sur ce PC.
        echo.
        echo Installez Python depuis :
        echo https://www.python.org/downloads/windows/
        echo.
        echo Pendant l'installation, gardez le lanceur py active.
        echo Tkinter doit etre installe avec Python.
        echo.
        pause
        exit /b 1
    )
)

echo Python detecte : %PYTHON_CMD%
echo.

if not exist requirements.txt (
    echo requirements.txt est introuvable.
    echo Lancez ce fichier depuis la racine du dossier Gruterra.
    echo.
    pause
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    echo Creation de l'environnement local .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo Impossible de creer l'environnement Python.
        pause
        exit /b 1
    )
) else (
    echo Environnement .venv deja present.
)

echo.
echo Mise a jour de pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo La mise a jour de pip a echoue.
    pause
    exit /b 1
)

echo.
echo Installation des dependances Gruterra...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo L'installation des dependances a echoue.
    pause
    exit /b 1
)

echo.
echo Installation terminee.
echo.
echo Pour tester sans materiel :
echo   double-cliquez sur Lancer_Demo.py
echo.
echo Pour commencer une vraie utilisation locale :
echo   double-cliquez sur Lancer_Gruterra.py
echo.
pause

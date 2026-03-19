@echo off
echo ================================================
echo   ToDoT Build Script
echo ================================================
echo.

REM Create venv if not exists
if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Using existing venv
)

echo [2/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/5] Generating icon...
python create_icon.py

echo [4/5] Building with PyInstaller...
pyinstaller --noconfirm --onefile --windowed ^
    --name "ToDoT" ^
    --icon "icon.ico" ^
    --add-data "src;src" ^
    --add-data "icon.png;." ^
    src\main.py

echo [5/5] Copying assets...
if not exist "dist\output" mkdir "dist\output"
if not exist "dist\tmp" mkdir "dist\tmp"
copy /Y icon.png dist\icon.png >nul 2>&1

echo.
echo ================================================
echo   Build complete!
echo   Executable: dist\ToDoT.exe
echo ================================================
pause

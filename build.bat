@echo off
chcp 65001 >nul
echo ================================================
echo   ToDoT 빌드 스크립트
echo ================================================
echo.

REM 가상환경 확인
if not exist "venv" (
    echo [1/5] 가상환경 생성 중...
    python -m venv venv
) else (
    echo [1/5] 기존 가상환경 사용
)

echo [2/5] 가상환경 활성화 및 의존성 설치...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/5] 아이콘 생성...
python create_icon.py

echo [4/5] PyInstaller로 빌드 중...
pyinstaller --noconfirm --onefile --windowed ^
    --name "ToDoT" ^
    --icon "icon.ico" ^
    --add-data "src;src" ^
    --add-data "icon.png;." ^
    src\main.py

echo [5/5] 결과물 정리...
if not exist "dist\output" mkdir "dist\output"
if not exist "dist\tmp" mkdir "dist\tmp"
copy /Y icon.png dist\icon.png >nul 2>&1

echo.
echo ================================================
echo   빌드 완료!
echo   실행 파일: dist\ToDoT.exe
echo ================================================
pause

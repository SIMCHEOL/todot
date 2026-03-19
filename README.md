# ToDoT

> 이미지와 동영상을 **도트(픽셀아트)**, **ASCII**, **한글**, **유니코드** 아트로 변환하는 Windows 데스크톱 프로그램

<br>

## 소개

**ToDoT**은 이미지와 동영상 파일을 다양한 아트 스타일로 변환해주는 GUI + CLI 프로그램입니다.  
파라미터를 조절하면 실시간으로 결과를 미리 확인할 수 있고, 직접 그림을 그려서 변환하는 것도 가능합니다.

<br>

## 주요 기능

**변환 모드**

| 모드 | 설명 |
|------|------|
| 도트(픽셀아트) | K-means 색상 양자화 기반 레트로 픽셀아트 |
| ASCII 아트 | ASCII 문자로 구성된 아트 (컬러 / 흑백) |
| 한글 문자 | 한글 자모·음절로 구성된 아트 (컬러 / 흑백) |
| 유니코드 블록 | 유니코드 블록 문자 아트 (컬러 / 흑백) |

**핵심 기능**

- 실시간 미리보기 - 파라미터 변경 시 즉시 결과 확인
- 동영상 5초 미리보기 - 전체 변환 전 빠른 프리뷰
- 그림판 모드 - 직접 그린 후 변환
- 결과물 브라우저 - 출력 폴더를 썸네일/리스트로 탐색, 드래그 앤 드롭으로 외부 복사
- 진행률 표시 - 경과 시간, 예상 남은 시간, Windows 작업 표시줄 진행률
- 6가지 테마 - Catppuccin Mocha/Latte, Dracula, Nord, Solarized Dark, Gruvbox Dark
- CLI 지원 - 커맨드라인으로 일괄 변환 가능

**지원 형식**

- **이미지**: PNG, JPG, JPEG, BMP, GIF, TIFF, TIF, WEBP, ICO
- **동영상**: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V

<br>

## 시스템 요구사항

- Windows 7 이상
- Python 3.8 이상 (소스 실행 시)

<br>

## 시작하기

### exe 파일 실행

[Releases](../../releases) 페이지에서 `ToDoT.exe`를 다운로드하여 실행합니다.  
`output`과 `tmp` 폴더가 자동으로 생성됩니다.

### 소스에서 실행

```bash
git clone https://github.com/<username>/todot.git
cd todot

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python src/main.py
```

<br>

## 빌드

### 자동 빌드

```bash
build.bat
```

더블클릭하면 가상환경 생성, 의존성 설치, 아이콘 생성, PyInstaller 빌드가 순서대로 진행됩니다.

### 수동 빌드

```bash
venv\Scripts\activate
python create_icon.py
pyinstaller --noconfirm --onefile --windowed ^
    --name "ToDoT" --icon "icon.ico" ^
    --add-data "src;src" --add-data "icon.png;." ^
    src\main.py
```

결과물: `dist\ToDoT.exe`

<br>

## 사용법

### GUI

| 동작 | 방법 |
|------|------|
| 파일 열기 | `Ctrl+O`, 도구 모음 클릭, 또는 드래그 앤 드롭 |
| 새 그림 | `Ctrl+N`으로 캔버스 생성 후 자유롭게 그리기 |
| 변환 | 하단 패널에서 모드·옵션 조절 후 **⚡ 변환하기** 클릭 |
| 저장 | `Ctrl+S` 또는 **💾 저장** 클릭 |
| 설정 | `Ctrl+,`로 출력 형식, 테마, 기본값 변경 |

파라미터를 변경하면 **실시간 미리보기**가 자동으로 업데이트됩니다.

### CLI

```bash
# 도트 변환
python src/cli.py input.png -o output.png --mode pixel --pixel-size 8 --colors 16

# ASCII 아트
python src/cli.py photo.jpg --mode ascii --pixel-size 12

# 한글 아트
python src/cli.py image.png --mode hangul -o result.png

# 동영상 변환
python src/cli.py video.mp4 -o result.mp4 --mode unicode --pixel-size 10

# 전체 옵션 확인
python src/cli.py --help
```

<details>
<summary>CLI 옵션 전체 목록</summary>

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `input` | 입력 파일 경로 | (필수) |
| `-o, --output` | 출력 파일 경로 | 자동 생성 |
| `-m, --mode` | pixel, ascii, ascii_bw, hangul, hangul_bw, unicode, unicode_bw | pixel |
| `-p, --pixel-size` | 픽셀/문자 블록 크기 | 8 |
| `-c, --colors` | 색상 수 (도트 모드) | 16 |
| `--grid` | 격자선 표시 | off |
| `--outline` | 윤곽선 강조 | off |
| `--output-dir` | 출력 폴더 | 입력 파일 위치 |

</details>

<br>

## 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+N` | 새 그림 |
| `Ctrl+O` | 파일 열기 |
| `Ctrl+S` | 결과 저장 |
| `Ctrl+Shift+S` | 다른 이름으로 저장 |
| `Ctrl+Z` | 실행 취소 |
| `Ctrl+Y` | 다시 실행 |
| `Ctrl+,` | 설정 |

<br>

## 프로젝트 구조

```
todot/
├── src/
│   ├── main.py              # GUI 엔트리포인트
│   ├── cli.py               # CLI 엔트리포인트
│   ├── main_window.py       # 메인 윈도우
│   ├── converter.py         # 변환 엔진 (도트/ASCII/한글/유니코드)
│   ├── canvas_widget.py     # 그림판 위젯
│   ├── preview_widget.py    # 이미지/동영상 미리보기
│   ├── output_browser.py    # 결과물 폴더 브라우저
│   ├── history_widget.py    # 작업 히스토리
│   ├── settings_dialog.py   # 설정 다이얼로그
│   ├── config_manager.py    # 설정 관리
│   ├── history_manager.py   # 히스토리 관리
│   └── styles.py            # 6가지 테마 스타일시트
├── create_icon.py            # 아이콘 생성 스크립트
├── build.bat                 # 원클릭 빌드 스크립트
├── requirements.txt
├── icon.ico                  # 프로그램 아이콘
├── icon.png
└── project.md                # 프로젝트 기획 문서
```

**런타임 생성 파일** (`.gitignore` 대상)

```
output/       ← 변환 결과물
tmp/          ← 임시 파일
config.json   ← 사용자 설정
history.json  ← 작업 기록
```

<br>

## 기술 스택

| 분류 | 기술 |
|------|------|
| GUI | PyQt5, QtWinExtras |
| 이미지 처리 | OpenCV, NumPy |
| 아이콘 생성 | Pillow |
| 빌드 | PyInstaller |

<br>

## 라이선스

MIT License

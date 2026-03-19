# ToDoT

> 이미지와 동영상을 **픽셀아트**, **ASCII**, **한글**, **유니코드**, **아트 효과**로 변환하는 Windows 데스크톱 프로그램

<br>

## 소개

**ToDoT**은 이미지와 동영상을 18종의 아트 스타일로 변환하는 GUI + CLI 프로그램입니다.  
6종의 픽셀화 알고리즘, 4종의 문자 아트, 6종의 아트 효과, 그리고 4분할 복합 모드를 지원합니다.

<br>

## 변환 모드

### 픽셀 변환 (6종)

| 모드 | 설명 |
|------|------|
| K-means 양자화 | K-means 클러스터링 기반 색상 양자화 |
| 디더링 (Floyd-Steinberg) | 오류 확산 디더링 |
| 팔레트 매핑 | Game Boy, PICO-8, CGA 등 사전 정의 팔레트 매핑 |
| Nearest Neighbor | 순수 최근접 이웃 다운/업스케일 |
| Edge-preserving | 양방향 필터 + 엣지 오버레이 |
| 슈퍼픽셀 | Mean-shift 기반 영역 분할 후 픽셀화 |

### ASCII / 문자 변환 (4종)

| 모드 | 설명 |
|------|------|
| ASCII 아트 | 컬러 / 흑백 |
| 한글 문자 | 자모·음절 아트 (컬러 / 흑백) |
| 유니코드 블록 | 블록 문자 아트 (컬러 / 흑백) |

### 아트 효과 (6종)

| 모드 | 설명 |
|------|------|
| 하프톤 | 신문 인쇄 스타일 컬러 도트 |
| 만화 스타일 | 색상 단순화 + 엣지 라인 |
| 보로노이 아트 | 보로노이 셀 분할, 셀 평균색 |
| 로우 폴리 | Delaunay 삼각분할, 삼각형 평균색 |
| 점묘화 | 밝기 기반 랜덤 도트 배치 |
| 글리치 아트 | 채널 시프트 + 블록 변위 + 스캔라인 |

### 복합 모드

원본 + 3가지 변환을 **2x2 그리드**로 합성. 각 패널 모드를 자유롭게 선택 가능.

<br>

## 주요 기능

- **실시간 미리보기** - 파라미터 변경 시 즉시 결과 확인
- **동영상 5초 미리보기** - 전체 변환 전 빠른 프리뷰
- **그림판 모드** - 직접 그린 후 변환
- **결과물 브라우저** - 썸네일/리스트 보기, 드래그 앤 드롭 외부 복사
- **진행률 표시** - 경과 시간, 예상 남은 시간, Windows 작업 표시줄
- **6가지 테마** - Catppuccin Mocha/Latte, Dracula, Nord, Solarized Dark, Gruvbox Dark
- **CLI** - 커맨드라인 일괄 변환

### 지원 형식

- **이미지**: PNG, JPG, JPEG, BMP, GIF, TIFF, TIF, WEBP, ICO
- **동영상**: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V

<br>

## 시작하기

### exe 실행

[Releases](../../releases) 페이지에서 `ToDoT.exe`를 다운로드하여 실행합니다.

### 소스에서 실행

```bash
git clone https://github.com/SIMCHEOL/todot.git
cd todot

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python src/main.py
```

<br>

## 빌드

```bash
build.bat
```

<br>

## CLI 사용법

```bash
# K-means 픽셀아트
python src/cli.py input.png --mode pixel --pixel-size 8 --colors 16

# 디더링
python src/cli.py input.png --mode pixel_dither --pixel-size 10

# 팔레트 매핑 (Game Boy)
python src/cli.py input.png --mode pixel_palette --palette "Game Boy"

# 만화 스타일
python src/cli.py photo.jpg --mode cartoon --pixel-size 8

# 보로노이 아트
python src/cli.py input.png --mode voronoi --pixel-size 6

# 로우 폴리
python src/cli.py input.png --mode lowpoly --pixel-size 10

# 글리치 아트
python src/cli.py input.png --mode glitch --pixel-size 12

# 복합 모드
python src/cli.py input.png --mode composite --composite-modes pixel halftone lowpoly

# 동영상 변환
python src/cli.py video.mp4 -o result.mp4 --mode cartoon

# 전체 옵션
python src/cli.py --help
```

<details>
<summary>CLI 옵션 전체 목록</summary>

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `input` | 입력 파일 경로 | (필수) |
| `-o, --output` | 출력 파일 경로 | 자동 생성 |
| `-m, --mode` | 변환 모드 | pixel |
| `-p, --pixel-size` | 블록 크기 | 8 |
| `-c, --colors` | 색상 수 | 16 |
| `--grid` | 격자선 | off |
| `--outline` | 윤곽선 | off |
| `--output-dir` | 출력 폴더 | 입력 위치 |
| `--palette` | 팔레트 이름 | PICO-8 |
| `--composite-modes` | 복합 3개 모드 | pixel ascii hangul |

**변환 모드:**  
`pixel`, `pixel_dither`, `pixel_palette`, `pixel_nearest`, `pixel_edge`, `pixel_superpixel`,  
`ascii`, `ascii_bw`, `hangul`, `hangul_bw`, `unicode`, `unicode_bw`,  
`halftone`, `cartoon`, `voronoi`, `lowpoly`, `stipple`, `glitch`, `composite`

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
├── src/                      # 소스 코드 (12개 모듈)
│   ├── main.py               # GUI 엔트리포인트
│   ├── cli.py                # CLI 엔트리포인트
│   ├── converter.py          # 변환 엔진 (18종 + 복합)
│   ├── main_window.py        # 메인 윈도우
│   └── ...                   # 위젯, 설정, 스타일
├── build.bat                 # 빌드 스크립트
├── requirements.txt
├── project.md                # 프로젝트 설계 문서
└── LICENSE
```

<br>

## 기술 스택

| 분류 | 기술 |
|------|------|
| GUI | PyQt5, QtWinExtras |
| 이미지 처리 | OpenCV (K-means, bilateral, Canny, Subdiv2D, meanShift) |
| 수치 연산 | NumPy |
| 아이콘 | Pillow |
| 빌드 | PyInstaller |

<br>

## 라이선스

MIT License

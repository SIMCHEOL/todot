import cv2
import numpy as np
import os
from PyQt5.QtCore import QThread, pyqtSignal


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".ico"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}

ASCII_CHARS_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
HANGUL_CHARS = " ·ㅡㅣㄱㄴㅅㅇㅈㅂㅁㄷㄹㅎㅊㅋㅌㅍ가나다마바사아자타파하묘봄활흑"
UNICODE_CHARS = " ·∙░▒▓▉█▊▋▌▍▐■"

CONVERT_MODES = [
    ("pixel", "도트 변환"),
    ("ascii", "ASCII 아트 (컬러)"),
    ("ascii_bw", "ASCII 아트 (흑백)"),
    ("hangul", "한글 문자 (컬러)"),
    ("hangul_bw", "한글 문자 (흑백)"),
    ("unicode", "유니코드 블록 (컬러)"),
    ("unicode_bw", "유니코드 블록 (흑백)"),
]

MODE_KEYS = [m[0] for m in CONVERT_MODES]
MODE_LABELS = [m[1] for m in CONVERT_MODES]


def is_image(path):
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def is_video(path):
    return os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS


def get_supported_filter():
    img = " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))
    vid = " ".join(f"*{ext}" for ext in sorted(VIDEO_EXTENSIONS))
    return (
        f"모든 지원 파일 ({img} {vid});;"
        f"이미지 파일 ({img});;"
        f"동영상 파일 ({vid});;"
        "모든 파일 (*.*)"
    )


def pixelize_image(image, pixel_size=8, num_colors=16, grid=False, outline=False):
    if image is None:
        return None

    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)

    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)

    if outline:
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if len(small.shape) == 3 else small
        edges = cv2.Canny(gray, 100, 200)
        edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR) if len(small.shape) == 3 else edges
        small = cv2.subtract(small, edges_color // 2)

    pixels = small.reshape(-1, 3).astype(np.float32)
    actual_colors = min(num_colors, len(np.unique(pixels, axis=0)))
    if actual_colors < 2:
        actual_colors = 2

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    try:
        _, labels, centers = cv2.kmeans(
            pixels, actual_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS
        )
        quantized = centers[labels.flatten()].reshape(small.shape).astype(np.uint8)
    except cv2.error:
        quantized = small

    result = cv2.resize(quantized, (w, h), interpolation=cv2.INTER_NEAREST)

    if grid:
        grid_color = (40, 40, 40)
        for x in range(0, w, pixel_size):
            cv2.line(result, (x, 0), (x, h - 1), grid_color, 1)
        for y in range(0, h, pixel_size):
            cv2.line(result, (0, y), (w - 1, y), grid_color, 1)

    return result


def _char_art_image(image, cols, char_set, color_mode, char_w, char_h):
    """Shared logic for ASCII / Hangul / Unicode art rendering."""
    if image is None:
        return None

    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    cell_w = max(1, w / cols)
    cell_h = cell_w * 2.0
    rows = int(h / cell_h)
    if rows < 1:
        rows = 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    small_gray = cv2.resize(gray, (cols, rows), interpolation=cv2.INTER_AREA)

    small_color = None
    if color_mode and len(image.shape) == 3:
        small_color = cv2.resize(image, (cols, rows), interpolation=cv2.INTER_AREA)

    font_face = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1

    out_w = cols * char_w
    out_h = rows * char_h
    result = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            brightness = small_gray[r, c]
            idx = int(brightness / 256.0 * len(char_set))
            idx = min(idx, len(char_set) - 1)
            char = char_set[idx]

            x = c * char_w
            y = r * char_h + char_h - 4

            if small_color is not None:
                bgr = small_color[r, c]
                color = (int(bgr[0]), int(bgr[1]), int(bgr[2]))
            else:
                color = (0, 255, 0)

            cv2.putText(result, char, (x, y), font_face, font_scale, color, thickness, cv2.LINE_AA)

    return result


def ascii_art_image(image, cols=120, char_set=None, color_mode=False):
    if char_set is None:
        char_set = ASCII_CHARS_DETAILED
    return _char_art_image(image, cols, char_set, color_mode, char_w=10, char_h=18)


def hangul_art_image(image, cols=80, color_mode=True):
    return _char_art_image(image, cols, HANGUL_CHARS, color_mode, char_w=14, char_h=20)


def unicode_art_image(image, cols=100, color_mode=True):
    return _char_art_image(image, cols, UNICODE_CHARS, color_mode, char_w=12, char_h=18)


def convert_single_frame(frame, mode, pixel_size, num_colors, grid, outline):
    """Convert a single frame using the specified mode. Used by all threads."""
    if mode == "ascii":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return ascii_art_image(frame, cols=cols, color_mode=True)
    elif mode == "ascii_bw":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return ascii_art_image(frame, cols=cols, color_mode=False)
    elif mode == "hangul":
        cols = max(20, frame.shape[1] // (pixel_size * 2))
        return hangul_art_image(frame, cols=cols, color_mode=True)
    elif mode == "hangul_bw":
        cols = max(20, frame.shape[1] // (pixel_size * 2))
        return hangul_art_image(frame, cols=cols, color_mode=False)
    elif mode == "unicode":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return unicode_art_image(frame, cols=cols, color_mode=True)
    elif mode == "unicode_bw":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return unicode_art_image(frame, cols=cols, color_mode=False)
    else:
        return pixelize_image(frame, pixel_size, num_colors, grid, outline)


class ImageConvertThread(QThread):
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, image, pixel_size, num_colors, grid, outline, mode="pixel"):
        super().__init__()
        self.image = image
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode

    def run(self):
        try:
            result = convert_single_frame(
                self.image, self.mode,
                self.pixel_size, self.num_colors, self.grid, self.outline
            )
            if result is not None:
                self.finished.emit(result)
            else:
                self.error.emit("변환에 실패했습니다.")
        except Exception as e:
            self.error.emit(str(e))


class VideoConvertThread(QThread):
    progress = pyqtSignal(int, float, float)  # percent, elapsed_sec, remaining_sec
    frame_converted = pyqtSignal(np.ndarray)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, pixel_size, num_colors, grid, outline, mode="pixel"):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        import time as _time
        try:
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                self.error.emit("동영상을 열 수 없습니다.")
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            dummy = np.zeros((h, w, 3), dtype=np.uint8)
            test_result = convert_single_frame(
                dummy, self.mode, self.pixel_size, self.num_colors, self.grid, self.outline
            )
            if test_result is not None:
                out_h, out_w = test_result.shape[:2]
            else:
                out_w, out_h = w, h

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            ext = os.path.splitext(self.output_path)[1].lower()
            if ext == ".avi":
                fourcc = cv2.VideoWriter_fourcc(*"XVID")

            writer = cv2.VideoWriter(self.output_path, fourcc, fps, (out_w, out_h))
            if not writer.isOpened():
                cap.release()
                self.error.emit("동영상 출력 초기화 실패. 코덱을 확인해주세요.")
                return

            frame_idx = 0
            preview_interval = max(1, total // 60)
            start_time = _time.time()

            while True:
                if self._cancelled:
                    break
                ret, frame = cap.read()
                if not ret:
                    break

                converted = convert_single_frame(
                    frame, self.mode, self.pixel_size, self.num_colors, self.grid, self.outline
                )

                if converted is not None:
                    writer.write(converted)
                    if frame_idx % preview_interval == 0:
                        self.frame_converted.emit(converted.copy())

                frame_idx += 1
                if total > 0:
                    pct = int(frame_idx / total * 100)
                    elapsed = _time.time() - start_time
                    remaining = (elapsed / max(frame_idx, 1)) * (total - frame_idx)
                    self.progress.emit(pct, elapsed, remaining)

            cap.release()
            writer.release()

            if self._cancelled:
                if os.path.exists(self.output_path):
                    os.remove(self.output_path)
                self.error.emit("변환이 취소되었습니다.")
            else:
                self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class VideoPreviewThread(QThread):
    """Convert only ~5 seconds of video for quick preview."""
    finished = pyqtSignal(list, float)  # frames, fps
    error = pyqtSignal(str)

    def __init__(self, input_path, pixel_size, num_colors, grid, outline, mode="pixel", duration=5.0):
        super().__init__()
        self.input_path = input_path
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode
        self.duration = duration
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                self.error.emit("동영상을 열 수 없습니다.")
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            max_frames = int(fps * self.duration)

            frames = []
            for _ in range(max_frames):
                if self._cancelled:
                    break
                ret, frame = cap.read()
                if not ret:
                    break

                converted = convert_single_frame(
                    frame, self.mode, self.pixel_size, self.num_colors, self.grid, self.outline
                )
                if converted is not None:
                    frames.append(converted)

            cap.release()

            if not self._cancelled and frames:
                self.finished.emit(frames, fps)
            elif not frames:
                self.error.emit("미리보기 프레임을 생성할 수 없습니다.")
        except Exception as e:
            self.error.emit(str(e))

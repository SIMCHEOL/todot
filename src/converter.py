import cv2
import numpy as np
import os
from PyQt5.QtCore import QThread, pyqtSignal


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".ico"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}

ASCII_CHARS_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
HANGUL_CHARS = " ·ㅡㅣㄱㄴㅅㅇㅈㅂㅁㄷㄹㅎㅊㅋㅌㅍ가나다마바사아자타파하묘봄활흑"
UNICODE_CHARS = " ·∙░▒▓▉█▊▋▌▍▐■"

# ─── Predefined palettes (RGB, converted to BGR at load) ───

_PALETTE_RGB = {
    "Game Boy": [
        (15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15),
    ],
    "PICO-8": [
        (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
        (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
        (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
        (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
    ],
    "CGA": [
        (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
        (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
        (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
        (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255),
    ],
    "Commodore 64": [
        (0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238),
        (204, 68, 204), (0, 204, 85), (0, 0, 170), (238, 238, 119),
        (221, 136, 85), (102, 68, 0), (255, 119, 119), (51, 51, 51),
        (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187),
    ],
    "Grayscale 16": [
        (i, i, i) for i in range(0, 256, 17)
    ],
    "Sepia": [
        (44, 31, 22), (66, 47, 34), (88, 64, 46), (110, 80, 58),
        (132, 96, 70), (155, 113, 82), (177, 129, 94), (199, 145, 106),
        (210, 161, 118), (220, 177, 130), (230, 193, 142), (239, 209, 154),
        (245, 222, 168), (248, 233, 182), (251, 243, 196), (255, 252, 212),
    ],
}

PALETTES = {}
PALETTE_NAMES = []
for _name, _colors in _PALETTE_RGB.items():
    PALETTES[_name] = np.array([[c[2], c[1], c[0]] for c in _colors], dtype=np.uint8)
    PALETTE_NAMES.append(_name)

# ─── Category / mode hierarchy ───

PIXEL_MODES = [
    ("pixel", "K-means 양자화"),
    ("pixel_dither", "디더링 (Floyd-Steinberg)"),
    ("pixel_palette", "팔레트 매핑"),
    ("pixel_nearest", "Nearest Neighbor"),
    ("pixel_edge", "Edge-preserving"),
    ("pixel_superpixel", "슈퍼픽셀"),
]

ASCII_MODES = [
    ("ascii", "ASCII 아트 (컬러)"),
    ("ascii_bw", "ASCII 아트 (흑백)"),
]

CHAR_MODES = [
    ("hangul", "한글 문자 (컬러)"),
    ("hangul_bw", "한글 문자 (흑백)"),
    ("unicode", "유니코드 블록 (컬러)"),
    ("unicode_bw", "유니코드 블록 (흑백)"),
]

ART_MODES = [
    ("halftone", "하프톤 (신문 스타일)"),
    ("cartoon", "만화 스타일"),
    ("voronoi", "보로노이 아트"),
    ("lowpoly", "로우 폴리"),
    ("stipple", "점묘화"),
    ("glitch", "글리치 아트"),
]

CATEGORIES = [
    ("pixel", "픽셀 변환"),
    ("ascii", "ASCII 변환"),
    ("char", "한글/유니코드"),
    ("art", "아트 효과"),
    ("composite", "복합 모드"),
]

CATEGORY_KEYS = [c[0] for c in CATEGORIES]
CATEGORY_LABELS = [c[1] for c in CATEGORIES]

SUBMODES_BY_CATEGORY = {
    "pixel": PIXEL_MODES,
    "ascii": ASCII_MODES,
    "char": CHAR_MODES,
    "art": ART_MODES,
    "composite": [],
}

ALL_MODES = PIXEL_MODES + ASCII_MODES + CHAR_MODES + ART_MODES
ALL_MODE_KEYS = [m[0] for m in ALL_MODES]
ALL_MODE_LABELS = [m[1] for m in ALL_MODES]

MODE_KEYS = ALL_MODE_KEYS
MODE_LABELS = ALL_MODE_LABELS


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


# ═══════════════════════════════════════════════════════════
#  Pixel conversion functions
# ═══════════════════════════════════════════════════════════

def _add_grid(result, pixel_size, w, h):
    grid_color = (40, 40, 40)
    for x in range(0, w, pixel_size):
        cv2.line(result, (x, 0), (x, h - 1), grid_color, 1)
    for y in range(0, h, pixel_size):
        cv2.line(result, (0, y), (w - 1, y), grid_color, 1)


def pixelize_image(image, pixel_size=8, num_colors=16, grid=False, outline=False):
    """K-means quantization pixel art (original mode)."""
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
        _add_grid(result, pixel_size, w, h)
    return result


def dither_pixelize(image, pixel_size=8, num_colors=16, grid=False):
    """Floyd-Steinberg dithering pixel art."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)

    # Build palette via K-means
    pixels = small.reshape(-1, 3).astype(np.float32)
    actual_colors = min(num_colors, len(np.unique(pixels, axis=0)))
    if actual_colors < 2:
        actual_colors = 2
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    try:
        _, _, centers = cv2.kmeans(
            pixels, actual_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS
        )
        palette = centers.astype(np.float32)
    except cv2.error:
        result = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return result

    # Floyd-Steinberg dithering
    img_f = small.astype(np.float32)
    sh, sw = img_f.shape[:2]

    for y in range(sh):
        for x in range(sw):
            old_px = img_f[y, x].copy()
            dists = np.sum((palette - old_px) ** 2, axis=1)
            nearest = palette[np.argmin(dists)]
            img_f[y, x] = nearest
            err = old_px - nearest

            if x + 1 < sw:
                img_f[y, x + 1] += err * (7.0 / 16.0)
            if y + 1 < sh:
                if x - 1 >= 0:
                    img_f[y + 1, x - 1] += err * (3.0 / 16.0)
                img_f[y + 1, x] += err * (5.0 / 16.0)
                if x + 1 < sw:
                    img_f[y + 1, x + 1] += err * (1.0 / 16.0)

    dithered = np.clip(img_f, 0, 255).astype(np.uint8)
    result = cv2.resize(dithered, (w, h), interpolation=cv2.INTER_NEAREST)
    if grid:
        _add_grid(result, pixel_size, w, h)
    return result


def palette_pixelize(image, pixel_size=8, palette_name="PICO-8", grid=False):
    """Map pixels to a predefined color palette."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    pal = PALETTES.get(palette_name)
    if pal is None:
        pal = PALETTES.get("PICO-8", np.array([[0, 0, 0]], dtype=np.uint8))

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)

    # Vectorized nearest-palette-color mapping
    flat = small.reshape(-1, 3).astype(np.float32)
    pal_f = pal.astype(np.float32)
    # dist[i, j] = squared distance between pixel i and palette color j
    dists = np.sum((flat[:, np.newaxis, :] - pal_f[np.newaxis, :, :]) ** 2, axis=2)
    indices = np.argmin(dists, axis=1)
    mapped = pal[indices].reshape(small.shape)

    result = cv2.resize(mapped, (w, h), interpolation=cv2.INTER_NEAREST)
    if grid:
        _add_grid(result, pixel_size, w, h)
    return result


def nearest_pixelize(image, pixel_size=8, grid=False):
    """Pure nearest-neighbor downscale/upscale."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
    result = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    if grid:
        _add_grid(result, pixel_size, w, h)
    return result


def edge_pixelize(image, pixel_size=8, num_colors=16, grid=False):
    """Edge-preserving pixelization using bilateral filter + edge overlay."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    filtered = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = cv2.resize(filtered, (small_w, small_h), interpolation=cv2.INTER_AREA)

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

    edges_up = cv2.resize(edges, (w, h), interpolation=cv2.INTER_NEAREST)
    edge_mask = edges_up > 0
    dark = (result.astype(np.int16) * 0.4).astype(np.uint8)
    result[edge_mask] = dark[edge_mask]

    if grid:
        _add_grid(result, pixel_size, w, h)
    return result


def superpixel_pixelize(image, pixel_size=8, num_colors=16, grid=False):
    """Superpixel-like pixelization via mean-shift filtering."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    sp = max(5, pixel_size * 2)
    sr = max(10, pixel_size * 3)
    shifted = cv2.pyrMeanShiftFiltering(image, sp=sp, sr=sr)

    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = cv2.resize(shifted, (small_w, small_h), interpolation=cv2.INTER_AREA)

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
        _add_grid(result, pixel_size, w, h)
    return result


# ═══════════════════════════════════════════════════════════
#  Art effect functions
# ═══════════════════════════════════════════════════════════

def halftone_image(image, dot_size=8):
    """Halftone (newspaper-style) with colored dots sized by brightness."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    result = np.full((h, w, 3), 240, dtype=np.uint8)

    for y in range(0, h, dot_size):
        for x in range(0, w, dot_size):
            by = min(y + dot_size, h)
            bx = min(x + dot_size, w)
            block_gray = gray[y:by, x:bx]
            brightness = float(np.mean(block_gray))

            radius = int((1.0 - brightness / 255.0) * dot_size * 0.6)
            if radius < 1:
                continue

            cx = x + dot_size // 2
            cy = y + dot_size // 2
            block_color = image[y:by, x:bx]
            mean_bgr = block_color.mean(axis=(0, 1))
            color = (int(mean_bgr[0]), int(mean_bgr[1]), int(mean_bgr[2]))
            cv2.circle(result, (cx, cy), radius, color, -1, cv2.LINE_AA)

    return result


def cartoon_image(image, pixel_size=8):
    """Cartoon style: bilateral filter smoothing + adaptive threshold edges."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    num_passes = max(2, min(7, pixel_size // 2))
    color = image.copy()
    for _ in range(num_passes):
        color = cv2.bilateralFilter(color, d=7, sigmaColor=9, sigmaSpace=7)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)

    block_size = max(3, min(15, pixel_size | 1))
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, block_size, 2,
    )

    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.bitwise_and(color, edges_bgr)


def voronoi_image(image, pixel_size=8):
    """Voronoi tessellation art using edge-aware seed points."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h < 4 or w < 4:
        return image.copy()

    num_points = max(80, (h * w) // (pixel_size * pixel_size * 4))
    num_points = min(num_points, 3000)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_yx = np.column_stack(np.where(edges > 0))

    n_edge = min(len(edge_yx), num_points * 2 // 3)
    rng = np.random.RandomState(42)
    if n_edge > 0:
        idx = rng.choice(len(edge_yx), n_edge, replace=False)
        edge_pts = edge_yx[idx][:, ::-1]
    else:
        edge_pts = np.empty((0, 2), dtype=int)

    n_rand = max(10, num_points - len(edge_pts))
    rand_pts = np.column_stack([rng.randint(1, w - 1, n_rand), rng.randint(1, h - 1, n_rand)])
    all_pts = np.vstack([edge_pts, rand_pts]) if len(edge_pts) > 0 else rand_pts

    rect = (0, 0, w, h)
    subdiv = cv2.Subdiv2D(rect)
    for pt in all_pts:
        x, y = float(pt[0]), float(pt[1])
        if 1 <= x < w - 1 and 1 <= y < h - 1:
            try:
                subdiv.insert((x, y))
            except cv2.error:
                pass

    try:
        facets, _ = subdiv.getVoronoiFacetList([])
    except cv2.error:
        return image.copy()

    result = np.zeros_like(image)
    for facet in facets:
        ifacet = np.array(facet, dtype=np.int32)
        ifacet[:, 0] = np.clip(ifacet[:, 0], 0, w - 1)
        ifacet[:, 1] = np.clip(ifacet[:, 1], 0, h - 1)

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, ifacet, 255)
        mean_c = cv2.mean(image, mask=mask)[:3]
        cv2.fillConvexPoly(result, ifacet, mean_c)
        cv2.polylines(result, [ifacet], True, (30, 30, 30), 1, cv2.LINE_AA)

    return result


def lowpoly_image(image, pixel_size=8):
    """Low-poly art via Delaunay triangulation with average-color fill."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h < 4 or w < 4:
        return image.copy()

    num_points = max(50, (h * w) // (pixel_size * pixel_size * 6))
    num_points = min(num_points, 2500)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_yx = np.column_stack(np.where(edges > 0))

    n_edge = min(len(edge_yx), num_points * 2 // 3)
    rng = np.random.RandomState(42)
    if n_edge > 0:
        idx = rng.choice(len(edge_yx), n_edge, replace=False)
        edge_pts = edge_yx[idx][:, ::-1]
    else:
        edge_pts = np.empty((0, 2), dtype=int)

    corners = np.array([[1, 1], [w - 2, 1], [1, h - 2], [w - 2, h - 2]])
    n_rand = max(10, num_points - len(edge_pts) - 4)
    rand_pts = np.column_stack([rng.randint(1, w - 1, n_rand), rng.randint(1, h - 1, n_rand)])

    parts = [p for p in [edge_pts, corners, rand_pts] if len(p) > 0]
    all_pts = np.vstack(parts)

    rect = (0, 0, w, h)
    subdiv = cv2.Subdiv2D(rect)
    for pt in all_pts:
        x, y = float(pt[0]), float(pt[1])
        if 1 <= x < w - 1 and 1 <= y < h - 1:
            try:
                subdiv.insert((x, y))
            except cv2.error:
                pass

    triangles = subdiv.getTriangleList()
    result = np.zeros_like(image)

    for t in triangles:
        pts = np.array([[t[0], t[1]], [t[2], t[3]], [t[4], t[5]]], dtype=np.int32)
        if (np.all(pts[:, 0] >= 0) and np.all(pts[:, 0] < w) and
                np.all(pts[:, 1] >= 0) and np.all(pts[:, 1] < h)):
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillConvexPoly(mask, pts, 255)
            mean_c = cv2.mean(image, mask=mask)[:3]
            cv2.fillConvexPoly(result, pts, mean_c)

    return result


def stipple_image(image, pixel_size=8):
    """Stipple (pointillism) art: density-weighted random dot placement."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    inv = (255 - gray).astype(np.float64)
    total_inv = inv.sum()
    if total_inv == 0:
        return np.full((h, w, 3), 245, dtype=np.uint8)
    prob = inv / total_inv

    area = h * w
    scale = max(0.05, (34 - pixel_size) / 32.0)
    total_dots = int(area / 50 * scale)
    total_dots = max(200, min(total_dots, 60000))
    dot_r = max(1, pixel_size // 5)

    result = np.full((h, w, 3), 245, dtype=np.uint8)
    flat_idx = np.random.choice(h * w, size=total_dots, p=prob.flatten(), replace=True)
    ys = flat_idx // w
    xs = flat_idx % w

    for x, y in zip(xs, ys):
        color = (int(image[y, x, 0]), int(image[y, x, 1]), int(image[y, x, 2]))
        cv2.circle(result, (int(x), int(y)), dot_r, color, -1, cv2.LINE_AA)

    return result


def glitch_image(image, pixel_size=8):
    """Glitch art: channel shift, block displacement, scan lines, color corruption."""
    if image is None:
        return None
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return None

    result = image.copy()
    intensity = pixel_size

    b, g, r = cv2.split(result)
    shift = intensity * 2
    b = np.roll(b, shift, axis=1)
    r = np.roll(r, -shift, axis=1)
    result = cv2.merge([b, g, r])

    rng = np.random.RandomState(None)
    n_blocks = intensity * 2
    for _ in range(n_blocks):
        y = rng.randint(0, h)
        bh = rng.randint(1, max(2, h // 30))
        offset = rng.randint(-w // 5, max(1, w // 5))
        y_end = min(y + bh, h)
        result[y:y_end] = np.roll(result[y:y_end], offset, axis=1)

    scan = max(2, 5 - intensity // 8)
    result[::scan] = np.clip(result[::scan].astype(np.int16) * 7 // 10, 0, 255).astype(np.uint8)

    for _ in range(intensity):
        bx = rng.randint(0, w)
        by = rng.randint(0, h)
        bw = rng.randint(10, max(11, w // 10))
        bh2 = rng.randint(2, max(3, h // 30))
        ch = rng.randint(0, 3)
        result[by:min(by + bh2, h), bx:min(bx + bw, w), ch] = rng.randint(0, 256)

    return result


# ═══════════════════════════════════════════════════════════
#  Character art functions
# ═══════════════════════════════════════════════════════════

def _char_art_image(image, cols, char_set, color_mode, char_w, char_h):
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


# ═══════════════════════════════════════════════════════════
#  Composite mode
# ═══════════════════════════════════════════════════════════

def composite_convert(frame, modes, pixel_size, num_colors, grid, outline, extra=None):
    """2x2 grid: top-left = original, other 3 = converted."""
    h, w = frame.shape[:2]
    panels = [frame.copy()]
    for mode in modes:
        converted = convert_single_frame(frame, mode, pixel_size, num_colors, grid, outline, extra)
        if converted is not None:
            converted = cv2.resize(converted, (w, h))
        else:
            converted = frame.copy()
        panels.append(converted)

    while len(panels) < 4:
        panels.append(frame.copy())

    top = np.hstack([panels[0], panels[1]])
    bottom = np.hstack([panels[2], panels[3]])
    return np.vstack([top, bottom])


# ═══════════════════════════════════════════════════════════
#  Unified dispatch
# ═══════════════════════════════════════════════════════════

def convert_single_frame(frame, mode, pixel_size, num_colors, grid, outline, extra=None):
    """Convert a single frame. Used by all threads and CLI."""
    if extra is None:
        extra = {}

    if mode == "composite":
        comp_modes = extra.get("composite_modes", ["pixel", "ascii", "hangul"])
        return composite_convert(frame, comp_modes, pixel_size, num_colors, grid, outline, extra)

    # Pixel modes
    if mode == "pixel":
        return pixelize_image(frame, pixel_size, num_colors, grid, outline)
    elif mode == "pixel_dither":
        return dither_pixelize(frame, pixel_size, num_colors, grid)
    elif mode == "pixel_palette":
        palette_name = extra.get("palette", "PICO-8")
        return palette_pixelize(frame, pixel_size, palette_name, grid)
    elif mode == "pixel_nearest":
        return nearest_pixelize(frame, pixel_size, grid)
    elif mode == "pixel_edge":
        return edge_pixelize(frame, pixel_size, num_colors, grid)
    elif mode == "pixel_superpixel":
        return superpixel_pixelize(frame, pixel_size, num_colors, grid)

    # ASCII modes
    elif mode == "ascii":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return ascii_art_image(frame, cols=cols, color_mode=True)
    elif mode == "ascii_bw":
        cols = max(30, frame.shape[1] // (pixel_size * 2))
        return ascii_art_image(frame, cols=cols, color_mode=False)

    # Character modes
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

    # Art effect modes
    elif mode == "halftone":
        return halftone_image(frame, dot_size=pixel_size)
    elif mode == "cartoon":
        return cartoon_image(frame, pixel_size=pixel_size)
    elif mode == "voronoi":
        return voronoi_image(frame, pixel_size=pixel_size)
    elif mode == "lowpoly":
        return lowpoly_image(frame, pixel_size=pixel_size)
    elif mode == "stipple":
        return stipple_image(frame, pixel_size=pixel_size)
    elif mode == "glitch":
        return glitch_image(frame, pixel_size=pixel_size)

    # Fallback
    return pixelize_image(frame, pixel_size, num_colors, grid, outline)


# ═══════════════════════════════════════════════════════════
#  Threads
# ═══════════════════════════════════════════════════════════

class ImageConvertThread(QThread):
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, image, pixel_size, num_colors, grid, outline, mode="pixel", extra=None):
        super().__init__()
        self.image = image
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode
        self.extra = extra or {}

    def run(self):
        try:
            result = convert_single_frame(
                self.image, self.mode,
                self.pixel_size, self.num_colors, self.grid, self.outline,
                self.extra,
            )
            if result is not None:
                self.finished.emit(result)
            else:
                self.error.emit("변환에 실패했습니다.")
        except Exception as e:
            self.error.emit(str(e))


class VideoConvertThread(QThread):
    progress = pyqtSignal(int, float, float)
    frame_converted = pyqtSignal(np.ndarray)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, pixel_size, num_colors, grid, outline,
                 mode="pixel", extra=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode
        self.extra = extra or {}
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
                dummy, self.mode, self.pixel_size, self.num_colors,
                self.grid, self.outline, self.extra,
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
                    frame, self.mode, self.pixel_size, self.num_colors,
                    self.grid, self.outline, self.extra,
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
    finished = pyqtSignal(list, float)
    error = pyqtSignal(str)

    def __init__(self, input_path, pixel_size, num_colors, grid, outline,
                 mode="pixel", duration=5.0, extra=None):
        super().__init__()
        self.input_path = input_path
        self.pixel_size = pixel_size
        self.num_colors = num_colors
        self.grid = grid
        self.outline = outline
        self.mode = mode
        self.duration = duration
        self.extra = extra or {}
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
                    frame, self.mode, self.pixel_size, self.num_colors,
                    self.grid, self.outline, self.extra,
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

import os
import sys
import time as _time
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QToolBar, QAction, QFileDialog, QStatusBar,
    QProgressBar, QLabel, QSlider, QSpinBox, QCheckBox,
    QPushButton, QFrame, QMessageBox, QGridLayout,
    QApplication, QInputDialog, QComboBox
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QKeySequence, QIcon

try:
    from PyQt5.QtWinExtras import QWinTaskbarButton
    HAS_WIN_TASKBAR = True
except ImportError:
    HAS_WIN_TASKBAR = False

from config_manager import ConfigManager, get_base_dir
from history_manager import HistoryManager
from converter import (
    pixelize_image, ascii_art_image, hangul_art_image, unicode_art_image,
    convert_single_frame,
    ImageConvertThread, VideoConvertThread, VideoPreviewThread,
    is_image, is_video, get_supported_filter,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS,
    CATEGORIES, CATEGORY_KEYS, CATEGORY_LABELS,
    PIXEL_MODES, ASCII_MODES, CHAR_MODES, ART_MODES, SUBMODES_BY_CATEGORY,
    ALL_MODES, ALL_MODE_KEYS, ALL_MODE_LABELS,
    MODE_KEYS, MODE_LABELS,
    PALETTE_NAMES,
)
from styles import get_theme_stylesheet
from canvas_widget import DrawingCanvas, CanvasToolbar
from preview_widget import PreviewPanel, VideoPreviewPanel, cv2_to_qpixmap
from history_widget import HistoryWidget
from output_browser import OutputBrowser
from settings_dialog import SettingsDialog


def _fmt_time(seconds):
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.history_manager = HistoryManager()

        self.current_image = None
        self.result_image = None
        self.current_video_path = None
        self.current_mode = "none"
        self._convert_thread = None
        self._preview_thread = None
        self._current_input_path = None
        self._taskbar_btn = None

        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.setInterval(400)
        self._live_timer.timeout.connect(self._live_preview)

        self._video_preview_timer = QTimer(self)
        self._video_preview_timer.setSingleShot(True)
        self._video_preview_timer.setInterval(600)
        self._video_preview_timer.timeout.connect(self._generate_video_preview)

        self.setWindowTitle("ToDoT - 도트 이미지 변환기")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 820)

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()
        self._load_icon()

    def showEvent(self, event):
        super().showEvent(event)
        if HAS_WIN_TASKBAR and self._taskbar_btn is None:
            self._taskbar_btn = QWinTaskbarButton(self)
            self._taskbar_btn.setWindow(self.windowHandle())

    # ─── UI Setup ───

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        self._setup_left_panel()
        self._setup_right_panel()

        self.splitter.setSizes([320, 980])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter)

    def _setup_left_panel(self):
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.left_tabs = QTabWidget()

        output_dir = self.config.get("output_dir", os.path.join(get_base_dir(), "output"))
        self.output_browser = OutputBrowser(output_dir)
        self.output_browser.file_selected.connect(self._on_output_file_selected)
        self.output_browser.file_double_clicked.connect(self._load_file)
        self.left_tabs.addTab(self.output_browser, "📁 결과물")

        self.history_widget = HistoryWidget(self.history_manager)
        self.history_widget.item_clicked.connect(self._load_from_history)
        self.left_tabs.addTab(self.history_widget, "🕐 히스토리")

        left_layout.addWidget(self.left_tabs)
        self.splitter.addWidget(left_panel)

    def _setup_right_panel(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tab_widget = QTabWidget()

        self._setup_preview_tab()
        self._setup_canvas_tab()
        self._setup_video_tab()

        right_layout.addWidget(self.tab_widget, 1)

        self._setup_convert_panel()
        right_layout.addWidget(self.convert_panel)

        self.splitter.addWidget(right_panel)

    def _setup_preview_tab(self):
        preview_container = QWidget()
        preview_layout = QHBoxLayout(preview_container)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(8)

        self.original_panel = PreviewPanel("원본")
        self.result_panel = PreviewPanel("변환 결과")
        self.result_panel.image_label.set_placeholder("변환 버튼을 눌러주세요")

        preview_layout.addWidget(self.original_panel, 1)
        preview_layout.addWidget(self.result_panel, 1)

        self.tab_widget.addTab(preview_container, "🖼 이미지 미리보기")

    def _setup_canvas_tab(self):
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.drawing_canvas = DrawingCanvas()
        self.canvas_toolbar = CanvasToolbar(self.drawing_canvas)
        canvas_layout.addWidget(self.canvas_toolbar)
        canvas_layout.addWidget(self.drawing_canvas, 1)

        self.tab_widget.addTab(canvas_container, "✏ 새 그림")

    def _setup_video_tab(self):
        video_container = QWidget()
        video_layout = QHBoxLayout(video_container)
        video_layout.setContentsMargins(8, 8, 8, 8)
        video_layout.setSpacing(8)

        self.video_original_panel = VideoPreviewPanel("원본 동영상")
        self.video_result_panel = VideoPreviewPanel("변환 결과 (5초 미리보기)")

        video_layout.addWidget(self.video_original_panel, 1)
        video_layout.addWidget(self.video_result_panel, 1)

        self.tab_widget.addTab(video_container, "🎬 동영상 미리보기")

    # ─── Convert panel (2 rows) ───

    def _setup_convert_panel(self):
        self.convert_panel = QFrame()
        self.convert_panel.setObjectName("convertPanel")
        self.convert_panel.setFixedHeight(115)

        outer = QVBoxLayout(self.convert_panel)
        outer.setContentsMargins(16, 6, 16, 6)
        outer.setSpacing(4)

        # Row 1: category + sub-mode + composite selectors + palette
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        row1.addWidget(QLabel("카테고리:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORY_LABELS)
        self.category_combo.setFixedWidth(130)
        self.category_combo.setToolTip("변환 카테고리 선택")
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        row1.addWidget(self.category_combo)

        self._sub_mode_label = QLabel("모드:")
        row1.addWidget(self._sub_mode_label)
        self.sub_mode_combo = QComboBox()
        self.sub_mode_combo.setFixedWidth(190)
        self.sub_mode_combo.setToolTip("세부 변환 모드 선택")
        self.sub_mode_combo.currentIndexChanged.connect(self._on_sub_mode_changed)
        row1.addWidget(self.sub_mode_combo)

        # Palette selector (only for pixel_palette)
        self._palette_label = QLabel("팔레트:")
        self._palette_label.setVisible(False)
        row1.addWidget(self._palette_label)
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(PALETTE_NAMES)
        self.palette_combo.setFixedWidth(130)
        self.palette_combo.setToolTip("사전 정의 컬러 팔레트")
        self.palette_combo.setVisible(False)
        self.palette_combo.currentIndexChanged.connect(self._on_param_changed)
        row1.addWidget(self.palette_combo)

        # Composite mode selectors (hidden by default)
        self._composite_widget = QWidget()
        comp_layout = QHBoxLayout(self._composite_widget)
        comp_layout.setContentsMargins(0, 0, 0, 0)
        comp_layout.setSpacing(8)

        self._comp_combos = []
        comp_positions = ["우상단", "좌하단", "우하단"]
        comp_defaults = [0, 2, 6]  # pixel, ascii, hangul by index in ALL_MODES
        for i, pos in enumerate(comp_positions):
            comp_layout.addWidget(QLabel(f"{pos}:"))
            combo = QComboBox()
            combo.addItems(ALL_MODE_LABELS)
            combo.setFixedWidth(160)
            combo.setToolTip(f"복합 모드 {pos} 패널의 변환 모드")
            if i < len(comp_defaults):
                combo.setCurrentIndex(comp_defaults[i])
            combo.currentIndexChanged.connect(self._on_param_changed)
            comp_layout.addWidget(combo)
            self._comp_combos.append(combo)

        self._composite_widget.setVisible(False)
        row1.addWidget(self._composite_widget)

        row1.addStretch()
        outer.addLayout(row1)

        # Row 2: parameters + action buttons
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        row2.addWidget(QLabel("크기:"))
        self.pixel_size_slider = QSlider(Qt.Horizontal)
        self.pixel_size_slider.setRange(2, 32)
        self.pixel_size_slider.setValue(self.config.get("pixel_size", 8))
        self.pixel_size_slider.setFixedWidth(120)
        self.pixel_size_slider.setToolTip("하나의 도트 블록 크기 (클수록 더 큰 도트)")
        self.pixel_size_slider.valueChanged.connect(self._on_param_changed)
        row2.addWidget(self.pixel_size_slider)
        self.pixel_size_label = QLabel(str(self.config.get("pixel_size", 8)))
        self.pixel_size_label.setFixedWidth(24)
        self.pixel_size_label.setObjectName("accentLabel")
        row2.addWidget(self.pixel_size_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        row2.addWidget(sep)

        self.color_label = QLabel("색상:")
        row2.addWidget(self.color_label)
        self.color_spin = QSpinBox()
        self.color_spin.setRange(2, 256)
        self.color_spin.setValue(self.config.get("num_colors", 16))
        self.color_spin.setFixedWidth(72)
        self.color_spin.setToolTip("사용할 색상 팔레트 크기")
        self.color_spin.valueChanged.connect(self._on_param_changed)
        row2.addWidget(self.color_spin)

        self.grid_check = QCheckBox("격자")
        self.grid_check.setChecked(self.config.get("grid_lines", False))
        self.grid_check.setToolTip("도트 사이에 격자선을 표시합니다")
        self.grid_check.stateChanged.connect(self._on_param_changed)
        row2.addWidget(self.grid_check)

        self.outline_check = QCheckBox("윤곽선")
        self.outline_check.setChecked(self.config.get("outline", False))
        self.outline_check.setToolTip("윤곽선을 강조합니다 (K-means 전용)")
        self.outline_check.stateChanged.connect(self._on_param_changed)
        row2.addWidget(self.outline_check)

        row2.addStretch()

        self.cancel_btn = QPushButton("✕ 취소")
        self.cancel_btn.setFixedSize(80, 36)
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.setToolTip("진행 중인 변환을 취소합니다")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_convert)
        row2.addWidget(self.cancel_btn)

        self.convert_btn = QPushButton("⚡ 변환하기")
        self.convert_btn.setFixedSize(120, 36)
        self.convert_btn.setToolTip("원본 해상도로 최종 변환합니다")
        self.convert_btn.clicked.connect(self._convert)
        row2.addWidget(self.convert_btn)

        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setFixedSize(80, 36)
        self.save_btn.setObjectName("secondaryBtn")
        self.save_btn.setToolTip("변환 결과를 출력 폴더에 저장합니다 (Ctrl+S)")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_result)
        row2.addWidget(self.save_btn)

        outer.addLayout(row2)

        # Initialize sub-mode list for default category
        self._on_category_changed(0)

    # ─── Menu / Toolbar / Statusbar ───

    def _setup_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("파일(&F)")
        new_action = QAction("새 그림(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_canvas)
        file_menu.addAction(new_action)

        open_action = QAction("파일 열기(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()
        save_action = QAction("결과 저장(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_result)
        file_menu.addAction(save_action)

        save_as_action = QAction("다른 이름으로 저장(&A)", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_result_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("편집(&E)")
        undo_action = QAction("실행 취소(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(lambda: self.drawing_canvas.undo())
        edit_menu.addAction(undo_action)

        redo_action = QAction("다시 실행(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(lambda: self.drawing_canvas.redo())
        edit_menu.addAction(redo_action)

        view_menu = menubar.addMenu("보기(&V)")
        toggle_left = QAction("좌측 패널(&L)", self)
        toggle_left.setCheckable(True)
        toggle_left.setChecked(True)
        toggle_left.triggered.connect(
            lambda checked: self.splitter.widget(0).setVisible(checked)
        )
        view_menu.addAction(toggle_left)

        tools_menu = menubar.addMenu("도구(&T)")
        settings_action = QAction("설정(&S)", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

        help_menu = menubar.addMenu("도움말(&H)")
        about_action = QAction("ToDoT 정보(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("메인 도구")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        new_btn = QAction("📄 새 그림", self)
        new_btn.triggered.connect(self._new_canvas)
        toolbar.addAction(new_btn)

        open_btn = QAction("📂 파일 열기", self)
        open_btn.triggered.connect(self._open_file)
        toolbar.addAction(open_btn)

        save_btn = QAction("💾 저장", self)
        save_btn.triggered.connect(self._save_result)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        settings_btn = QAction("⚙ 설정", self)
        settings_btn.triggered.connect(self._open_settings)
        toolbar.addAction(settings_btn)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("준비")
        self.statusbar.addWidget(self.status_label, 1)

        self.time_label = QLabel("")
        self.statusbar.addPermanentWidget(self.time_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def _apply_theme(self):
        theme = self.config.get("theme", "Catppuccin Mocha")
        self.setStyleSheet(get_theme_stylesheet(theme))

    def _load_icon(self):
        icon_path = os.path.join(get_base_dir(), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    # ─── Taskbar progress ───

    def _set_taskbar_progress(self, value, visible=True):
        if not HAS_WIN_TASKBAR or self._taskbar_btn is None:
            return
        prog = self._taskbar_btn.progress()
        prog.setVisible(visible)
        if visible:
            prog.setRange(0, 100)
            prog.setValue(value)

    # ─── Category / sub-mode logic ───

    def _on_category_changed(self, idx):
        cat_key = CATEGORY_KEYS[idx] if 0 <= idx < len(CATEGORY_KEYS) else "pixel"
        is_composite = (cat_key == "composite")

        self._sub_mode_label.setVisible(not is_composite)
        self.sub_mode_combo.setVisible(not is_composite)
        self._composite_widget.setVisible(is_composite)

        if not is_composite:
            modes = SUBMODES_BY_CATEGORY.get(cat_key, PIXEL_MODES)
            self.sub_mode_combo.blockSignals(True)
            self.sub_mode_combo.clear()
            self.sub_mode_combo.addItems([m[1] for m in modes])
            self.sub_mode_combo.blockSignals(False)
            self._on_sub_mode_changed(0)
        else:
            self._update_param_visibility()
            self._on_param_changed()

    def _on_sub_mode_changed(self, _idx=0):
        self._update_param_visibility()
        self._on_param_changed()

    def _update_param_visibility(self):
        mode = self._get_convert_mode()
        cat_key = self._get_category_key()

        is_pixel_cat = (cat_key == "pixel")
        needs_colors = mode in ("pixel", "pixel_dither", "pixel_edge", "pixel_superpixel")
        needs_outline = (mode == "pixel")
        is_palette = (mode == "pixel_palette")
        is_art = (cat_key == "art")

        self.color_spin.setEnabled(needs_colors)
        self.color_label.setEnabled(needs_colors)
        self.grid_check.setEnabled(is_pixel_cat)
        self.outline_check.setEnabled(needs_outline)

        self._palette_label.setVisible(is_palette)
        self.palette_combo.setVisible(is_palette)

        if is_art:
            self.color_spin.setEnabled(False)
            self.color_label.setEnabled(False)
            self.grid_check.setEnabled(False)
            self.outline_check.setEnabled(False)

    def _get_category_key(self):
        idx = self.category_combo.currentIndex()
        if 0 <= idx < len(CATEGORY_KEYS):
            return CATEGORY_KEYS[idx]
        return "pixel"

    def _get_convert_mode(self):
        cat_key = self._get_category_key()
        if cat_key == "composite":
            return "composite"
        modes = SUBMODES_BY_CATEGORY.get(cat_key, PIXEL_MODES)
        idx = self.sub_mode_combo.currentIndex()
        if 0 <= idx < len(modes):
            return modes[idx][0]
        return "pixel"

    def _get_extra(self):
        extra = {}
        mode = self._get_convert_mode()
        if mode == "pixel_palette":
            extra["palette"] = self.palette_combo.currentText()
        elif mode == "composite":
            comp_modes = []
            for combo in self._comp_combos:
                ci = combo.currentIndex()
                if 0 <= ci < len(ALL_MODE_KEYS):
                    comp_modes.append(ALL_MODE_KEYS[ci])
                else:
                    comp_modes.append("pixel")
            extra["composite_modes"] = comp_modes
        return extra

    # ─── Live preview ───

    def _on_param_changed(self, _=None):
        self.pixel_size_label.setText(str(self.pixel_size_slider.value()))

        if self.current_image is not None and self.current_mode in ("image", "canvas"):
            self._live_timer.start()
        elif self.current_mode == "video" and self.current_video_path:
            self._video_preview_timer.start()

    def _live_preview(self):
        if self.current_image is None:
            return

        preview_img = self.current_image.copy()
        h, w = preview_img.shape[:2]
        max_dim = 600
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            preview_img = cv2.resize(preview_img, (int(w * scale), int(h * scale)))

        params = self._get_params()
        mode = self._get_convert_mode()
        extra = self._get_extra()

        if hasattr(self, '_live_worker') and self._live_worker and self._live_worker.isRunning():
            return

        self._live_worker = ImageConvertThread(
            preview_img, params["pixel_size"], params["num_colors"],
            params["grid"], params["outline"], mode, extra
        )
        self._live_worker.finished.connect(self._on_live_preview_done)
        self._live_worker.error.connect(lambda msg: self.status_label.setText(f"미리보기 오류: {msg[:60]}"))
        self._live_worker.start()

    def _on_live_preview_done(self, result):
        self.result_panel.set_image(result)
        self.status_label.setText("미리보기 업데이트됨")

    def _generate_video_preview(self):
        if not self.current_video_path or not os.path.exists(self.current_video_path):
            return

        if self._preview_thread and self._preview_thread.isRunning():
            try:
                self._preview_thread.finished.disconnect()
                self._preview_thread.error.disconnect()
            except TypeError:
                pass
            self._preview_thread.cancel()
            self._preview_thread.wait(1000)

        params = self._get_params()
        mode = self._get_convert_mode()
        extra = self._get_extra()
        self.status_label.setText("동영상 5초 미리보기 생성 중...")

        self._preview_thread = VideoPreviewThread(
            self.current_video_path,
            params["pixel_size"], params["num_colors"],
            params["grid"], params["outline"], mode, duration=5.0,
            extra=extra,
        )
        thread_id = id(self._preview_thread)

        def on_done(frames, fps):
            if self._preview_thread is not None and id(self._preview_thread) == thread_id:
                self._on_video_preview_ready(frames, fps)

        self._preview_thread.finished.connect(on_done)
        self._preview_thread.error.connect(lambda msg: self.status_label.setText(msg))
        self._preview_thread.start()

    def _on_video_preview_ready(self, frames, fps):
        self.video_result_panel.load_frames(frames, fps)
        self.status_label.setText(f"동영상 미리보기 준비 완료 ({len(frames)} 프레임, {len(frames)/fps:.1f}초)")

    # ─── File operations ───

    def _new_canvas(self):
        width, ok1 = QInputDialog.getInt(self, "캔버스 크기", "너비 (px):", 800, 100, 4096)
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(self, "캔버스 크기", "높이 (px):", 600, 100, 4096)
        if not ok2:
            return

        self.drawing_canvas.set_canvas_size(width, height)
        self.current_mode = "canvas"
        self.tab_widget.setCurrentIndex(1)
        self.status_label.setText(f"새 캔버스 ({width}x{height})")

    def _open_file(self):
        last_dir = self.config.get("last_open_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "파일 열기", last_dir, get_supported_filter()
        )
        if not path:
            return
        self.config.set("last_open_dir", os.path.dirname(path))
        self._load_file(path)

    def _load_file(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "오류", f"파일을 찾을 수 없습니다:\n{path}")
            return
        if is_image(path):
            self._load_image(path)
        elif is_video(path):
            self._load_video(path)
        else:
            QMessageBox.warning(self, "오류", "지원하지 않는 파일 형식입니다.")

    def _load_image(self, path):
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            QMessageBox.warning(self, "오류", "이미지를 읽을 수 없습니다.")
            return

        self.current_image = img
        self.result_image = None
        self.current_video_path = None
        self.current_mode = "image"
        self._current_input_path = path

        self.original_panel.set_image(img)
        self.result_panel.clear()
        self.save_btn.setEnabled(False)

        self.tab_widget.setCurrentIndex(0)
        h, w = img.shape[:2]
        self.status_label.setText(f"이미지 로드: {os.path.basename(path)} ({w}x{h})")
        self._live_timer.start()

    def _load_video(self, path):
        self.current_video_path = path
        self.current_image = None
        self.result_image = None
        self.current_mode = "video"
        self._current_input_path = path

        if not self.video_original_panel.load_video(path):
            QMessageBox.warning(self, "오류", "동영상을 열 수 없습니다.")
            self.current_video_path = None
            self.current_mode = "none"
            return

        self.video_result_panel.clear()
        self.save_btn.setEnabled(False)

        self.tab_widget.setCurrentIndex(2)
        self.status_label.setText(f"동영상 로드: {os.path.basename(path)}")
        self._video_preview_timer.start()

    def _load_from_history(self, input_path, output_path):
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "오류", f"원본 파일을 찾을 수 없습니다:\n{input_path}")
            return
        self._load_file(input_path)
        if os.path.exists(output_path):
            if is_image(output_path):
                result = cv2.imread(output_path, cv2.IMREAD_COLOR)
                if result is not None:
                    self.result_image = result
                    self.result_panel.set_image(result)
                    self.save_btn.setEnabled(True)
            elif is_video(output_path):
                self.video_result_panel.load_video(output_path)
                self.save_btn.setEnabled(True)

    def _on_output_file_selected(self, path):
        if is_image(path):
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                h, w = img.shape[:2]
                self.status_label.setText(f"선택: {os.path.basename(path)} ({w}x{h})")

    # ─── Conversion ───

    def _get_params(self):
        return {
            "pixel_size": self.pixel_size_slider.value(),
            "num_colors": self.color_spin.value(),
            "grid": self.grid_check.isChecked(),
            "outline": self.outline_check.isChecked(),
        }

    def _convert(self):
        tab_idx = self.tab_widget.currentIndex()
        if tab_idx == 1:
            self._convert_canvas()
        elif tab_idx == 2 or self.current_mode == "video":
            self._convert_video()
        else:
            self._convert_image()

    def _convert_image(self):
        if self.current_image is None:
            QMessageBox.information(self, "알림", "먼저 이미지를 열어주세요.")
            return
        params = self._get_params()
        mode = self._get_convert_mode()
        extra = self._get_extra()
        self.status_label.setText("이미지 변환 중...")
        self.convert_btn.setEnabled(False)
        QApplication.processEvents()

        self._convert_thread = ImageConvertThread(
            self.current_image.copy(),
            params["pixel_size"], params["num_colors"],
            params["grid"], params["outline"], mode, extra
        )
        self._convert_thread.finished.connect(self._on_image_converted)
        self._convert_thread.error.connect(self._on_convert_error)
        self._convert_thread.start()

    def _convert_canvas(self):
        img = self.drawing_canvas.get_image_as_numpy()
        if img is None:
            return
        self.current_image = img
        self.original_panel.set_image(img)
        self.current_mode = "canvas"

        params = self._get_params()
        mode = self._get_convert_mode()
        extra = self._get_extra()
        self.status_label.setText("캔버스 그림 변환 중...")
        self.convert_btn.setEnabled(False)

        self._convert_thread = ImageConvertThread(
            img.copy(),
            params["pixel_size"], params["num_colors"],
            params["grid"], params["outline"], mode, extra
        )
        self._convert_thread.finished.connect(self._on_canvas_converted)
        self._convert_thread.error.connect(self._on_convert_error)
        self._convert_thread.start()

    def _on_image_converted(self, result):
        self.result_image = result
        self.result_panel.set_image(result)
        self.save_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.tab_widget.setCurrentIndex(0)
        self.status_label.setText("이미지 변환 완료!")

    def _on_canvas_converted(self, result):
        self.result_image = result
        self.result_panel.set_image(result)
        self.save_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.tab_widget.setCurrentIndex(0)
        self.status_label.setText("캔버스 그림 변환 완료!")

    def _convert_video(self):
        if not self.current_video_path or not os.path.exists(self.current_video_path):
            QMessageBox.information(self, "알림", "먼저 동영상을 열어주세요.")
            return
        params = self._get_params()
        mode = self._get_convert_mode()
        extra = self._get_extra()
        output_dir = self.config.get("output_dir", os.path.join(get_base_dir(), "output"))
        os.makedirs(output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(self.current_video_path))[0]
        suffix = f"_{mode}" if mode != "pixel" else "_dot"
        ext = "." + self.config.get("video_format", "MP4").lower()
        output_path = os.path.join(output_dir, f"{base}{suffix}{ext}")

        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base}{suffix}_{counter}{ext}")
            counter += 1

        self.status_label.setText("동영상 변환 중...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.time_label.setText("")
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self._set_taskbar_progress(0, True)

        self._convert_thread = VideoConvertThread(
            self.current_video_path, output_path,
            params["pixel_size"], params["num_colors"],
            params["grid"], params["outline"], mode, extra
        )
        self._convert_thread.progress.connect(self._on_video_progress)
        self._convert_thread.frame_converted.connect(self._on_video_frame_preview)
        self._convert_thread.finished.connect(self._on_video_converted)
        self._convert_thread.error.connect(self._on_convert_error)
        self._convert_thread.start()

    def _on_video_progress(self, pct, elapsed, remaining):
        self.progress_bar.setValue(pct)
        self._set_taskbar_progress(pct, True)
        self.status_label.setText(f"동영상 변환 중... {pct}%")
        self.time_label.setText(
            f"경과: {_fmt_time(elapsed)}  |  남은 시간: ~{_fmt_time(remaining)}"
        )

    def _on_video_frame_preview(self, frame):
        pix = cv2_to_qpixmap(frame)
        self.video_result_panel.image_label.set_pixmap(pix)

    def _cancel_convert(self):
        if self._convert_thread and self._convert_thread.isRunning():
            self._convert_thread.cancel()
            self.status_label.setText("변환 취소 중...")

    def _on_video_converted(self, output_path):
        self.progress_bar.setVisible(False)
        self.time_label.setText("")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.save_btn.setEnabled(True)
        self._set_taskbar_progress(100, False)

        self.video_result_panel.load_video(output_path)
        self.tab_widget.setCurrentIndex(2)

        self.history_manager.add(self.current_video_path, output_path, "video")
        self.history_widget.refresh()
        self.output_browser.refresh()
        self.status_label.setText(f"동영상 변환 완료: {os.path.basename(output_path)}")

    def _on_convert_error(self, msg):
        self.progress_bar.setVisible(False)
        self.time_label.setText("")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self._set_taskbar_progress(0, False)
        self.status_label.setText("변환 실패")
        if "취소" not in msg:
            QMessageBox.critical(self, "변환 오류", msg)

    # ─── Save ───

    def _save_result(self):
        if self.current_mode == "video":
            self.status_label.setText("동영상은 변환 시 자동 저장됩니다.")
            return
        if self.result_image is None:
            QMessageBox.information(self, "알림", "먼저 변환을 실행해주세요.")
            return

        output_dir = self.config.get("output_dir", os.path.join(get_base_dir(), "output"))
        os.makedirs(output_dir, exist_ok=True)

        ext = "." + self.config.get("image_format", "PNG").lower()
        mode = self._get_convert_mode()
        suffix = f"_{mode}" if mode != "pixel" else "_dot"

        if self._current_input_path:
            base = os.path.splitext(os.path.basename(self._current_input_path))[0]
        else:
            base = "canvas"
        base += suffix

        output_path = os.path.join(output_dir, f"{base}{ext}")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base}_{counter}{ext}")
            counter += 1

        try:
            cv2.imwrite(output_path, self.result_image)
            input_path = self._current_input_path or output_path
            self.history_manager.add(input_path, output_path, "image")
            self.history_widget.refresh()
            self.output_browser.refresh()
            self.status_label.setText(f"저장 완료: {os.path.basename(output_path)}")
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))

    def _save_result_as(self):
        if self.result_image is None:
            QMessageBox.information(self, "알림", "먼저 변환을 실행해주세요.")
            return
        ext = self.config.get("image_format", "PNG")
        path, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 저장", "",
            f"이미지 파일 (*.{ext.lower()});;모든 파일 (*.*)"
        )
        if not path:
            return
        try:
            cv2.imwrite(path, self.result_image)
            self.status_label.setText(f"저장 완료: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))

    # ─── Settings ───

    def _open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == SettingsDialog.Accepted:
            self._apply_theme()
            self.pixel_size_slider.setValue(self.config.get("pixel_size", 8))
            self.color_spin.setValue(self.config.get("num_colors", 16))
            new_dir = self.config.get("output_dir", "")
            if new_dir:
                self.output_browser.set_output_dir(new_dir)
            self.status_label.setText("설정이 저장되었습니다.")

    # ─── About ───

    def _show_about(self):
        QMessageBox.about(
            self, "ToDoT 정보",
            "<h2>ToDoT</h2>"
            "<p>이미지와 동영상을 다양한 아트 스타일로 변환</p>"
            "<p>버전 2.0.0</p>"
            "<hr>"
            "<p><b>픽셀 변환:</b> K-means, 디더링, 팔레트, NN, Edge-preserving, 슈퍼픽셀</p>"
            "<p><b>문자 아트:</b> ASCII, 한글, 유니코드 (컬러/흑백)</p>"
            "<p><b>아트 효과:</b> 하프톤, 만화, 보로노이, 로우폴리, 점묘화, 글리치</p>"
            "<p><b>복합 모드:</b> 4분할 합성</p>"
            f"<p><b>이미지:</b> {', '.join(sorted(e.upper() for e in IMAGE_EXTENSIONS))}</p>"
            f"<p><b>동영상:</b> {', '.join(sorted(e.upper() for e in VIDEO_EXTENSIONS))}</p>"
            "<p><b>CLI:</b> python src/cli.py --help</p>"
        )

    # ─── Drag & Drop ───

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            QApplication.setOverrideCursor(Qt.DragCopyCursor)

    def dragLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def dropEvent(self, event):
        QApplication.restoreOverrideCursor()
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._load_file(path)

    def closeEvent(self, event):
        if self._convert_thread and self._convert_thread.isRunning():
            self._convert_thread.cancel()
            self._convert_thread.wait(3000)
        if self._preview_thread and self._preview_thread.isRunning():
            self._preview_thread.cancel()
            self._preview_thread.wait(1000)
        self.video_original_panel.clear()
        self.video_result_panel.clear()
        self._set_taskbar_progress(0, False)
        event.accept()

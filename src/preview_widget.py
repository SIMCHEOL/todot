import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QScrollArea, QFrame, QPushButton, QSlider
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap, QPainter


def cv2_to_qpixmap(cv_img):
    if cv_img is None:
        return QPixmap()
    if len(cv_img.shape) == 2:
        h, w = cv_img.shape
        qimg = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(100, 100)
        self._pixmap = None
        self._placeholder = "여기에 이미지가 표시됩니다"

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self._update_display()

    def set_placeholder(self, text):
        self._placeholder = text
        if self._pixmap is None:
            self.setText(self._placeholder)

    def _update_display(self):
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
        else:
            self.setText(self._placeholder)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def clear_image(self):
        self._pixmap = None
        self.setText(self._placeholder)


class PreviewPanel(QFrame):
    def __init__(self, title="미리보기", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("subtitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.image_label = ImageLabel()
        layout.addWidget(self.image_label, 1)

        self.info_label = QLabel("")
        self.info_label.setObjectName("subtitleLabel")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

    def set_image(self, cv_img):
        if cv_img is not None:
            pix = cv2_to_qpixmap(cv_img)
            self.image_label.set_pixmap(pix)
            h, w = cv_img.shape[:2]
            self.info_label.setText(f"{w} × {h}")
        else:
            self.image_label.clear_image()
            self.info_label.setText("")

    def set_pixmap(self, pixmap, info=""):
        self.image_label.set_pixmap(pixmap)
        self.info_label.setText(info)

    def clear(self):
        self.image_label.clear_image()
        self.info_label.setText("")


class VideoPreviewPanel(QFrame):
    def __init__(self, title="동영상 미리보기", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("subtitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.image_label = ImageLabel()
        layout.addWidget(self.image_label, 1)

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setObjectName("secondaryBtn")
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.sliderPressed.connect(self._on_seek_start)
        self.seek_slider.sliderReleased.connect(self._on_seek_end)
        controls.addWidget(self.seek_slider, 1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("subtitleLabel")
        self.time_label.setFixedWidth(100)
        controls.addWidget(self.time_label)

        layout.addLayout(controls)

        self.info_label = QLabel("")
        self.info_label.setObjectName("subtitleLabel")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.cap = None
        self.frames = []
        self.fps = 30.0
        self.total_frames = 0
        self.current_frame = 0
        self.playing = False
        self.seeking = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)

    def load_video(self, path):
        self.stop()
        self.frames.clear()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            return False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self.total_frames <= 0 or w <= 0 or h <= 0:
            self.cap.release()
            self.cap = None
            self.info_label.setText("유효하지 않은 동영상입니다")
            return False

        self.seek_slider.setRange(0, max(0, self.total_frames - 1))
        self.info_label.setText(f"{w} × {h} | {self.fps:.1f} FPS | {self.total_frames} frames")

        self.current_frame = 0
        self._show_frame_at(0)
        return True

    def load_frames(self, frames_list, fps=30.0):
        self.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.frames = frames_list
        self.fps = fps
        self.total_frames = len(frames_list)
        self.seek_slider.setRange(0, max(0, self.total_frames - 1))
        self.current_frame = 0
        if frames_list:
            h, w = frames_list[0].shape[:2]
            self.info_label.setText(f"{w} × {h} | {fps:.1f} FPS | {len(frames_list)} frames")
            self._display_frame(frames_list[0])
        self._update_time()

    def _show_frame_at(self, idx):
        if self.frames:
            if 0 <= idx < len(self.frames):
                self._display_frame(self.frames[idx])
        elif self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = self.cap.read()
            if ret:
                self._display_frame(frame)
        self.current_frame = idx
        if not self.seeking:
            self.seek_slider.setValue(idx)
        self._update_time()

    def _display_frame(self, frame):
        pix = cv2_to_qpixmap(frame)
        self.image_label.set_pixmap(pix)

    def _next_frame(self):
        next_idx = self.current_frame + 1
        if next_idx >= self.total_frames:
            next_idx = 0
        self._show_frame_at(next_idx)

    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def play(self):
        if self.total_frames <= 0:
            return
        self.playing = True
        self.play_btn.setText("⏸")
        interval = max(1, int(1000 / self.fps))
        self.timer.start(interval)

    def pause(self):
        self.playing = False
        self.play_btn.setText("▶")
        self.timer.stop()

    def stop(self):
        self.pause()
        self.current_frame = 0

    def _on_seek_start(self):
        self.seeking = True

    def _on_seek_end(self):
        self.seeking = False
        self._show_frame_at(self.seek_slider.value())

    def _update_time(self):
        if self.fps <= 0:
            return
        cur_sec = self.current_frame / self.fps
        total_sec = self.total_frames / self.fps
        self.time_label.setText(
            f"{int(cur_sec // 60)}:{int(cur_sec % 60):02d} / "
            f"{int(total_sec // 60)}:{int(total_sec % 60):02d}"
        )

    def clear(self):
        self.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.frames.clear()
        self.image_label.clear_image()
        self.info_label.setText("")
        self.time_label.setText("0:00 / 0:00")
        self.seek_slider.setValue(0)

    def closeEvent(self, event):
        self.stop()
        if self.cap:
            self.cap.release()
        super().closeEvent(event)

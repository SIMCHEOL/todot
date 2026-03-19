import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QLineEdit, QGroupBox, QFormLayout,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from config_manager import ConfigManager
from styles import get_theme_names


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("설정")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        output_group = QGroupBox("출력 설정")
        output_layout = QFormLayout(output_group)
        output_layout.setSpacing(10)

        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG", "JPG", "BMP", "TIFF", "WEBP"])
        output_layout.addRow("이미지 출력 형식:", self.image_format_combo)

        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["MP4", "AVI"])
        output_layout.addRow("동영상 출력 형식:", self.video_format_combo)

        dir_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        dir_row.addWidget(self.output_dir_edit, 1)
        browse_btn = QPushButton("찾아보기")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_row.addWidget(browse_btn)
        output_layout.addRow("출력 폴더:", dir_row)

        layout.addWidget(output_group)

        appearance_group = QGroupBox("외관 설정")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(get_theme_names())
        appearance_layout.addRow("테마:", self.theme_combo)

        layout.addWidget(appearance_group)

        convert_group = QGroupBox("변환 기본값")
        convert_layout = QFormLayout(convert_group)
        convert_layout.setSpacing(10)

        self.pixel_size_combo = QComboBox()
        self.pixel_size_combo.addItems(["2", "4", "8", "12", "16", "24", "32"])
        convert_layout.addRow("기본 픽셀 크기:", self.pixel_size_combo)

        self.color_count_combo = QComboBox()
        self.color_count_combo.addItems(["4", "8", "16", "32", "64", "128", "256"])
        convert_layout.addRow("기본 색상 수:", self.color_count_combo)

        layout.addWidget(convert_group)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("저장")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _load_values(self):
        img_fmt = self.config.get("image_format", "PNG")
        idx = self.image_format_combo.findText(img_fmt)
        if idx >= 0:
            self.image_format_combo.setCurrentIndex(idx)

        vid_fmt = self.config.get("video_format", "MP4")
        idx = self.video_format_combo.findText(vid_fmt)
        if idx >= 0:
            self.video_format_combo.setCurrentIndex(idx)

        self.output_dir_edit.setText(self.config.get("output_dir", ""))

        theme = self.config.get("theme", "Catppuccin Mocha")
        idx = self.theme_combo.findText(theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        px = str(self.config.get("pixel_size", 8))
        idx = self.pixel_size_combo.findText(px)
        if idx >= 0:
            self.pixel_size_combo.setCurrentIndex(idx)

        nc = str(self.config.get("num_colors", 16))
        idx = self.color_count_combo.findText(nc)
        if idx >= 0:
            self.color_count_combo.setCurrentIndex(idx)

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "출력 폴더 선택", self.output_dir_edit.text()
        )
        if directory:
            self.output_dir_edit.setText(directory)

    def _save_and_close(self):
        self.config.set_many({
            "image_format": self.image_format_combo.currentText(),
            "video_format": self.video_format_combo.currentText(),
            "output_dir": self.output_dir_edit.text(),
            "theme": self.theme_combo.currentText(),
            "pixel_size": int(self.pixel_size_combo.currentText()),
            "num_colors": int(self.color_count_combo.currentText()),
        })
        self.accept()

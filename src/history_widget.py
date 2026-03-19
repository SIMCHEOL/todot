import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QImage
import cv2

from history_manager import HistoryManager


class HistoryWidget(QWidget):
    """Compact history list for embedding inside a tab or panel."""
    item_clicked = pyqtSignal(str, str)

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("최근 작업 히스토리")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        clear_btn = QPushButton("지우기")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setFixedHeight(26)
        clear_btn.clicked.connect(self._clear_history)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(40, 40))
        self.list_widget.setSpacing(2)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, 1)

    def refresh(self):
        self.list_widget.clear()
        for entry in self.history_manager.get_all():
            item = QListWidgetItem()
            filename = os.path.basename(entry.input_path)
            timestamp = time.strftime("%m/%d %H:%M", time.localtime(entry.timestamp))
            icon = "🎬" if entry.media_type == "video" else "🖼"
            item.setText(f"{icon} {filename}\n   {timestamp}")
            item.setData(Qt.UserRole, (entry.input_path, entry.output_path))
            item.setSizeHint(QSize(-1, 46))

            if entry.media_type == "image" and os.path.exists(entry.output_path):
                try:
                    img = cv2.imread(entry.output_path)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        h, w = img.shape[:2]
                        qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
                        pix = QPixmap.fromImage(qimg).scaled(
                            40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        item.setIcon(QIcon(pix))
                except Exception:
                    pass

            self.list_widget.addItem(item)

        if self.list_widget.count() == 0:
            empty = QListWidgetItem("아직 작업 기록이 없습니다")
            empty.setFlags(Qt.NoItemFlags)
            empty.setTextAlignment(Qt.AlignCenter)
            self.list_widget.addItem(empty)

    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            self.item_clicked.emit(data[0], data[1])

    def _clear_history(self):
        self.history_manager.clear()
        self.refresh()

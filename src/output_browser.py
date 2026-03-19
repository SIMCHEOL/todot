import os
import time
import cv2
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QSizePolicy, QAbstractItemView, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QFileSystemWatcher, QUrl, QMimeData
from PyQt5.QtGui import QIcon, QPixmap, QImage, QDrag

from converter import is_image, is_video


VIEW_THUMBNAIL = 0
VIEW_THUMBNAIL_NAME = 1
VIEW_DETAIL = 2


class DragOutListWidget(QListWidget):
    """QListWidget that supports dragging files OUT to Explorer/desktop
    but blocks internal drag-drop rearrangement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, supportedActions):
        items = self.selectedItems()
        if not items:
            return

        paths = []
        for item in items:
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                paths.append(path)

        if not paths:
            return

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(p) for p in paths])

        drag = QDrag(self)
        drag.setMimeData(mime)

        thumb = items[0].icon().pixmap(48, 48)
        if not thumb.isNull():
            drag.setPixmap(thumb)

        drag.exec_(Qt.CopyAction)


class OutputBrowser(QWidget):
    file_selected = pyqtSignal(str)
    file_double_clicked = pyqtSignal(str)

    def __init__(self, output_dir, parent=None):
        super().__init__(parent)
        self.output_dir = output_dir
        self.view_mode = VIEW_THUMBNAIL_NAME
        self._thumb_cache = {}
        self._setup_ui()

        self.watcher = QFileSystemWatcher(self)
        if os.path.isdir(output_dir):
            self.watcher.addPath(output_dir)
        self.watcher.directoryChanged.connect(self._on_dir_changed)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.timeout.connect(self.refresh)

        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("결과물")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        self.view_btn = QPushButton("보기 ▾")
        self.view_btn.setObjectName("secondaryBtn")
        self.view_btn.setFixedHeight(28)
        self.view_btn.setMinimumWidth(80)
        self.view_btn.clicked.connect(self._show_view_menu)
        header.addWidget(self.view_btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setToolTip("새로고침")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        self.list_widget = DragOutListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget, 1)

        self.info_label = QLabel("0개 파일")
        self.info_label.setObjectName("subtitleLabel")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

    def set_output_dir(self, directory):
        if self.output_dir and os.path.isdir(self.output_dir):
            try:
                self.watcher.removePath(self.output_dir)
            except Exception:
                pass
        self.output_dir = directory
        if os.path.isdir(directory):
            self.watcher.addPath(directory)
        self._thumb_cache.clear()
        self.refresh()

    def _on_dir_changed(self, _path):
        self._refresh_timer.start()

    def refresh(self):
        self.list_widget.clear()
        self._thumb_cache.clear()

        if not os.path.isdir(self.output_dir):
            self.info_label.setText("폴더 없음")
            return

        files = []
        for f in os.listdir(self.output_dir):
            fp = os.path.join(self.output_dir, f)
            if os.path.isfile(fp) and (is_image(fp) or is_video(fp)):
                mtime = os.path.getmtime(fp)
                size = os.path.getsize(fp)
                files.append((f, fp, mtime, size))

        files.sort(key=lambda x: x[2], reverse=True)

        if self.view_mode == VIEW_THUMBNAIL:
            self.list_widget.setViewMode(QListWidget.IconMode)
            self.list_widget.setIconSize(QSize(88, 88))
            self.list_widget.setGridSize(QSize(100, 100))
            self.list_widget.setWrapping(True)
            self.list_widget.setResizeMode(QListWidget.Adjust)
        elif self.view_mode == VIEW_THUMBNAIL_NAME:
            self.list_widget.setViewMode(QListWidget.IconMode)
            self.list_widget.setIconSize(QSize(64, 64))
            self.list_widget.setGridSize(QSize(145, 108))
            self.list_widget.setWrapping(True)
            self.list_widget.setResizeMode(QListWidget.Adjust)
        else:
            self.list_widget.setViewMode(QListWidget.ListMode)
            self.list_widget.setIconSize(QSize(36, 36))
            self.list_widget.setGridSize(QSize(-1, -1))
            self.list_widget.setWrapping(False)

        for name, fp, mtime, size in files:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, fp)

            if self.view_mode == VIEW_THUMBNAIL:
                item.setText("")
                item.setToolTip(name)
            elif self.view_mode == VIEW_THUMBNAIL_NAME:
                display = name if len(name) <= 18 else name[:15] + "..."
                item.setText(display)
                item.setToolTip(name)
            else:
                date_str = time.strftime("%m/%d %H:%M", time.localtime(mtime))
                size_str = self._format_size(size)
                item.setText(f"{name}\n  {date_str}  |  {size_str}")
                item.setSizeHint(QSize(-1, 52))

            thumb = self._get_thumbnail(fp)
            if thumb:
                item.setIcon(QIcon(thumb))

            self.list_widget.addItem(item)

        self.info_label.setText(f"{len(files)}개 파일")

    def _get_thumbnail(self, path):
        if path in self._thumb_cache:
            return self._thumb_cache[path]

        pix = None
        try:
            if is_image(path):
                img = cv2.imread(path)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    h, w = img.shape[:2]
                    qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
                    pix = QPixmap.fromImage(qimg).scaled(
                        80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
            elif is_video(path):
                cap = cv2.VideoCapture(path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = frame.shape[:2]
                    qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)
                    pix = QPixmap.fromImage(qimg).scaled(
                        80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
        except Exception:
            pass

        if pix:
            self._thumb_cache[path] = pix
        return pix

    def _format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def _on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.file_selected.emit(path)

    def _on_item_double_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.file_double_clicked.emit(path)

    def _show_view_menu(self):
        menu = QMenu(self)
        labels = ["썸네일만 보기", "썸네일 + 이름", "자세히 보기"]
        for i, label in enumerate(labels):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(i == self.view_mode)
            action.setData(i)
            action.triggered.connect(self._change_view_mode)
            menu.addAction(action)
        menu.exec_(self.view_btn.mapToGlobal(self.view_btn.rect().bottomLeft()))

    def _change_view_mode(self):
        action = self.sender()
        if action:
            self.view_mode = action.data()
            self.refresh()

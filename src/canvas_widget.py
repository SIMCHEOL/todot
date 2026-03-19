import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QColorDialog, QSlider, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import (
    QPainter, QImage, QColor, QPen, QPixmap, QCursor
)


class DrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.canvas_image = QImage(800, 600, QImage.Format_RGB32)
        self.canvas_image.fill(QColor(255, 255, 255))

        self.drawing = False
        self.brush_color = QColor(0, 0, 0)
        self.brush_size = 4
        self.eraser_mode = False
        self.last_point = QPoint()

        self.undo_stack = []
        self.redo_stack = []
        self._save_state()

        self.setCursor(Qt.CrossCursor)

    def _save_state(self):
        self.undo_stack.append(self.canvas_image.copy())
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.canvas_image = self.undo_stack[-1].copy()
            self.update()

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.canvas_image = state.copy()
            self.update()

    def clear_canvas(self):
        self._save_state()
        self.canvas_image.fill(QColor(255, 255, 255))
        self.update()

    def set_brush_color(self, color):
        self.brush_color = color
        self.eraser_mode = False

    def set_eraser(self, enabled):
        self.eraser_mode = enabled
        self.setCursor(Qt.CrossCursor)

    def _canvas_rect(self):
        cw, ch = self.canvas_image.width(), self.canvas_image.height()
        ww, wh = self.width(), self.height()
        scale = min(ww / cw, wh / ch)
        sw, sh = int(cw * scale), int(ch * scale)
        x = (ww - sw) // 2
        y = (wh - sh) // 2
        return QRect(x, y, sw, sh), scale

    def _widget_to_canvas(self, pos):
        rect, scale = self._canvas_rect()
        cx = (pos.x() - rect.x()) / scale
        cy = (pos.y() - rect.y()) / scale
        return QPoint(int(cx), int(cy))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        rect, _ = self._canvas_rect()

        painter.fillRect(self.rect(), QColor(30, 30, 46) if self.palette().window().color().lightness() < 128 else QColor(220, 224, 232))

        painter.drawImage(rect, self.canvas_image)

        pen = QPen(QColor(100, 100, 100), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(-1, -1, 0, 0))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = self._widget_to_canvas(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and (event.buttons() & Qt.LeftButton):
            current = self._widget_to_canvas(event.pos())
            painter = QPainter(self.canvas_image)
            if self.eraser_mode:
                pen = QPen(QColor(255, 255, 255), self.brush_size * 3,
                           Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else:
                pen = QPen(self.brush_color, self.brush_size,
                           Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, current)
            painter.end()
            self.last_point = current
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self._save_state()

    def get_image_as_numpy(self):
        img = self.canvas_image.convertToFormat(QImage.Format_RGB888)
        w, h = img.width(), img.height()
        ptr = img.bits()
        if ptr is None:
            return None
        ptr.setsize(h * w * 3)
        arr = np.array(ptr).reshape(h, w, 3).copy()
        import cv2
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    def set_canvas_size(self, width, height):
        new_image = QImage(width, height, QImage.Format_RGB32)
        new_image.fill(QColor(255, 255, 255))
        painter = QPainter(new_image)
        painter.drawImage(0, 0, self.canvas_image)
        painter.end()
        self.canvas_image = new_image
        self._save_state()
        self.update()


class CanvasToolbar(QFrame):
    def __init__(self, canvas: DrawingCanvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.color_btn = QPushButton("  색상  ")
        self.color_btn.setFixedHeight(32)
        self.color_btn.setStyleSheet(
            f"background-color: {self.canvas.brush_color.name()}; "
            "border-radius: 6px; min-width: 50px; color: white; font-weight: bold;"
        )
        self.color_btn.clicked.connect(self._pick_color)
        layout.addWidget(self.color_btn)

        self.brush_btn = QPushButton("✏ 브러시")
        self.brush_btn.setCheckable(True)
        self.brush_btn.setChecked(True)
        self.brush_btn.setObjectName("secondaryBtn")
        self.brush_btn.clicked.connect(lambda: self._set_tool("brush"))
        layout.addWidget(self.brush_btn)

        self.eraser_btn = QPushButton("◻ 지우개")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.setObjectName("secondaryBtn")
        self.eraser_btn.clicked.connect(lambda: self._set_tool("eraser"))
        layout.addWidget(self.eraser_btn)

        layout.addWidget(QLabel("크기:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 30)
        self.size_slider.setValue(4)
        self.size_slider.setFixedWidth(120)
        self.size_slider.valueChanged.connect(self._size_changed)
        layout.addWidget(self.size_slider)
        self.size_label = QLabel("4")
        self.size_label.setFixedWidth(24)
        layout.addWidget(self.size_label)

        layout.addStretch()

        undo_btn = QPushButton("↩ 실행 취소")
        undo_btn.setObjectName("secondaryBtn")
        undo_btn.setToolTip("마지막 작업을 취소합니다 (Ctrl+Z)")
        undo_btn.clicked.connect(self.canvas.undo)
        layout.addWidget(undo_btn)

        redo_btn = QPushButton("↪ 다시 실행")
        redo_btn.setObjectName("secondaryBtn")
        redo_btn.setToolTip("취소한 작업을 다시 실행합니다 (Ctrl+Y)")
        redo_btn.clicked.connect(self.canvas.redo)
        layout.addWidget(redo_btn)

        clear_btn = QPushButton("✕ 전체 지우기")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.setToolTip("캔버스를 모두 지웁니다")
        clear_btn.clicked.connect(self.canvas.clear_canvas)
        layout.addWidget(clear_btn)

    def _pick_color(self):
        color = QColorDialog.getColor(self.canvas.brush_color, self, "브러시 색상 선택")
        if color.isValid():
            self.canvas.set_brush_color(color)
            self._update_color_btn(color)
            self.brush_btn.setChecked(True)
            self.eraser_btn.setChecked(False)

    def _update_color_btn(self, color):
        lum = color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
        text_color = "#000000" if lum > 140 else "#ffffff"
        self.color_btn.setStyleSheet(
            f"background-color: {color.name()}; "
            f"border-radius: 6px; min-width: 50px; color: {text_color}; font-weight: bold;"
        )

    def _set_tool(self, tool):
        if tool == "brush":
            self.canvas.set_eraser(False)
            self.brush_btn.setChecked(True)
            self.eraser_btn.setChecked(False)
        else:
            self.canvas.set_eraser(True)
            self.brush_btn.setChecked(False)
            self.eraser_btn.setChecked(True)

    def _size_changed(self, value):
        self.canvas.brush_size = value
        self.size_label.setText(str(value))

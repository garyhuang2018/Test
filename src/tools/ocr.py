import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QWidget, QHBoxLayout, QSlider,
                             QGridLayout, QGroupBox, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QMutex, QMutexLocker
import sys

import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QWidget, QHBoxLayout, QGroupBox)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint


class OrangeDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cap = None
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.roi_rect = None
        self.frame_mutex = QMutex()
        self.current_frame = None  # 新增帧缓存
        self.init_ui()
        self.setup_color_params()

    def update_display(self):
        """安全更新显示的方法"""
        if self.current_frame is not None:
            try:
                # 转换为RGB格式
                display_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = display_frame.shape
                bytes_per_line = ch * w
                q_img = QImage(display_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.cam_label.setPixmap(
                    QPixmap.fromImage(q_img).scaled(
                        self.cam_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )

            except Exception as e:
                print(f"显示更新失败: {str(e)}")

    def init_ui(self):
        self.setWindowTitle('智能区域检测系统')
        self.setGeometry(300, 300, 1400, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()

        # ===== 左侧摄像头区域 =====
        left_panel = QVBoxLayout()

        # 摄像头预览（支持鼠标交互）
        self.cam_label = InteractiveLabel()
        self.cam_label.setMinimumSize(800, 600)
        self.cam_label.setStyleSheet("""
            QLabel {
                border: 2px solid #666;
                background: #333;
                qproperty-alignment: AlignCenter;
                font: bold 18px;
                color: #fff;
            }
        """)
        self.cam_label.mouse_pressed.connect(self.start_drawing)
        self.cam_label.mouse_moved.connect(self.keep_drawing)
        self.cam_label.mouse_released.connect(self.finish_drawing)
        left_panel.addWidget(self.cam_label)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.btn_start = self.create_button("▶ 启动摄像头", "#4CAF50")
        self.btn_reset = self.create_button("🔄 重置区域", "#2196F3")
        self.btn_stop = self.create_button("⏹ 停止检测", "#f44336")
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_stop)
        left_panel.addLayout(btn_layout)

        # ===== 右侧控制面板 =====
        control_panel = QVBoxLayout()

        # 使用说明
        help_group = QGroupBox("操作指南")
        help_group.setStyleSheet("QGroupBox { font: bold 16px; }")
        help_layout = QVBoxLayout()
        help_text = QLabel("""
            <b>使用步骤：</b>
            <ol>
            <li>启动摄像头</li>
            <li>按住鼠标左键在画面中绘制检测区域（绿色大框）</li>
            <li>系统将在划定区域内自动检测橙色灯光</li>
            <li>点击重置区域可重新绘制</li>
            </ol>
            <b>显示说明：</b>
            <ul>
            <li>绿色大框：用户绘制的检测范围</li>
            <li>绿色小框：检测到的橙色灯区域</li>
            <li>红色提示：未检测到有效区域</li>
            </ul>
        """)
        help_text.setStyleSheet("font: 14px;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        control_panel.addWidget(help_group)

        main_layout.addLayout(left_panel, 70)
        main_layout.addLayout(control_panel, 30)
        main_widget.setLayout(main_layout)

        # 事件绑定
        self.btn_start.clicked.connect(self.toggle_camera)
        self.btn_reset.clicked.connect(self.reset_roi)
        self.btn_stop.clicked.connect(self.stop_camera)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)

    def create_button(self, text, color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                padding: 12px 24px;
                font: bold 14px;
                border-radius: 5px;
                min-width: 120px;
                background: {color};
                color: white;
            }}
            QPushButton:hover {{ background: {color}88; }}
        """)
        return btn

    def setup_color_params(self):
        # 橙色检测参数（可根据需要调整）
        self.lower_orange = np.array([10, 100, 100])
        self.upper_orange = np.array([25, 255, 255])

    def start_drawing(self, pos):
        if not self.cap:
            QMessageBox.warning(self, "警告", "请先启动摄像头!")
            return
        with QMutexLocker(self.frame_mutex):  # 加锁
            print('start drawing')
            self.drawing = True
            self.start_point = pos
            self.end_point = pos
            self.roi_rect = None

    def keep_drawing(self, pos):
        if self.drawing and self.cap:
            try:
                with QMutexLocker(self.frame_mutex):
                    print('keep drawing')
                    self.end_point = pos
                    # 触发显示更新
                    self.update_display()  # 现在此方法已定义
            except Exception as e:
                print(f"持续绘制异常: {str(e)}")
                self.reset_drawing()

    def finish_drawing(self):
        """ 参考take_photo的区域保存逻辑 """
        if self.drawing:
            try:
                with QMutexLocker(self.frame_mutex):
                    print('finish drawing')
                    self.drawing = False
                    if self.start_point != self.end_point:
                        x1, y1 = self.start_point.x(), self.start_point.y()
                        x2, y2 = self.end_point.x(), self.end_point.y()
                        # 确保最小有效区域
                        if abs(x2-x1)<10 or abs(y2-y1)<10:
                            self.roi_rect = None
                            return
                        self.roi_rect = (
                            min(x1, x2),
                            min(y1, y2),
                            abs(x2 - x1),
                            abs(y2 - y1))
                    self.update_display()  # 现在此方法已定义
            except Exception as e:
                print(f"完成绘制异常: {str(e)}")
                self.reset_drawing()

    def reset_roi(self):
        self.roi_rect = None
        self.update_display()

    def toggle_camera(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
            self.timer.start(30)
            self.btn_start.setText("📸 摄像头运行中")
        else:
            self.stop_camera()

    def stop_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.timer.stop()
        self.cam_label.clear()
        self.btn_start.setText("▶ 启动摄像头")

    def process_frame(self):
        if not self.cap: return

        try:
            with QMutexLocker(self.frame_mutex):
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    return

                # 直接使用BGR格式处理
                display_frame = frame.copy()

                # 绘制绿框（BGR颜色空间）
                if self.drawing:
                    x1 = int(self.start_point.x())
                    y1 = int(self.start_point.y())
                    x2 = int(self.end_point.x())
                    y2 = int(self.end_point.y())
                    cv2.rectangle(display_frame,
                                  (x1, y1), (x2, y2),
                                  (0, 255, 0), 2)  # BGR格式绿色

                # 转换为RGB用于显示
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # 强制刷新显示
                self.cam_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                    self.cam_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                self.cam_label.repaint()  # 立即重绘

        except Exception as e:
            print(f"[CRITICAL] 帧处理失败: {str(e)}")
            self.stop_camera()


    def get_scaled_roi(self, frame_shape):
        """增强型坐标转换"""
        if not self.roi_rect or frame_shape[0] * frame_shape[1] == 0:
            return (0, 0, 0, 0)

        try:
            # 获取标签实际显示尺寸
            label_w = max(1, self.cam_label.width())
            label_h = max(1, self.cam_label.height())

            # 计算缩放比例
            scale_x = frame_shape[1] / label_w
            scale_y = frame_shape[0] / label_h

            # 转换坐标
            x = int(self.roi_rect[0] * scale_x)
            y = int(self.roi_rect[1] * scale_y)
            w = int(self.roi_rect[2] * scale_x)
            h = int(self.roi_rect[3] * scale_y)

            # 严格边界检查
            x = np.clip(x, 0, frame_shape[1] - 1)
            y = np.clip(y, 0, frame_shape[0] - 1)
            w = np.clip(w, 10, frame_shape[1] - x)
            h = np.clip(h, 10, frame_shape[0] - y)

            return (x, y, w, h)
        except Exception as e:
            print(f"坐标转换错误: {str(e)}")
            return (0, 0, 0, 0)

    def detect_orange(self, roi_frame):
        """在ROI区域内检测橙色区域"""
        hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_orange, self.upper_orange)

        # 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # 寻找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 100:  # 过滤小区域
                x, y, w, h = cv2.boundingRect(cnt)
                detected.append((x, y, w, h))

        return detected if detected else None

    def draw_user_roi(self, frame):
        """绘制用户定义的ROI区域"""
        if self.roi_rect:
            x, y, w, h = self.get_scaled_roi(frame.shape)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        elif self.drawing:
            # 实时绘制临时矩形
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            cv2.rectangle(frame,
                          (int(x1), int(y1)),
                          (int(x2), int(y2)),
                          (0, 255, 0), 2)

    def display_image(self, frame):
        """将OpenCV图像转换为Qt格式显示"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.cam_label.width(), self.cam_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))


class InteractiveLabel(QLabel):
    mouse_pressed = pyqtSignal(QPoint)
    mouse_moved = pyqtSignal(QPoint)
    mouse_released = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._last_valid_pos = QPoint()  # 添加最后有效坐标缓存

    def mousePressEvent(self, event):
        try:
            super().mousePressEvent(event)  # 关键修复1：调用父类方法
            if event.button() == Qt.LeftButton:
                pos = self._validate_position(event.pos())
                self.mouse_pressed.emit(pos)
        except Exception as e:
            print(f"MousePress Error: {str(e)}")

    def mouseMoveEvent(self, event):
        try:
            super().mouseMoveEvent(event)  # 关键修复2：保持事件传递
            pos = self._validate_position(event.pos())
            self._last_valid_pos = pos
            self.mouse_moved.emit(pos)
        except Exception as e:
            print(f"MouseMove Error: {str(e)}")
            self.mouse_moved.emit(self._last_valid_pos)

    def mouseReleaseEvent(self, event):
        try:
            super().mouseReleaseEvent(event)  # 关键修复3：完整事件链
            if event.button() == Qt.LeftButton:
                pos = self._validate_position(event.pos())
                self.mouse_released.emit()
        except Exception as e:
            print(f"MouseRelease Error: {str(e)}")

    def _validate_position(self, pos):
        """ 坐标安全验证 """
        x = max(0, min(pos.x(), self.width()-1))
        y = max(0, min(pos.y(), self.height()-1))
        return QPoint(x, y)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    detector = OrangeDetector()
    detector.show()
    app.exec_()
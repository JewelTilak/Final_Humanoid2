# Owner: Mohit
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets
import sys, os, time, math, random, subprocess

# ----------------------------- Worker for background tasks -----------------------------
class WorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    message = QtCore.pyqtSignal(str)

class FakeLongTask(QtCore.QRunnable):
    def __init__(self, duration=5, message_prefix="Working"):
        super().__init__()
        self.duration = duration
        self.signals = WorkerSignals()
        self.message_prefix = message_prefix

    def run(self):
        steps = max(10, int(self.duration * 5))
        for i in range(steps + 1):
            pct = int(i * 100 / steps)
            self.signals.progress.emit(pct)
            if i % (max(1, steps // 5)) == 0:
                self.signals.message.emit(f"{self.message_prefix}... {pct}%")
            time.sleep(self.duration / steps)
        self.signals.message.emit(f"{self.message_prefix} complete.")
        self.signals.finished.emit()


# ----------------------------- Space Background -----------------------------
class SpaceBackground(QtWidgets.QWidget):
    def __init__(self, star_count=145, parent=None):
        super().__init__(parent)
        self.star_count = star_count
        self.stars = []
        for _ in range(star_count):
            x = random.randint(0, 1920)
            y = random.randint(0, 1080)
            base_brightness = random.randint(180, 255)
            phase = random.random() * math.pi * 2
            self.stars.append([x, y, base_brightness, phase])
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0))
        grad = QtGui.QLinearGradient(self.width() * 0.5, 0, self.width(), self.height())
        grad.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        grad.setColorAt(1.0, QtGui.QColor(100, 0, 160, 40))
        p.fillRect(self.rect(), grad)
        for x, y, base_brightness, phase in self.stars:
            brightness = base_brightness + 50 * math.sin(time.time() * 0.8 + phase)
            brightness = max(100, min(255, int(brightness)))
            p.setPen(QtGui.QColor(brightness, brightness, brightness))
            p.drawPoint(x % self.width(), y % self.height())


# ----------------------------- Glow Button -----------------------------
class GlowButton(QtWidgets.QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(110)
        self.setMinimumWidth(500)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(QtGui.QColor(170, 0, 255, 160))
        self.setGraphicsEffect(self.shadow)

        self._scale = 1.0
        self.anim_group = QtCore.QParallelAnimationGroup(self)
        self.blur_anim = QtCore.QPropertyAnimation(self.shadow, b"blurRadius")
        self.scale_anim = QtCore.QPropertyAnimation(self, b"_scale_prop")

        for anim in (self.blur_anim, self.scale_anim):
            anim.setDuration(220)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.anim_group.addAnimation(self.blur_anim)
        self.anim_group.addAnimation(self.scale_anim)

        self.setStyleSheet(self.base_stylesheet())

    def get_scale(self):
        return self._scale

    def set_scale(self, v):
        self._scale = v
        self.setStyleSheet(self.base_stylesheet(scale=v))

    _scale_prop = QtCore.pyqtProperty(float, fget=get_scale, fset=set_scale)

    def enterEvent(self, e):
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(36)
        self.scale_anim.setStartValue(self._scale)
        self.scale_anim.setEndValue(1.03)
        self.anim_group.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.blur_anim.setStartValue(self.shadow.blurRadius())
        self.blur_anim.setEndValue(0)
        self.scale_anim.setStartValue(self._scale)
        self.scale_anim.setEndValue(1.0)
        self.anim_group.start()
        super().leaveEvent(e)

    def base_stylesheet(self, scale=1.0):
        border = "rgba(170,0,255,0.3)"
        text_color = "rgb(240,230,255)"
        return f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(40,0,60,200), stop:1 rgba(80,0,100,240));
    border: 2px solid {border};
    border-radius: 18px;
    padding: 10px 18px;
    color: {text_color};
    font-size: 24px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-align: center;
    transform: scale({scale});
}}
QPushButton:pressed {{ transform: scale({max(0.98, scale - 0.02)}); }}
"""


# ----------------------------- AURA Core -----------------------------
class AuraCore(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(540, 540)
        self._color = QtGui.QColor(38, 103, 255)
        self._opacity = 180
        self._scale = 1.0
        self.phase = 0.0
        self.speed = 0.04

        self.anim_timer = QtCore.QTimer(self)
        self.anim_timer.timeout.connect(self.animate_pulse)
        self.anim_timer.start(30)

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(self._scale, self._scale)
        p.translate(-self.width() / 2, -self.height() / 2)

        r = self.width() / 2
        brightness_factor = 1.0 + ((self._scale - 1.0) * 2.5)
        brightness_factor = min(1.8, max(0.6, brightness_factor))

        glow_color = QtGui.QColor(
            min(int(self._color.red() * brightness_factor), 255),
            min(int(self._color.green() * brightness_factor), 255),
            min(int(self._color.blue() * brightness_factor), 255)
        )

        grad = QtGui.QRadialGradient(QtCore.QPointF(r, r), r)
        c = QtGui.QColor(glow_color)
        c.setAlpha(int(self._opacity))
        grad.setColorAt(0.0, c)
        grad.setColorAt(0.5, QtGui.QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 180))
        grad.setColorAt(0.8, QtGui.QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 80))
        grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))

        p.setBrush(QtGui.QBrush(grad))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QRectF(0, 0, self.width(), self.height()))

    def animate_pulse(self):
        self.phase += self.speed
        self._scale = 1.0 + 0.12 * math.sin(self.phase)
        self._opacity = 130 + 110 * (1 + math.sin(self.phase)) / 2
        self.update()

    def pulse_react(self, color: QtGui.QColor):
        self._color = color
        anim = QtCore.QPropertyAnimation(self, b"geometry")
        anim.setDuration(600)
        start_rect = self.geometry()
        end_rect = QtCore.QRect(start_rect.x() - 25, start_rect.y() - 25,
                                start_rect.width() + 50, start_rect.height() + 50)
        anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)
        anim.finished.connect(lambda: self.reset_pulse(start_rect))
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def reset_pulse(self, rect):
        anim = QtCore.QPropertyAnimation(self, b"geometry")
        anim.setDuration(800)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        anim.setStartValue(self.geometry())
        anim.setEndValue(rect)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)


# ----------------------------- Main Window -----------------------------
class AuraMain(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AURA — Interface")
        self.resize(1280, 800)

        self.background = SpaceBackground()
        self.setCentralWidget(self.background)

        self.overlay = QtWidgets.QWidget(self.background)
        self.overlay.setGeometry(self.background.rect())
        self.overlay.raise_()

        layout = QtWidgets.QVBoxLayout(self.overlay)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        header = self.header_widget()
        layout.addWidget(header, alignment=QtCore.Qt.AlignHCenter)

        content = self.center_controls()
        layout.addWidget(content, alignment=QtCore.Qt.AlignHCenter)

        # Status label
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 600;
            color: rgba(150,200,255,0.8);
            letter-spacing: 2px;
            text-shadow: 0 0 25px rgba(100,160,255,0.6);
        """)
        layout.addWidget(self.status_label, alignment=QtCore.Qt.AlignHCenter)

        self.background.installEventFilter(self)
        self.threadpool = QtCore.QThreadPool()
        self.showMaximized()

    def eventFilter(self, s, e):
        if e.type() == QtCore.QEvent.Resize:
            self.overlay.setGeometry(self.background.rect())
        return super().eventFilter(s, e)

    def header_widget(self):
        w = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(w)
        title = QtWidgets.QLabel("AURA")
        title.setFont(QtGui.QFont("Segoe UI", 110, QtGui.QFont.Bold))
        title.setStyleSheet("""
            color: #A020F0;
            letter-spacing: 10px;
            text-shadow:
                0 0 20px #2667FF,
                0 0 50px #2667FF,
                0 0 90px #2667FF,
                0 0 140px #2667FF,
                0 0 200px #2667FF;
        """)
        title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        h.addWidget(title)
        h.addStretch()
        return w

    def center_controls(self):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setSpacing(100)
        layout.setContentsMargins(220, 40, 60, 40)

        self.aura_core = AuraCore()
        layout.addWidget(self.aura_core, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        btn_col = QtWidgets.QVBoxLayout()
        btn_col.setSpacing(25)
        btn_col.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.btn_start = GlowButton("🧠  Start recognition")
        self.btn_train = GlowButton("⚙️  Train data")
        self.btn_manage = GlowButton("📁  Manage dataset")
        self.btn_listen = GlowButton("🎧  Listen")
        self.btn_exit = GlowButton("⏻  Exit")

        for b in [self.btn_start, self.btn_train, self.btn_manage, self.btn_listen]:
            btn_col.addWidget(b)

        layout.addWidget(self.aura_core, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout.addSpacing(300)
        layout.addLayout(btn_col)

        self.btn_exit.setFixedSize(160, 60)
        self.btn_exit.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(100,0,60,220), stop:1 rgba(200,0,100,255));
            border: 2px solid rgba(255,120,120,0.6);
            border-radius: 14px;
            color: rgb(255,230,230);
            font-size: 22px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(150,0,80,240), stop:1 rgba(255,80,80,255));
        }
        """)

        exit_container = QtWidgets.QWidget(self.overlay)
        exit_layout = QtWidgets.QHBoxLayout(exit_container)
        exit_layout.setContentsMargins(0, 0, 40, 40)
        exit_layout.addStretch()
        exit_layout.addWidget(self.btn_exit, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        exit_container.setGeometry(0, 0, self.overlay.width(), self.overlay.height())
        exit_container.raise_()
        self.overlay.resizeEvent = lambda e: exit_container.setGeometry(0, 0, self.overlay.width(), self.overlay.height())

        self.btn_exit.clicked.connect(QtWidgets.QApplication.quit)
        return container


# ----------------------------- Entrypoint -----------------------------
def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    w = AuraMain()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

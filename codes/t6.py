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
    def __init__(self, star_count=2005, parent=None):
        super().__init__(parent)
        self.star_count = star_count
        self.stars = []
        for _ in range(star_count):
            x = random.uniform(0, 1920)
            y = random.uniform(0, 1080)
            base_brightness = random.randint(160, 255)
            phase = random.random() * math.pi * 2
            size = random.choice([1, 1, 2])
            self.stars.append([x, y, base_brightness, phase, size])
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_twinkle)
        self.timer.start(60)

    def update_twinkle(self):
        for s in self.stars:
            s[3] += 0.06 + random.random() * 0.01
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor(2, 6, 18))

        grad = QtGui.QLinearGradient(self.width() * 0.2, 0, self.width(), self.height())
        grad.setColorAt(0.0, QtGui.QColor(10, 6, 20, 0))
        grad.setColorAt(1.0, QtGui.QColor(40, 10, 70, 40))
        p.fillRect(self.rect(), grad)

        for x, y, base_brightness, phase, size in self.stars:
            sx = int(x) % max(1, self.width())
            sy = int(y) % max(1, self.height())
            brightness = base_brightness + int(60 * math.sin(time.time() * 0.8 + phase))
            brightness = max(80, min(255, brightness))
            color = QtGui.QColor(brightness, brightness, brightness)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(color)
            p.drawEllipse(sx, sy, size, size)


# ----------------------------- Glow Button -----------------------------
class GlowButton(QtWidgets.QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(50)
        self.setMinimumWidth(100)
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
        base1 = "rgba(10, 40, 90, 220)"
        base2 = "rgba(25, 90, 160, 240)"
        hover1 = "rgba(20, 70, 140, 240)"
        hover2 = "rgba(70, 150, 255, 255)"
        border_normal = "rgba(30,150,255,0.35)"
        border_hover  = "rgba(80,200,255,0.70)"
        text_color = "rgb(235,245,255)"
        return f"""
        QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {base1},
            stop:1 {base2});
        border: 2px solid {border_normal};
        border-radius: 18px;
        padding: 10px 18px;
        color: {text_color};
        font-size: 24px;
        font-weight: 600;
        letter-spacing: 0.6px;
        text-align: center;
        transform: scale({scale});
        }}
        QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {hover1},
            stop:1 {hover2});
        border: 2px solid {border_hover};
        }}
        QPushButton:pressed {{
        transform: scale({max(0.98, scale - 0.02)});
        }}
        """


# ----------------------------- AURA Core (upgraded pulsation) -----------------------------
class AuraCore(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(900, 800)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.base_color = QtGui.QColor(100, 220, 255)
        self.phase = 0.0
        self.speed = 0.045
        self.saturn_angle = 0.0

        self.anim_timer = QtCore.QTimer(self)
        self.anim_timer.timeout.connect(self.animate_pulse)
        self.anim_timer.start(16)

    def animate_pulse(self):
        self.phase += self.speed
        self.saturn_angle = (self.saturn_angle + 0.45) % 360
        self.update()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        p.fillRect(self.rect(), QtCore.Qt.transparent)

        true_core = 450.0
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        r = true_core / 2.0

        pulse = (math.sin(self.phase) + 1.0) / 2.0
        t = pulse
        eased = t * t * (3 - 2 * t)
        core_scale = 1.0 + 0.14 * eased
        halo_scale = 1.0 + 0.26 * (0.5 + 0.5 * math.sin(self.phase * 0.9))

        core_r = r * core_scale
        halo_r = r * halo_scale + 100.0

        ring_alpha = int(80 + 40 * math.sin(self.phase * 1.1))
        ring_color = QtGui.QColor(self.base_color)
        ring_color.setAlpha(max(20, ring_alpha))
        pen = QtGui.QPen(ring_color, 4, QtCore.Qt.SolidLine)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        rect_wave = QtCore.QRectF(cx - halo_r, cy - halo_r, halo_r * 2.0, halo_r * 2.0)
        p.drawEllipse(rect_wave)

        glow_grad = QtGui.QRadialGradient(QtCore.QPointF(cx, cy), halo_r * 1.1)
        gc = QtGui.QColor(self.base_color)
        gc.setAlpha(int(120 * (0.5 + 0.5 * eased)))
        glow_grad.setColorAt(0.0, gc)
        glow_grad.setColorAt(0.6, QtGui.QColor(60, 140, 220, int(60 * (0.6 + 0.4 * eased))))
        glow_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(glow_grad)
        rect_glow = QtCore.QRectF(cx - halo_r * 1.1, cy - halo_r * 1.1, halo_r * 2.2, halo_r * 2.2)
        p.drawEllipse(rect_glow)

        core_grad = QtGui.QRadialGradient(QtCore.QPointF(cx, cy), core_r)
        c_inner = QtGui.QColor(220, 245, 255, int(200 * (0.8 + 0.2 * eased)))
        c_mid = QtGui.QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), int(200 * (0.7 + 0.3 * eased)))
        core_grad.setColorAt(0.0, c_inner)
        core_grad.setColorAt(0.55, c_mid)
        core_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        p.setBrush(core_grad)
        rect_core = QtCore.QRectF(cx - core_r, cy - core_r, core_r * 2.0, core_r * 2.0)
        p.drawEllipse(rect_core)

        shimmer_r = core_r * 0.22
        shimmer_alpha = int(190 + 40 * math.sin(self.phase * 2.8))
        shimmer_color = QtGui.QColor(255, 255, 255, shimmer_alpha)
        p.setBrush(shimmer_color)
        p.setPen(QtCore.Qt.NoPen)
        rect_shim = QtCore.QRectF(cx - shimmer_r, cy - shimmer_r, shimmer_r * 2.0, shimmer_r * 2.0)
        p.drawEllipse(rect_shim)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.saturn_angle)
        ring_w = core_r * 1.4
        ring_h = core_r * 0.35
        ring_rect = QtCore.QRectF(-ring_w, -ring_h / 2.0, ring_w * 2.0, ring_h)
        ring_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 40), 2)
        ring_pen.setCosmetic(True)
        p.setPen(ring_pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(ring_rect)
        p.restore()

    def pulse_react(self, color: QtGui.QColor):
        self.base_color = color
        self.phase += 0.6


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
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.overlay.raise_()

        layout = QtWidgets.QVBoxLayout(self.overlay)
        layout.setContentsMargins(28, -120, 28, 18)  # Changed top margin from -50 to -120
        layout.setSpacing(16)
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        header = self.header_widget()
        layout.addWidget(header, alignment=QtCore.Qt.AlignHCenter)

        # Position orb with absolute positioning
        self.aura_core = AuraCore()
        self.aura_core.setParent(self.overlay)
        self.aura_core.move(210, 30)  # x=100, y=100 - adjust y to move up/down
        self.aura_core.show()

        content = self.center_controls()
        layout.addWidget(content, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: rgba(180,220,255,0.9);
            letter-spacing: 1px;
            text-shadow: 0 0 12px rgba(100,160,255,0.35);
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

        font_family = "Segoe UI"
        try:
            from PyQt5.QtGui import QFontDatabase, QFont
            font_path = os.path.join(os.path.dirname(__file__), "Centauri", "Centauri.ttf")
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        except Exception:
            pass

        title = QtWidgets.QLabel("AURA")
        title.setFont(QtGui.QFont(font_family, 90, QtGui.QFont.Weight.Bold))
        title.setStyleSheet("""
            color: #87BFFF;
            letter-spacing: 30px;
            text-shadow:
                0 0 18px rgba(140, 200, 255, 0.8),
                0 0 40px rgba(100, 170, 255, 0.6);
        """)
        title.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        h.addWidget(title)
        h.addStretch()
        return w

    def center_controls(self):
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setSpacing(40)
        h_layout.setContentsMargins(1100, 150, 0, 0)  # Increased left margin (900->1050) and added top margin (0->150)

        btn_col = QtWidgets.QVBoxLayout()
        btn_col.setSpacing(18)
        btn_col.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.btn_start = GlowButton("Recog")
        self.btn_train = GlowButton("Train")
        self.btn_manage = GlowButton("Data")
        self.btn_listen = GlowButton("Ask")
        self.btn_exit = GlowButton("Exit")

        for b in [self.btn_start, self.btn_train, self.btn_manage, self.btn_listen]:
            btn_col.addWidget(b)

        self.btn_start.clicked.connect(self.start_recognition)
        self.btn_train.clicked.connect(self.train_data)
        self.btn_manage.clicked.connect(self.manage_dataset)
        self.btn_listen.clicked.connect(self.run_queries)
        self.btn_exit.clicked.connect(self.exit_app)

        h_layout.addLayout(btn_col, stretch=0)
        
        return container

    def start_recognition(self):
        script_path = os.path.join(os.path.dirname(__file__), "recognise.py")
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(self, "Error", "recognise.py not found in the app folder.")
            return
        try:
            self.aura_core.pulse_react(QtGui.QColor(38, 103, 255))
            self.status_label.setText("Recognizing...")
            subprocess.Popen([sys.executable, script_path])
            QtCore.QTimer.singleShot(3000, lambda: self.status_label.clear())
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to run recognise.py:\n{e}")
            print("Error while launching recognise.py:", e)

    def train_data(self):
        script_path = os.path.join(os.path.dirname(__file__), "train.py")
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(self, "Error", "train.py not found in the app folder.")
            return
        person_name, ok = QtWidgets.QInputDialog.getText(self, "Enter Name", "Enter the person's name for training:")
        if ok and person_name.strip():
            try:
                name = person_name.strip()
                self.aura_core.pulse_react(QtGui.QColor(255, 220, 60))
                self.status_label.setText(f"Registering {name}...")
                self.training_process = QtCore.QProcess(self)
                self.training_process.finished.connect(lambda: self.training_done(name))
                self.training_process.start(sys.executable, [script_path, name])
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to run train.py:\n{e}")

    def training_done(self, name):
        self.aura_core.pulse_react(QtGui.QColor(80, 255, 120))
        self.status_label.setText(f"{name} Registration complete!")
        QtCore.QTimer.singleShot(3000, lambda: self.status_label.clear())

    def run_queries(self):
        script_path = os.path.join(os.path.dirname(__file__), "queries_api.py")
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"queries.py not found at:\n{script_path}")
            return
        try:
            self.aura_core.pulse_react(QtGui.QColor(0, 255, 255))
            self.status_label.setText("Listening...")
            subprocess.Popen([sys.executable, script_path])
            QtCore.QTimer.singleShot(3000, lambda: self.status_label.clear())
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to run queries.py:\n{e}")
            print("Error while launching queries.py:", e)

    def manage_dataset(self):
        self.status_label.setText("Opening dataset folder...")
        self.aura_core.pulse_react(QtGui.QColor(180, 100, 255))
        data_path = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(data_path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", data_path])
        else:
            subprocess.Popen(["xdg-open", data_path])
        QtCore.QTimer.singleShot(1500, lambda: self.status_label.clear())

    def exit_app(self):
        self.status_label.setText("Exiting...")
        self.aura_core.pulse_react(QtGui.QColor(255, 70, 70))
        reply = QtWidgets.QMessageBox.question(self, "Exit", "Exit AURA Interface?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            QtWidgets.QApplication.quit()
        else:
            self.status_label.clear()


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
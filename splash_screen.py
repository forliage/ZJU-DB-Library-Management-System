# splash_screen.py
import sys
import os
from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal

# Import the resource_path function (assuming it's in main_window or a utils file)
# If it's in main_window.py, you might need to adjust the import structure slightly
# or duplicate the function here for standalone testing.
try:
    # Adjust this import based on your project structure
    from main_window import resource_path
except ImportError:
    # Fallback if running standalone or structure differs
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)

class SplashScreen(QSplashScreen):
    # Signal emitted when the splash screen has finished its fade-out
    splash_finished = pyqtSignal()

    # Define windowOpacity property for animation
    def _get_window_opacity(self):
        return super().windowOpacity()

    def _set_window_opacity(self, opacity):
        super().setWindowOpacity(opacity)

    windowOpacity = pyqtProperty(float, fget=_get_window_opacity, fset=_set_window_opacity)

    def __init__(self, image_path="icons/splash_logo.png", duration=2500, fade_duration=500):
        # Try loading the image
        self.image_path_resolved = resource_path(image_path)
        pixmap = QPixmap(self.image_path_resolved)

        if pixmap.isNull():
            print(f"警告: Splash image not found at '{self.image_path_resolved}'. Creating fallback.")
            # Create a fallback pixmap with text
            pixmap = QPixmap(600, 300) # Adjust size as needed
            pixmap.fill(QColor("#34495e")) # Use a theme color
            painter = QPainter(pixmap)
            painter.setPen(QColor(Qt.GlobalColor.white))
            font = QFont("Microsoft YaHei", 20, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "智能图书管理系统\n正在加载...")
            painter.end()

        super().__init__(pixmap)

        self.duration = duration # Total time splash is visible (ms)
        self.fade_duration = fade_duration # Fade in/out time (ms)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Allow transparency for fade

        # Center the splash screen
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.center() - self.rect().center())

        # Fade In Animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(self.fade_duration)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Fade Out Animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(self.fade_duration)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(self.close_splash) # Close after fade out

        # Timer to start fade out
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        # Start fade out slightly before total duration ends
        self.timer.timeout.connect(self.start_fade_out)

        print("Splash screen initialized.")

    def show_splash(self):
        """Show the splash screen and start animations."""
        print("Showing splash screen...")
        self.setWindowOpacity(0.0) # Start fully transparent
        self.show()
        self.fade_in_animation.start()
        # Start the timer for total duration minus fade out time
        timer_duration = max(500, self.duration - self.fade_duration) # Ensure minimum display time
        self.timer.start(timer_duration)
        print(f"Splash timer started for {timer_duration} ms.")

    def show_message(self, message, color=Qt.GlobalColor.white, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter):
        """Override showMessage for potential styling."""
        # Note: Styling the default message is limited.
        # For complex styling, draw directly onto the QPixmap before init.
        super().showMessage(message, int(alignment), color)
        QApplication.processEvents() # Ensure message is displayed


    def start_fade_out(self):
        """Start the fade-out animation."""
        print("Starting splash fade out...")
        self.fade_out_animation.start()

    def close_splash(self):
        """Close the splash screen and emit finished signal."""
        print("Closing splash screen...")
        self.close()
        self.splash_finished.emit() # Signal that splash is done
        print("Splash finished signal emitted.")

# --- Standalone Test ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Make sure you have 'icons/splash_logo.png' or change the path
    splash = SplashScreen(duration=3000)

    def on_splash_done():
        print("Splash finished, would show main window now.")
        app.quit() # Quit test app when splash is done

    splash.splash_finished.connect(on_splash_done)
    splash.show_splash()
    splash.show_message("正在加载模块...")
    QTimer.singleShot(1000, lambda: splash.show_message("连接数据库..."))
    QTimer.singleShot(2000, lambda: splash.show_message("准备主界面..."))

    sys.exit(app.exec())
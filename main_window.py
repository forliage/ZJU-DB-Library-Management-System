# main_window.py
import sys
import os
import time # For simulated loading in splash test
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSpacerItem, QSizePolicy,
    QDialog, QMessageBox, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QIcon, QFont, QColor

# --- Theme ---
from qt_material import apply_stylesheet

# --- Splash Screen ---
try:
    from splash_screen import SplashScreen
except ImportError:
    print("错误：无法导入 SplashScreen。将不显示启动画面。")
    SplashScreen = None

# --- Page Imports ---
try:
    from login_dialog import LoginDialog
except ImportError:
    print("错误：无法导入 LoginDialog.");
    class LoginDialog(QDialog): pass

try:
    from patron_login_dialog import PatronLoginDialog
except ImportError:
    print("错误：无法导入 PatronLoginDialog.");
    class PatronLoginDialog(QDialog): pass

try:
    from query_page import QueryPage
except ImportError:
    print("错误：无法导入 QueryPage.");
    class QueryPage(QWidget): pass

try:
    from add_book_page import AddBookPage
except ImportError:
    print("错误：无法导入 AddBookPage.");
    class AddBookPage(QWidget): pass

try:
    from borrow_page import BorrowPage
except ImportError:
    print("错误：无法导入 BorrowPage.");
    class BorrowPage(QWidget): pass

try:
    from return_page import ReturnPage
except ImportError:
    print("错误：无法导入 ReturnPage.");
    class ReturnPage(QWidget): pass

try:
    from card_manage_page import CardManagePage
except ImportError:
    print("错误：无法导入 CardManagePage.");
    class CardManagePage(QWidget): pass

try:
    from overdue_page import OverduePage
except ImportError:
    print("错误：无法导入 OverduePage.");
    class OverduePage(QWidget): pass

from patron_borrowing_page import PatronBorrowingPage



try:
    from ai_assistant_page import AIAssistantPage
except ImportError:
    print("错误：无法导入 AIAssistantPage.");
    class AIAssistantPage(QWidget): pass


# --- Resource Path Function ---
def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- Placeholder Page ---
class PlaceholderPage(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"这里是 {text} 页面 (待实现)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("SimSun", 18))
        layout.addWidget(label)
        self.setStyleSheet("background-color: #f0f0f0;")

# --- Main Window Class ---
class MainWindow(QMainWindow):
    # Window Opacity Property for animation
    def _get_window_opacity(self): return super().windowOpacity()
    def _set_window_opacity(self, opacity): super().setWindowOpacity(opacity)
    window_opacity = pyqtProperty(float, fget=_get_window_opacity, fset=_set_window_opacity)

    def __init__(self):
        super().__init__()
        self.logged_in_user = None      # Admin info
        self.logged_in_patron = None    # Patron info
        self.animation_running = False
        self.page_effects = {}
        self.active_button_name = None # Track active button for styling

        self.setWindowTitle("✨ 智能图书管理系统 ✨")
        self.setGeometry(100, 100, 1150, 720)
        app_icon_path = resource_path(os.path.join('icons', 'app_icon.ico'))
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))

        # --- Central Widget and Main Layout ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        # Set background for the content area parent
        main_widget.setStyleSheet("background-color: #ecf0f1;")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Navigation Panel ---
        self.nav_widget = QWidget()
        self.nav_widget.setFixedWidth(200)
        nav_gradient = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #2c3e50, stop:1 #34495e);"
        self.nav_widget.setStyleSheet(f"background-color: {nav_gradient}; color: white;")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20); shadow.setColor(QColor(0, 0, 0, 80)); shadow.setOffset(5, 5)
        self.nav_widget.setGraphicsEffect(shadow)

        nav_layout = QVBoxLayout(self.nav_widget)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        nav_layout.setContentsMargins(10, 30, 10, 20)
        nav_layout.setSpacing(15) # Slightly reduced spacing

        # Styled Title
        title_label = QLabel()
        title_label.setTextFormat(Qt.TextFormat.RichText)
        title_label.setText("<p align='center'><font size='+2' color='#ecf0f1'>📚</font> <font size='+1' color='#ffffff' style='font-weight:bold;'>图书管理</font></p>")
        title_label.setStyleSheet("margin-bottom: 30px;")
        nav_layout.addWidget(title_label)

        # Navigation Buttons Setup
        self.nav_buttons = {}
        self.base_button_style = """
            QPushButton {
                background-color: transparent; color: white; border: none;
                padding: 12px 20px; text-align: left; min-height: 45px;
                font-size: 14px; border-radius: 8px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
            QPushButton:pressed { background-color: rgba(0, 0, 0, 0.1); }
            QPushButton:disabled { color: #7f8c8d; background-color: transparent; }
        """
        self.active_button_style = self.base_button_style + """
            QPushButton {
                background-color: rgba(41, 128, 185, 0.8);
                border-left: 4px solid #3498db;
                font-weight: bold;
            }
        """
        buttons_info = [
            ("图书查询", "btn_query", False, True, "search.svg"),
            ("AI 搜书", "btn_ai_search", False, True, "cpu.svg"),
            ("我的借阅", "btn_my_borrowing", False, True, "book-open.svg"),
            ("读者登录", "btn_patron_login", False, False, "user.svg"),
            ("管理员登录", "btn_admin_login", False, False, "shield.svg"),
            ("退出登录", "btn_logout", True, True, "log-out.svg"),
            ("图书入库", "btn_add_book", True, False, "plus-circle.svg"),
            ("借书管理", "btn_borrow", True, False, "arrow-up-circle.svg"),
            ("还书管理", "btn_return", True, False, "arrow-down-circle.svg"),
            ("借书证管理", "btn_card_manage", True, False, "users.svg"),
            ("逾期提醒", "btn_overdue", True, False, "alert-triangle.svg"),
        ]

        for text, name, is_admin, is_patron, icon_file in buttons_info:
            button = QPushButton(text)
            button.setObjectName(name)
            button.setStyleSheet(self.base_button_style)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("is_admin_only", is_admin)
            button.setProperty("is_patron_only", is_patron)
            icon_path = resource_path(os.path.join('icons', icon_file))
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(24, 24))
            else:
                print(f"警告: 图标文件未找到: {icon_path}")
            nav_layout.addWidget(button)
            self.nav_buttons[name] = button

        nav_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        main_layout.addWidget(self.nav_widget)

        # --- Right Content Area (StackedWidget) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create Pages and add effects
        self.pages = {}
        page_definitions = {
            "query": ("图书查询", QueryPage()),
            "ai_search": ("AI 搜书", AIAssistantPage()),
            "my_borrowing": ("我的借阅", PatronBorrowingPage()),
            "add_book": ("图书入库", AddBookPage()),
            "borrow": ("借书管理", BorrowPage()),
            "return": ("还书管理", ReturnPage()),
            "card_manage": ("借书证管理", CardManagePage()),
            "overdue": ("逾期提醒", OverduePage()),
        }
        for name, (title, page_widget) in page_definitions.items():
            if isinstance(page_widget, QWidget):
                opacity_effect = QGraphicsOpacityEffect(page_widget)
                opacity_effect.setOpacity(1.0)
                page_widget.setGraphicsEffect(opacity_effect)
                self.page_effects[page_widget] = opacity_effect
                self.stacked_widget.addWidget(page_widget)
                self.pages[name] = page_widget
            else:
                print(f"警告：页面 '{name}' (标题: {title}) 对应的实例无效，跳过添加。")
                error_page = PlaceholderPage(f"{title} 页面加载失败")
                opacity_effect = QGraphicsOpacityEffect(error_page)
                opacity_effect.setOpacity(1.0)
                error_page.setGraphicsEffect(opacity_effect)
                self.page_effects[error_page] = opacity_effect
                self.stacked_widget.addWidget(error_page)
                self.pages[name] = error_page

        # --- Status Bar ---
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("background-color: #bdc3c7; color: #2c3e50; padding: 3px;")
        self.user_label = QLabel("当前状态: 未登录")
        self.time_label = QLabel(" ")
        self.status_bar.addPermanentWidget(self.user_label, stretch=1)
        self.status_bar.addPermanentWidget(self.time_label)

        # Timer for clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time() # Initial time update

        # --- Connect Signals ---
        self.nav_buttons["btn_query"].clicked.connect(lambda: self.switch_page("query"))
        self.nav_buttons["btn_ai_search"].clicked.connect(lambda: self.switch_page("ai_search"))
        self.nav_buttons["btn_my_borrowing"].clicked.connect(lambda: self.switch_page("my_borrowing"))
        self.nav_buttons["btn_patron_login"].clicked.connect(self.handle_patron_login)
        self.nav_buttons["btn_admin_login"].clicked.connect(self.handle_admin_login)
        self.nav_buttons["btn_logout"].clicked.connect(self.handle_logout)
        self.nav_buttons["btn_add_book"].clicked.connect(lambda: self.switch_page("add_book"))
        self.nav_buttons["btn_borrow"].clicked.connect(lambda: self.switch_page("borrow"))
        self.nav_buttons["btn_return"].clicked.connect(lambda: self.switch_page("return"))
        self.nav_buttons["btn_card_manage"].clicked.connect(lambda: self.switch_page("card_manage"))
        self.nav_buttons["btn_overdue"].clicked.connect(lambda: self.switch_page("overdue"))

        # --- Set Initial View State (without showing window yet) ---
        self.update_view_for_state()
        default_page = "query"
        if default_page in self.pages and isinstance(self.pages[default_page], QWidget):
            self.stacked_widget.setCurrentWidget(self.pages[default_page])
            self.update_active_button(default_page)
        elif self.stacked_widget.count() > 0:
            self.stacked_widget.setCurrentIndex(0)
            for name, widget in self.pages.items():
                if widget == self.stacked_widget.currentWidget():
                    self.update_active_button(name)
                    break
        # Ensure initial page effect is correct
        current_initial_widget = self.stacked_widget.currentWidget()
        if current_initial_widget and current_initial_widget in self.page_effects:
            self.page_effects[current_initial_widget].setOpacity(1.0)


    # --- Method to Start Fade-in Animation ---
    def start_fade_in_animation(self):
        """Starts the main window fade-in animation. Call after show()."""
        self.setWindowOpacity(0.0)
        self.fade_in_animation = QPropertyAnimation(self, b'window_opacity')
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_in_animation.start()
        print("Main window fade-in started.")

    # --- Animation and Page Switching Methods ---
    def switch_page(self, page_name):
        if self.animation_running: return
        if page_name not in self.pages: print(f"错误：找不到页面 '{page_name}'。"); return
        target_widget = self.pages[page_name]; current_widget = self.stacked_widget.currentWidget()
        if target_widget == current_widget: self.refresh_page_data(page_name, target_widget); return
        if not isinstance(target_widget, QWidget): print(f"错误：页面 '{page_name}' 对应的对象不是有效的 QWidget。"); return

        self.animation_running = True; self.disable_navigation()
        target_effect = self.page_effects.get(target_widget); current_effect = self.page_effects.get(current_widget)
        if target_effect: target_effect.setOpacity(0.0); target_widget.setVisible(True)

        if current_widget and current_effect:
            self.fade_out = QPropertyAnimation(current_effect, b"opacity"); self.fade_out.setDuration(200)
            self.fade_out.setStartValue(1.0); self.fade_out.setEndValue(0.0); self.fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
            self.fade_out.finished.connect(lambda: self.perform_fade_in(current_widget, target_widget, page_name))
            self.fade_out.start()
        else:
            self.perform_fade_in(None, target_widget, page_name)

    def perform_fade_in(self, old_widget, new_widget, new_page_name):
        self.stacked_widget.setCurrentWidget(new_widget);
        if old_widget: old_widget.setVisible(False)
        self.refresh_page_data(new_page_name, new_widget)
        self.update_active_button(new_page_name)
        target_effect = self.page_effects.get(new_widget)
        if target_effect:
            self.fade_in = QPropertyAnimation(target_effect, b"opacity"); self.fade_in.setDuration(200)
            self.fade_in.setStartValue(0.0); self.fade_in.setEndValue(1.0); self.fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.fade_in.finished.connect(self.animation_finished); self.fade_in.start()
        else:
            self.animation_finished()

    def animation_finished(self):
        self.animation_running = False
        self.enable_navigation()
        print("页面切换动画完成。")

    def disable_navigation(self):
        for button in self.nav_buttons.values():
            button.setEnabled(False)

    def enable_navigation(self):
        is_admin = self.logged_in_user is not None
        is_patron = self.logged_in_patron is not None
        is_logged_in = is_admin or is_patron
        for name, button in self.nav_buttons.items():
            is_admin_only = button.property("is_admin_only")
            is_patron_only = button.property("is_patron_only")
            # Login/logout buttons visibility/enabled state
            if name == "btn_admin_login": button.setEnabled(not is_logged_in); button.setVisible(not is_logged_in)
            elif name == "btn_patron_login": button.setEnabled(not is_logged_in); button.setVisible(not is_logged_in)
            elif name == "btn_logout": button.setEnabled(is_logged_in); button.setVisible(is_logged_in)
            # Functional buttons visibility/enabled state
            elif is_admin_only: button.setEnabled(is_admin); button.setVisible(is_admin)
            elif is_patron_only: button.setEnabled(is_logged_in); button.setVisible(is_logged_in)
            else: button.setEnabled(True); button.setVisible(True) # Common buttons

    def update_active_button(self, active_page_name):
        button_page_map = {"btn_query": "query", "btn_ai_search": "ai_search", "btn_my_borrowing": "my_borrowing", "btn_add_book": "add_book", "btn_borrow": "borrow", "btn_return": "return", "btn_card_manage": "card_manage", "btn_overdue": "overdue"}
        active_button_name = None
        for btn_name, page_name in button_page_map.items():
            if page_name == active_page_name: active_button_name = btn_name; break
        if self.active_button_name and self.active_button_name in self.nav_buttons:
            self.nav_buttons[self.active_button_name].setStyleSheet(self.base_button_style)
        if active_button_name and active_button_name in self.nav_buttons:
            self.nav_buttons[active_button_name].setStyleSheet(self.active_button_style)
            self.active_button_name = active_button_name
        else:
            self.active_button_name = None

    def refresh_page_data(self, page_name, page_widget):
         print(f"Refreshing data for page: {page_name}")
         if page_name == "my_borrowing" and hasattr(page_widget, 'set_patron_info'): page_widget.set_patron_info(self.logged_in_patron)
         elif page_name == "overdue" and hasattr(page_widget, 'load_overdue_records'): page_widget.load_overdue_records()
         elif page_name == "query" and hasattr(page_widget, 'load_borrow_ranking'): page_widget.load_borrow_ranking(); page_widget.perform_search(initial_load=True)
         elif page_name == "add_book" and hasattr(page_widget, 'load_recent_books'): page_widget.load_recent_books()
         elif page_name == "card_manage" and hasattr(page_widget, 'load_cards'): page_widget.load_cards(); page_widget.clear_stats_display()
         elif page_name == "borrow" and hasattr(page_widget, 'set_operator'): page_widget.set_operator(self.logged_in_user['UserID'] if self.logged_in_user else None)

    # --- Login/Logout Handlers ---
    def handle_admin_login(self):
        if self.logged_in_patron: self.handle_logout() # Log out patron if active
        login_dialog = LoginDialog(self); result = login_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.logged_in_user = login_dialog.get_user_info();
            if self.logged_in_user:
                print(f"管理员 '{self.logged_in_user['UserID']}' 登录成功")
                self.update_view_for_state()
                self.switch_page("query") # Switch to default page after login
            else:
                QMessageBox.critical(self, "登录错误", "管理员登录成功但未能获取用户信息！")
                self.logged_in_user = None; self.update_view_for_state()
        else:
            print("管理员取消登录或登录失败。")
            self.logged_in_user = None; self.update_view_for_state()

    def handle_patron_login(self):
        if self.logged_in_user: self.handle_logout() # Log out admin if active
        login_dialog = PatronLoginDialog(self); result = login_dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.logged_in_patron = login_dialog.get_patron_info();
            if self.logged_in_patron:
                print(f"读者 '{self.logged_in_patron['CardNo']}' 登录成功")
                self.update_view_for_state()
                self.switch_page("my_borrowing") # Switch to default page after login
            else:
                QMessageBox.critical(self, "登录错误", "读者登录成功但未能获取用户信息！")
                self.logged_in_patron = None; self.update_view_for_state()
        else:
            print("读者取消登录或登录失败。")
            self.logged_in_patron = None; self.update_view_for_state()

    def handle_logout(self):
        logged_out_user = None
        if self.logged_in_user: logged_out_user = f"管理员 '{self.logged_in_user['UserID']}'"
        elif self.logged_in_patron: logged_out_user = f"读者 '{self.logged_in_patron['CardNo']}'"
        self.logged_in_user = None; self.logged_in_patron = None
        if logged_out_user: print(f"用户 '{logged_out_user}' 正在退出登录")
        self.update_view_for_state()
        if "query" in self.pages: self.switch_page("query")

    # --- Unified View Update ---
    def update_view_for_state(self):
        is_admin = self.logged_in_user is not None
        is_patron = self.logged_in_patron is not None
        if is_admin:
            display_name = self.logged_in_user.get('Name') or self.logged_in_user.get('UserID', '管理员')
            self.user_label.setText(f"当前用户: {display_name} (管理员)")
        elif is_patron:
            display_name = self.logged_in_patron.get('Name') or self.logged_in_patron.get('CardNo', '读者')
            self.user_label.setText(f"当前用户: {display_name} (读者)")
        else:
            self.user_label.setText("当前状态: 未登录")
        self.enable_navigation() # Handles visibility and enabled state
        # Reset active button highlight only if needed (e.g., on logout)
        if not is_admin and not is_patron:
            self.update_active_button(None)
            if "query" in self.pages: # Ensure default page button is active
                 self.update_active_button("query")
        else:
             # Update active button based on current page (handled in switch_page)
             pass


    # --- Clock Update ---
    def update_time(self):
        current_time = QDateTime.currentDateTime()
        formatted_time = current_time.toString("yyyy-MM-dd hh:mm:ss")
        self.time_label.setText(formatted_time)

    # --- Close Event ---
    def closeEvent(self, event):
        print("主窗口关闭事件触发...")
        # Stop animations
        if hasattr(self, 'fade_out') and self.fade_out and self.fade_out.state() == QPropertyAnimation.State.Running: self.fade_out.stop()
        if hasattr(self, 'fade_in') and self.fade_in and self.fade_in.state() == QPropertyAnimation.State.Running: self.fade_in.stop()
        if hasattr(self, 'fade_in_animation') and self.fade_in_animation and self.fade_in_animation.state() == QPropertyAnimation.State.Running: self.fade_in_animation.stop()
        # Notify pages
        for page_name, page_widget in self.pages.items():
            if hasattr(page_widget, 'closeEvent') and callable(page_widget.closeEvent):
                try: page_widget.closeEvent(event)
                except Exception as e: print(f"调用页面 {page_name} 的 closeEvent 时出错: {e}")
        print("已尝试通知所有页面关闭...")
        super().closeEvent(event)


# --- Application Entry Point ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_blue.xml', extra={'density_scale': '0'}) # Apply theme

    splash = None
    main_win = None # Define main_win here

    # Function to show main window after splash
    def show_main_window():
        global main_win
        print("Splash finished. Creating and showing main window...")
        main_win = MainWindow()
        main_win.show()
        main_win.start_fade_in_animation() # Start fade-in AFTER show()
        if splash:
            splash.close()

    if SplashScreen:
        splash = SplashScreen(duration=2500, fade_duration=400)
        splash.splash_finished.connect(show_main_window)
        splash.show_splash()
        splash.show_message("正在初始化...", alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        app.processEvents() # Ensure splash is visible
        # Simulate loading (optional)
        # time.sleep(0.5); splash.show_message("加载配置..."); app.processEvents()
        # time.sleep(0.5); splash.show_message("准备就绪..."); app.processEvents()
    else:
        # No splash screen, show main window directly
        print("未加载启动画面，直接启动主窗口。")
        main_win = MainWindow()
        main_win.show()
        main_win.start_fade_in_animation()

    sys.exit(app.exec())
# patron_login_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

# Assuming db_utils.py is accessible
try:
    from db_utils import execute_query
except ImportError:
    print("错误：无法从 db_utils 导入 execute_query。")
    def execute_query(query, params=None): return None


class PatronLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patron_info = None # Store successful patron info (dict)

        self.setWindowTitle("读者登录")
        # self.setWindowIcon(QIcon(resource_path("icons/patron_login.ico"))) # Optional icon
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("读者登录")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Card Number Input
        card_layout = QHBoxLayout()
        card_label = QLabel("借书证卡号:")
        card_label.setFixedWidth(80) # Adjust width as needed
        self.cardno_input = QLineEdit()
        self.cardno_input.setPlaceholderText("请输入您的借书证卡号")
        card_layout.addWidget(card_label)
        card_layout.addWidget(self.cardno_input)
        layout.addLayout(card_layout)

        # --- Add Password/PIN field (Recommended for real system) ---
        # For this example, we'll authenticate by CardNo only for simplicity.
        # pass_layout = QHBoxLayout()
        # pass_label = QLabel("密码/PIN:")
        # pass_label.setFixedWidth(80)
        # self.password_input = QLineEdit()
        # self.password_input.setPlaceholderText("输入密码或PIN码")
        # self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # pass_layout.addWidget(pass_label)
        # pass_layout.addWidget(self.password_input)
        # layout.addLayout(pass_layout)
        # --- ---

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.login_button = QPushButton("登录")
        self.cancel_button = QPushButton("取消")
        self.login_button.setDefault(True)
        self.login_button.setMinimumWidth(80)
        self.cancel_button.setMinimumWidth(80)
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # --- Signals and Slots ---
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.cardno_input.returnPressed.connect(self.handle_login)
        # if hasattr(self, 'password_input'): # If password field exists
        #     self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        card_no = self.cardno_input.text().strip()
        # password = self.password_input.text() # If password field exists

        if not card_no: # Add password check if using password
            QMessageBox.warning(self, "输入错误", "借书证卡号不能为空！")
            return

        # --- Database Validation ---
        # Query LibraryCard table based on CardNo (and password if implemented)
        query = "SELECT CardNo, Name, Department, CardType FROM LibraryCard WHERE CardNo = %s"
        # In a real system with passwords:
        # query = "SELECT CardNo, Name, Department, CardType FROM LibraryCard WHERE CardNo = %s AND PasswordHash = HASH_FUNCTION(%s)"
        params = (card_no,)
        result = execute_query(query, params)

        if result: # Card number exists
            self.patron_info = result[0] # Get patron info dictionary
            # Simple success message (no name displayed here, handled in main window)
            # QMessageBox.information(self, "登录成功", "登录成功！")
            self.accept() # Close dialog with Accepted status
        else:
            QMessageBox.critical(self, "登录失败", "无效的借书证卡号！") # Add or password mismatch if using password
            # self.password_input.clear() # If password field exists
            self.cardno_input.setFocus()

    def get_patron_info(self):
        """Returns the dictionary containing logged-in patron's info"""
        return self.patron_info

# --- Standalone Test ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    # Ensure you have test data in LibraryCard table
    app = QApplication(sys.argv)
    dialog = PatronLoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("读者登录成功！信息:", dialog.get_patron_info())
    else:
        print("读者取消登录或登录失败。")
    sys.exit()
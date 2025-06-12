# login_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont, QIcon # Optional: for styling
from PyQt6.QtCore import Qt

# 假设 db_utils.py 在同一目录下或 PYTHONPATH 中
try:
    from db_utils import execute_query
except ImportError:
    print("错误：无法从 db_utils 导入 execute_query。")
    # 在实际应用中可能需要更健壮的错误处理
    def execute_query(query, params=None): return None # 提供一个空实现以避免立即崩溃


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_info = None # 用于存储成功登录的用户信息

        self.setWindowTitle("管理员登录")
        # self.setWindowIcon(QIcon("path/to/login/icon.png")) # 可选图标
        self.setMinimumWidth(350) # 设置最小宽度
        self.setModal(True) # 设置为模态对话框，阻止与主窗口交互

        layout = QVBoxLayout(self)
        layout.setSpacing(15) # 控件间距
        layout.setContentsMargins(20, 20, 20, 20) # 对话框内边距

        title_label = QLabel("管理员登录")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 用户名输入
        user_layout = QHBoxLayout()
        user_label = QLabel("用户名:")
        user_label.setFixedWidth(60) # 固定标签宽度
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入管理员ID")
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.username_input)
        layout.addLayout(user_layout)

        # 密码输入
        pass_layout = QHBoxLayout()
        pass_label = QLabel("密  码:") # 使用全角空格对齐
        pass_label.setFixedWidth(60)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password) # 密码模式
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.password_input)
        layout.addLayout(pass_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        # 添加弹性空间将按钮推到右侧
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.login_button = QPushButton("登录")
        self.cancel_button = QPushButton("取消")
        self.login_button.setDefault(True) # 设置为默认按钮 (回车触发)
        self.login_button.setMinimumWidth(80)
        self.cancel_button.setMinimumWidth(80)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # --- 信号和槽 ---
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject) # reject() 会关闭对话框并返回 Rejected
        # 密码框按回车也尝试登录
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        """处理登录按钮点击事件"""
        username = self.username_input.text().strip()
        password = self.password_input.text() # 密码通常不需要 strip()

        if not username or not password:
            QMessageBox.warning(self, "输入错误", "用户名和密码不能为空！")
            return

        # --- 数据库验证 ---
        # !!! 安全警告：实际生产环境绝不能直接比较明文密码 !!!
        # !!! 应该存储密码哈希值，并比较哈希值 !!!
        # 这里为了简化，暂时直接比较
        query = "SELECT UserID, Name, Contact FROM Users WHERE UserID = %s AND Password = %s"
        params = (username, password)
        result = execute_query(query, params) # execute_query 返回列表，元素是字典

        if result: # 如果查询结果不为空 (列表非空)
            # 登录成功
            self.user_info = result[0] # 获取用户信息字典
            QMessageBox.information(self, "登录成功", f"欢迎您，{self.user_info.get('Name', username)}！")
            self.accept() # 关闭对话框并返回 Accepted
        else:
            # 登录失败
            QMessageBox.critical(self, "登录失败", "用户名或密码错误！")
            # 清空密码框，让用户重新输入
            self.password_input.clear()
            self.password_input.setFocus() # 将焦点设置回密码框

    def get_user_info(self):
        """返回成功登录的用户信息字典"""
        return self.user_info

# --- 用于独立测试对话框 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    # ！！！注意：要测试这个对话框，你需要先手动向 Users 表插入一条测试数据！！！
    # 例如，在 MySQL 中执行：
    # USE library_management_system;
    # INSERT INTO Users (UserID, Password, Name, Contact) VALUES ('admin', '123456', '测试管理员', '13800138000');
    # 确保你的 db_utils 和 config.py 配置正确且 MySQL 服务运行中

    app = QApplication(sys.argv)
    dialog = LoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("登录成功！用户信息:", dialog.get_user_info())
    else:
        print("用户取消登录或登录失败。")
    sys.exit()
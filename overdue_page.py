# overdue_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate # 导入 QDate 用于日期比较
from PyQt6.QtGui import QFont, QColor
import datetime

# 假设 db_utils.py 在可访问路径
try:
    from db_utils import execute_query
except ImportError as e:
    print(f"错误：导入数据库工具时出错 - {e}")
    def execute_query(query, params=None): return None

class OverduePage(QWidget):
    # 假设借阅期限（天）
    BORROW_DURATION_DAYS = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_overdue_records() # 页面加载时自动加载

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        title_label = QLabel("图书逾期提醒")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        info_label = QLabel(f"以下是已借出超过 {self.BORROW_DURATION_DAYS} 天且尚未归还的记录：")
        main_layout.addWidget(info_label)

        # 刷新按钮
        self.refresh_button = QPushButton("刷新列表")
        self.refresh_button.clicked.connect(self.load_overdue_records)
        # 将按钮放在布局右侧
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        main_layout.addLayout(button_layout)


        # 显示逾期记录的表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7) # FID, 卡号, 姓名, 书号, 书名, 借出日期, 逾期天数
        self.table_widget.setHorizontalHeaderLabels([
            "记录ID", "卡号", "持卡人姓名", "书号(ID)", "书名", "借出日期", "已逾期(天)"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # 书名可调
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # 逾期天数列自适应内容
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget { gridline-color: #dcdcdc; alternate-background-color: #fff0f0; } /* 淡红色隔行 */
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #dcdcdc; font-weight: bold;}
        """)
        main_layout.addWidget(self.table_widget)

    def load_overdue_records(self):
        """查询并加载所有逾期未还的记录"""
        # 计算截止日期 (今天 - 借阅期限)
        # 使用数据库的日期函数通常更可靠
        # MySQL: DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        # PostgreSQL: CURRENT_DATE - INTERVAL '30 days'
        # SQLite: date('now', '-30 days')
        # 这里我们假设使用 MySQL 的语法
        # 注意：直接在 SQL 中拼接字符串可能不安全或效率低，参数化更好
        # 但日期计算通常是安全的

        # cutoff_date = datetime.date.today() - datetime.timedelta(days=self.BORROW_DURATION_DAYS)
        # cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')

        query = f"""
        SELECT
            lr.FID, lr.CardNo, lc.Name AS BorrowerName, lr.BookNo, b.BookName, lr.LentDate,
            DATEDIFF(CURDATE(), lr.LentDate) AS OverdueDays -- 计算借出天数 (MySQL DATEDIFF)
        FROM LibraryRecords lr
        JOIN Books b ON lr.BookNo = b.BookNo
        JOIN LibraryCard lc ON lr.CardNo = lc.CardNo
        WHERE lr.ReturnDate IS NULL
          AND lr.LentDate < DATE_SUB(CURDATE(), INTERVAL {self.BORROW_DURATION_DAYS} DAY) -- 只查询借出日期早于截止日期的
        ORDER BY OverdueDays DESC, lr.LentDate ASC
        """
        # 注意：这里直接格式化了天数，对于固定值是安全的。如果天数是变量，应考虑其他方式。

        results = execute_query(query) # 无需参数
        self.populate_overdue_table(results)


    def populate_overdue_table(self, data):
        """填充逾期记录表格"""
        self.table_widget.setRowCount(0)
        if data is None:
            QMessageBox.critical(self, "查询错误", "获取逾期记录时发生错误！")
            return
        if not data:
            self.table_widget.setRowCount(1)
            no_overdue_item = QTableWidgetItem("当前没有逾期未还的记录。")
            no_overdue_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(0, 0, no_overdue_item)
            self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
            return

        self.table_widget.setRowCount(len(data))
        column_keys = ["FID", "CardNo", "BorrowerName", "BookNo", "BookName", "LentDate", "OverdueDays"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = ""
                if value is not None:
                     if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
                         display_text = value.strftime('%Y-%m-%d') # 只显示日期部分
                     else:
                         display_text = str(value)

                item = QTableWidgetItem(display_text)
                # 突出显示逾期天数
                if key == "OverdueDays":
                     item.setForeground(QColor('red'))
                     item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                     item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # 居中对齐天数
                elif key == "FID":
                     item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                     item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                self.table_widget.setItem(row_index, col_index, item)

# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    overdue_page = OverduePage()
    layout.addWidget(overdue_page)
    window.setWindowTitle("逾期提醒页面测试")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
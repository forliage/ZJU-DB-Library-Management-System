# patron_borrowing_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import datetime

# Assuming db_utils.py is accessible
try:
    from db_utils import execute_query
except ImportError as e:
    print(f"错误：导入数据库工具时出错 - {e}")
    def execute_query(query, params=None): return None

class PatronBorrowingPage(QWidget):
    # Consistent borrow duration
    BORROW_DURATION_DAYS = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.patron_card_no = None
        self.patron_name = "读者" # Default name
        self.setup_ui()

    def set_patron_info(self, patron_info):
        """Receives patron info (dict) from main window"""
        if patron_info and 'CardNo' in patron_info:
            self.patron_card_no = patron_info['CardNo']
            self.patron_name = patron_info.get('Name', self.patron_card_no) # Use name or card no
            self.welcome_label.setText(f"欢迎您，{self.patron_name}！")
            self.load_borrowing_info() # Load info when patron is set
        else:
            self.patron_card_no = None
            self.patron_name = "读者"
            self.welcome_label.setText("请先登录")
            self.table_widget.setRowCount(0) # Clear table if no patron

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.welcome_label = QLabel("请先登录查看借阅信息")
        self.welcome_label.setFont(QFont("Microsoft YaHei", 14))
        main_layout.addWidget(self.welcome_label)

        records_group = QGroupBox("我当前借阅的图书")
        records_layout = QVBoxLayout(records_group)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5) # BookNo, BookName, Author, LentDate, DueDate
        self.table_widget.setHorizontalHeaderLabels([
            "书号(ID)", "书名", "作者", "借出日期", "应还日期"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # BookName adjustable
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget { gridline-color: #dcdcdc; alternate-background-color: #f8f8f8; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #dcdcdc; font-weight: bold;}
        """)
        records_layout.addWidget(self.table_widget)
        main_layout.addWidget(records_group)

    def load_borrowing_info(self):
        """Loads borrowing info for the current patron"""
        if not self.patron_card_no:
            self.table_widget.setRowCount(0)
            return

        query = """
        SELECT lr.BookNo, b.BookName, b.Author, lr.LentDate
        FROM LibraryRecords lr
        JOIN Books b ON lr.BookNo = b.BookNo
        WHERE lr.CardNo = %s AND lr.ReturnDate IS NULL
        ORDER BY lr.LentDate ASC
        """
        results = execute_query(query, (self.patron_card_no,))
        self.populate_table(results)

    def populate_table(self, data):
        """Fills the table with borrowing data"""
        self.table_widget.setRowCount(0)
        if data is None:
            QMessageBox.critical(self, "错误", "查询借阅记录时出错！")
            return
        if not data:
            self.table_widget.setRowCount(1)
            no_records_item = QTableWidgetItem("您当前没有借阅中的图书。")
            no_records_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(0, 0, no_records_item)
            self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
            return

        self.table_widget.setRowCount(len(data))
        today = datetime.date.today()
        column_keys = ["BookNo", "BookName", "Author", "LentDate"] # DueDate calculated

        for row_index, row_data in enumerate(data):
            lent_date_dt = row_data.get("LentDate")
            due_date = None
            is_overdue = False

            if isinstance(lent_date_dt, datetime.datetime):
                lent_date_str = lent_date_dt.strftime('%Y-%m-%d')
                # Calculate due date
                due_date_dt = lent_date_dt.date() + datetime.timedelta(days=self.BORROW_DURATION_DAYS)
                due_date = due_date_dt.strftime('%Y-%m-%d')
                if due_date_dt < today:
                    is_overdue = True
            else:
                lent_date_str = "N/A"


            for col_index, key in enumerate(self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())):
                if key == "应还日期":
                    value = due_date if due_date else "N/A"
                else:
                     internal_key = column_keys[col_index] # Map header label index to data key index
                     value = row_data.get(internal_key)

                display_text = str(value) if value is not None else ""
                if key == "借出日期": display_text = lent_date_str # Use formatted date string

                item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                # Highlight overdue items
                if key == "应还日期" and is_overdue:
                    item.setForeground(QColor('red'))
                    item.setFont(QFont(item.font().family(), item.font().pointSize(), QFont.Weight.Bold))
                    item.setText(f"{display_text} (已逾期)")

                self.table_widget.setItem(row_index, col_index, item)


# --- Standalone Test ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    # Ensure you have test data for a specific CardNo in LibraryRecords (with ReturnDate=NULL)
    TEST_PATRON_INFO = {'CardNo': '000001', 'Name': '测试读者李四'} # Replace with actual test CardNo

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    patron_page = PatronBorrowingPage()
    patron_page.set_patron_info(TEST_PATRON_INFO) # Pass test info
    layout.addWidget(patron_page)
    window.setWindowTitle("读者借阅页面测试")
    window.resize(700, 400)
    window.show()
    sys.exit(app.exec())
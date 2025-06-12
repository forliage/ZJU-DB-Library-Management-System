# return_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QTextEdit # 导入 QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import datetime

# 假设 db_utils.py 在可访问路径
try:
    from db_utils import execute_query, execute_modify
except ImportError as e:
    print(f"错误：导入数据库工具时出错 - {e}")
    def execute_query(query, params=None): return None
    def execute_modify(query, params=None): return None

class ReturnPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_card_no = None
        self.current_borrowed_records = {}
        self.most_common_book_type = None # 存储分析出的最常借阅类别
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- 顶部：借书证和图书输入 ---
        top_group = QGroupBox("还书操作与信息")
        top_layout = QHBoxLayout(top_group)

        # 借书证输入区域
        card_info_layout = QVBoxLayout()
        card_input_layout = QHBoxLayout()
        card_label = QLabel("借书证卡号:")
        self.card_no_input = QLineEdit()
        self.card_no_input.setPlaceholderText("输入卡号后按回车或点击查询")
        self.card_no_input.returnPressed.connect(self.find_borrower_and_records)
        self.find_card_button = QPushButton("查询")
        self.find_card_button.clicked.connect(self.find_borrower_and_records)
        card_input_layout.addWidget(card_label)
        card_input_layout.addWidget(self.card_no_input, 1)
        card_input_layout.addWidget(self.find_card_button)
        card_info_layout.addLayout(card_input_layout)

        self.borrower_info_label = QLabel("持卡人信息: N/A")
        self.borrower_info_label.setStyleSheet("font-style: italic; color: gray;")
        card_info_layout.addWidget(self.borrower_info_label)

        self.habit_label = QLabel("最常借阅类别: N/A")
        self.habit_label.setStyleSheet("font-style: italic; color: gray;")
        card_info_layout.addWidget(self.habit_label)

        # 图书推荐区域
        self.recommendation_group = QGroupBox("为您推荐")
        self.recommendation_group.setVisible(False)
        recommendation_layout = QVBoxLayout(self.recommendation_group)
        self.recommendation_text = QTextEdit()
        self.recommendation_text.setReadOnly(True)
        self.recommendation_text.setMaximumHeight(100)
        self.recommendation_text.setStyleSheet("background-color: #fdfdfd;")
        recommendation_layout.addWidget(self.recommendation_text)
        card_info_layout.addWidget(self.recommendation_group)

        card_info_layout.addStretch()

        # 图书输入与还书区域
        book_action_layout = QVBoxLayout()
        book_label = QLabel("要归还的图书书号(ID):")
        self.book_no_input = QLineEdit()
        self.book_no_input.setPlaceholderText("输入要归还的图书ID")
        self.return_button = QPushButton("确认归还")
        self.return_button.setEnabled(False)
        self.return_button.setStyleSheet("padding: 8px 15px; background-color: #e67e22; color: white; font-weight: bold;")
        self.return_button.clicked.connect(self.perform_return)
        book_action_layout.addWidget(book_label)
        book_action_layout.addWidget(self.book_no_input)
        book_action_layout.addWidget(self.return_button)
        book_action_layout.addStretch()

        top_layout.addLayout(card_info_layout, 2)
        top_layout.addLayout(book_action_layout, 1)
        main_layout.addWidget(top_group)

        # --- 中部：当前借阅记录显示 ---
        records_group = QGroupBox("当前借阅中的图书 (未归还)")
        records_layout = QVBoxLayout(records_group)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels([
            "记录ID", "书号(ID)", "书名", "作者", "借出日期"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
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


    def find_borrower_and_records(self):
        """查询借书证信息、借阅记录、借阅习惯和推荐图书"""
        card_no = self.card_no_input.text().strip()
        if not card_no:
            QMessageBox.warning(self, "输入错误", "请输入借书证卡号！")
            self.reset_return_state()
            return

        card_query = "SELECT Name, Department, CardType FROM LibraryCard WHERE CardNo = %s"
        card_info = execute_query(card_query, (card_no,))
        if not card_info:
            QMessageBox.warning(self, "查询失败", f"未找到卡号为 '{card_no}' 的借书证！")
            self.reset_return_state()
            return

        borrower = card_info[0]
        self.borrower_info_label.setText(f"持卡人: {borrower.get('Name', 'N/A')} ({borrower.get('Department','N/A')} - {borrower.get('CardType','N/A')})")
        self.borrower_info_label.setStyleSheet("font-style: normal; color: green;")
        self.current_card_no = card_no
        self.return_button.setEnabled(True)
        self.book_no_input.setFocus()

        self.load_current_borrowed_books(card_no)
        self.load_borrowing_habit(card_no)

        if self.most_common_book_type:
            self.load_recommendations(card_no, self.most_common_book_type)
        else:
            self.recommendation_group.setVisible(False)


    def load_current_borrowed_books(self, card_no):
        """根据卡号加载当前借阅中的图书列表"""
        records_query = """
        SELECT lr.FID, lr.BookNo, b.BookName, b.Author, lr.LentDate
        FROM LibraryRecords lr
        JOIN Books b ON lr.BookNo = b.BookNo
        WHERE lr.CardNo = %s AND lr.ReturnDate IS NULL
        ORDER BY lr.LentDate ASC
        """
        results = execute_query(records_query, (card_no,))
        self.populate_borrowed_table(results)
        self.current_borrowed_records.clear()
        if results:
            for record in results:
                self.current_borrowed_records[record['FID']] = record

    def populate_borrowed_table(self, data):
        """填充当前借阅表格"""
        self.table_widget.setRowCount(0)
        if data is None or not data:
            return

        self.table_widget.setRowCount(len(data))
        column_keys = ["FID", "BookNo", "BookName", "Author", "LentDate"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = ""
                if value is not None:
                    if isinstance(value, datetime.datetime):
                        display_text = value.strftime('%Y-%m-%d %H:%M')
                    else:
                        display_text = str(value)
                item = QTableWidgetItem(display_text)
                if col_index == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table_widget.setItem(row_index, col_index, item)

    def reset_return_state(self):
        """重置还书相关状态和控件"""
        self.current_card_no = None
        self.borrower_info_label.setText("持卡人信息: N/A")
        self.borrower_info_label.setStyleSheet("font-style: italic; color: gray;")
        self.habit_label.setText("最常借阅类别: N/A")
        self.habit_label.setStyleSheet("font-style: italic; color: gray;")
        self.most_common_book_type = None
        self.recommendation_group.setVisible(False)
        self.recommendation_text.clear()
        self.return_button.setEnabled(False)
        self.table_widget.setRowCount(0)
        self.current_borrowed_records.clear()

    def load_borrowing_habit(self, card_no):
        """查询并显示最常借阅类别，并存储该类别"""
        query = """
        SELECT b.BookType, COUNT(lr.FID) AS BorrowCount
        FROM LibraryRecords lr
        JOIN Books b ON lr.BookNo = b.BookNo
        WHERE lr.CardNo = %s AND b.BookType IS NOT NULL AND b.BookType != ''
        GROUP BY b.BookType
        ORDER BY BorrowCount DESC
        LIMIT 1
        """
        result = execute_query(query, (card_no,))

        if result:
            self.most_common_book_type = result[0]['BookType']
            borrow_count = result[0]['BorrowCount']
            self.habit_label.setText(f"最常借阅类别: {self.most_common_book_type} ({borrow_count}次)")
            self.habit_label.setStyleSheet("font-style: normal; color: #2980b9;")
        else:
            self.most_common_book_type = None
            self.habit_label.setText("最常借阅类别: 暂无足够数据")
            self.habit_label.setStyleSheet("font-style: italic; color: gray;")

    def load_recommendations(self, card_no, book_type, limit=5):
        """根据指定类别，推荐用户未借阅过且有库存的图书"""
        query = """
        SELECT b.BookNo, b.BookName, b.Author
        FROM Books b
        WHERE b.BookType = %s
          AND b.Storage > 0
          AND b.BookNo NOT IN (
              SELECT DISTINCT lr.BookNo
              FROM LibraryRecords lr
              WHERE lr.CardNo = %s
          )
        ORDER BY b.Year DESC
        LIMIT %s
        """
        results = execute_query(query, (book_type, card_no, limit))

        if results:
            recommendations = ["根据您常借阅的类别，为您推荐："]
            for book in results:
                recommendations.append(f"- 《{book['BookName']}》 作者: {book.get('Author', 'N/A')} (ID: {book['BookNo']})")
            self.recommendation_text.setText("\n".join(recommendations))
            self.recommendation_group.setVisible(True)
        else:
            self.recommendation_text.setText(f"暂无更多 '{book_type}' 类别的推荐。")
            self.recommendation_group.setVisible(True)

    def perform_return(self):
        """执行还书操作"""
        if not self.current_card_no:
            QMessageBox.warning(self, "操作无效", "请先查询并确认有效的借书证卡号！")
            return
        book_no_to_return = self.book_no_input.text().strip()
        if not book_no_to_return:
            QMessageBox.warning(self, "输入错误", "请输入要归还的图书书号(ID)！")
            return

        record_to_return = None
        record_fid = None
        for fid, record in self.current_borrowed_records.items():
            if record['BookNo'] == book_no_to_return:
                record_to_return = record
                record_fid = fid
                break
        if record_to_return is None:
            QMessageBox.warning(self, "操作失败", f"卡号 {self.current_card_no} 当前未借阅书号为 '{book_no_to_return}' 的图书，或该书已还。")
            return

        # --- 执行还书 ---
        update_record_sql = "UPDATE LibraryRecords SET ReturnDate = %s WHERE FID = %s AND ReturnDate IS NULL"
        update_stock_sql = "UPDATE Books SET Storage = Storage + 1 WHERE BookNo = %s"
        return_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            execute_modify(update_record_sql, (return_date, record_fid))
            execute_modify(update_stock_sql, (book_no_to_return,))

            book_name = record_to_return.get('BookName', '未知书名')
            QMessageBox.information(self, "操作成功", f"图书 '{book_name}' (ID: {book_no_to_return})\n已成功归还！")
            self.book_no_input.clear()
            self.load_current_borrowed_books(self.current_card_no) # 刷新列表
             # 还书后也重新加载推荐
            if self.most_common_book_type:
                 self.load_recommendations(self.current_card_no, self.most_common_book_type)
            self.book_no_input.setFocus()

        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"还书操作失败：\n{e}")
            # 尝试回滚记录状态
            rollback_record_sql = "UPDATE LibraryRecords SET ReturnDate = NULL WHERE FID = %s"
            try:
                 check_record_sql = "SELECT ReturnDate FROM LibraryRecords WHERE FID = %s"
                 record_status = execute_query(check_record_sql, (record_fid,))
                 if record_status and record_status[0]['ReturnDate'] is not None:
                     execute_modify(rollback_record_sql, (record_fid,))
                     print(f"还书操作失败，已尝试回滚借阅记录 {record_fid} 的 ReturnDate。")
            except Exception as rollback_e:
                 print(f"!!! 严重错误：回滚借阅记录 {record_fid} 的 ReturnDate 失败：{rollback_e} !!! 数据可能不一致！")
                 QMessageBox.critical(self, "严重错误", "还书操作失败，且记录状态回滚失败！请联系管理员处理。")

# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    return_page = ReturnPage()
    layout.addWidget(return_page)
    window.setWindowTitle("还书管理页面测试 (含推荐)")
    window.resize(750, 650) # 调整大小
    window.show()
    sys.exit(app.exec())
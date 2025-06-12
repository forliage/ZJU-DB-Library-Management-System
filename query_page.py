# query_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QSpacerItem, QSizePolicy, QGroupBox # 导入 QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import datetime # 虽然这个页面目前没直接用，但保留导入以防万一

# 假设 db_utils.py 在同一目录下或 PYTHONPATH 中
try:
    from db_utils import execute_query
except ImportError:
    print("错误：无法从 db_utils 导入 execute_query。")
    def execute_query(query, params=None): return None

class QueryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_fields = {} # 初始化查询字段字典
        self.setup_ui()
        self.load_initial_data() # 页面加载时载入初始数据
        self.load_borrow_ranking() # 添加：加载借阅排行

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15) # 页面边距
        main_layout.setSpacing(10) # 控件间距

        # --- 查询条件区域 ---
        search_group = QWidget() # 使用一个 QWidget 来组织查询条件
        search_layout = QHBoxLayout(search_group)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        # 书名
        search_layout.addWidget(QLabel("书名:"))
        self.search_fields['BookName'] = QLineEdit()
        self.search_fields['BookName'].setPlaceholderText("模糊查询书名")
        search_layout.addWidget(self.search_fields['BookName'])

        # 作者
        search_layout.addWidget(QLabel("作者:"))
        self.search_fields['Author'] = QLineEdit()
        self.search_fields['Author'].setPlaceholderText("模糊查询作者")
        search_layout.addWidget(self.search_fields['Author'])

        # 出版社
        search_layout.addWidget(QLabel("出版社:"))
        self.search_fields['Publisher'] = QLineEdit()
        self.search_fields['Publisher'].setPlaceholderText("模糊查询出版社")
        search_layout.addWidget(self.search_fields['Publisher'])

        # 类别
        search_layout.addWidget(QLabel("类别:"))
        self.search_fields['BookType'] = QLineEdit()
        self.search_fields['BookType'].setPlaceholderText("输入类别")
        search_layout.addWidget(self.search_fields['BookType'])

        # 添加查询按钮和清空按钮
        self.search_button = QPushButton("查询")
        self.clear_button = QPushButton("清空")
        self.search_button.setStyleSheet("padding: 5px 15px;") # 按钮样式
        self.clear_button.setStyleSheet("padding: 5px 15px;")
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)

        main_layout.addWidget(search_group)

        # --- 中部布局: 查询结果 和 排行榜 上下排列 ---
        middle_layout = QVBoxLayout() # 创建一个新的垂直布局放表格
        middle_layout.setSpacing(15) # 设置表格间距

        # --- 查询结果显示表格 ---
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(9) # 根据数据库字段设置列数
        self.table_widget.setHorizontalHeaderLabels([
            "书号(ID)", "类别", "书名", "出版社", "年份", "作者", "价格", "总数", "库存"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # 列宽自适应伸展
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # 书名列可手动调整
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # 出版社列可手动调整
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # 作者列可手动调整
        self.table_widget.verticalHeader().setVisible(False) # 隐藏行号
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # 禁止编辑
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # 整行选择
        self.table_widget.setAlternatingRowColors(True) # 隔行变色
        self.table_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: #dcdcdc; /* 网格线颜色 */
                alternate-background-color: #f8f8f8; /* 隔行背景色 */
            }
            QHeaderView::section {
                background-color: #e0e0e0; /* 表头背景色 */
                padding: 4px;
                border: 1px solid #dcdcdc;
                font-weight: bold;
            }
        """)
        middle_layout.addWidget(self.table_widget, 3) # 查询结果占 3 份高度

        # --- 添加借阅排行榜区域 ---
        ranking_group = QGroupBox("热门借阅图书 Top 10")
        ranking_layout = QVBoxLayout(ranking_group)
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(4) # 书号, 书名, 作者, 借阅次数
        self.ranking_table.setHorizontalHeaderLabels(["书号(ID)", "书名", "作者", "借阅次数"])
        rank_header = self.ranking_table.horizontalHeader()
        rank_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rank_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # 书名可调
        self.ranking_table.verticalHeader().setVisible(False)
        self.ranking_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ranking_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ranking_table.setAlternatingRowColors(True)
        self.ranking_table.setMaximumHeight(250) # 限制最大高度
        self.ranking_table.setStyleSheet("""
            QTableWidget { gridline-color: #dcdcdc; alternate-background-color: #f8f8f8; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #dcdcdc; font-weight: bold;}
        """)
        ranking_layout.addWidget(self.ranking_table)
        middle_layout.addWidget(ranking_group, 1) # 排行榜占 1 份高度

        main_layout.addLayout(middle_layout) # 将中部布局添加到主布局

        # --- 连接信号和槽 ---
        self.search_button.clicked.connect(self.perform_search)
        self.clear_button.clicked.connect(self.clear_search_fields)
        for field in self.search_fields.values():
            if isinstance(field, QLineEdit):
                field.returnPressed.connect(self.perform_search)

    def load_initial_data(self):
        """加载初始数据 (例如，显示所有图书或最近添加的图书)"""
        self.perform_search(initial_load=True)

    def perform_search(self, initial_load=False):
        """执行查询操作"""
        base_query = "SELECT BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage FROM Books WHERE 1=1"
        conditions = []
        params = []

        if not initial_load: # 如果不是初始加载，才根据条件查询
            criteria = {name: field.text().strip() for name, field in self.search_fields.items() if isinstance(field, QLineEdit)}

            if criteria.get('BookName'):
                conditions.append("BookName LIKE %s")
                params.append(f"%{criteria['BookName']}%")
            if criteria.get('Author'):
                conditions.append("Author LIKE %s")
                params.append(f"%{criteria['Author']}%")
            if criteria.get('Publisher'):
                conditions.append("Publisher LIKE %s")
                params.append(f"%{criteria['Publisher']}%")
            if criteria.get('BookType'):
                conditions.append("BookType LIKE %s")
                params.append(f"%{criteria['BookType']}%")

        if conditions:
            final_query = base_query + " AND " + " AND ".join(conditions)
        else:
            final_query = base_query

        final_query += " ORDER BY UpdateTime DESC LIMIT 500"

        print(f"Executing query: {final_query} with params: {params}")
        results = execute_query(final_query, tuple(params))
        self.populate_table(results)

    def populate_table(self, data):
        """将查询结果填充到 QTableWidget"""
        self.table_widget.setRowCount(0)

        if data is None:
            QMessageBox.critical(self, "查询错误", "从数据库获取数据时发生错误！")
            return
        if not data:
            print("数据库中没有找到匹配的记录。")
            return

        self.table_widget.setRowCount(len(data))
        column_keys = ["BookNo", "BookType", "BookName", "Publisher", "Year", "Author", "Price", "Total", "Storage"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = ""
                if value is None:
                    display_text = ""
                elif isinstance(value, (int, float)):
                    if key == 'Price' and value is not None:
                         display_text = f"{value:.2f}"
                    else:
                        display_text = str(value)
                elif isinstance(value, datetime.datetime): # 处理时间戳或日期时间类型
                     display_text = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    display_text = str(value)

                item = QTableWidgetItem(display_text)
                if isinstance(value, (int, float)):
                     item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                     item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if key == 'Storage' and isinstance(value, int) and value < 3:
                    item.setForeground(QColor('red'))
                self.table_widget.setItem(row_index, col_index, item)

    def clear_search_fields(self):
        """清空所有查询条件输入框"""
        for field in self.search_fields.values():
            if isinstance(field, QLineEdit):
                field.clear()
        self.table_widget.setRowCount(0)
        self.load_initial_data()

    def load_borrow_ranking(self, top_n=10):
        """查询并加载借阅次数最多的图书"""
        query = """
        SELECT
            lr.BookNo,
            b.BookName,
            b.Author,
            COUNT(lr.FID) AS BorrowCount
        FROM LibraryRecords lr
        JOIN Books b ON lr.BookNo = b.BookNo
        GROUP BY lr.BookNo, b.BookName, b.Author
        ORDER BY BorrowCount DESC
        LIMIT %s
        """
        results = execute_query(query, (top_n,))
        self.populate_ranking_table(results)

    def populate_ranking_table(self, data):
        """填充排行榜表格"""
        self.ranking_table.setRowCount(0)
        if data is None or not data:
            self.ranking_table.setRowCount(1)
            no_rank_item = QTableWidgetItem("暂无借阅排行数据")
            no_rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ranking_table.setItem(0, 0, no_rank_item)
            self.ranking_table.setSpan(0, 0, 1, self.ranking_table.columnCount())
            return

        self.ranking_table.setRowCount(len(data))
        column_keys = ["BookNo", "BookName", "Author", "BorrowCount"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = str(value) if value is not None else ""
                item = QTableWidgetItem(display_text)
                if key == 'BorrowCount':
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.ranking_table.setItem(row_index, col_index, item)

# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    query_page = QueryPage()
    layout.addWidget(query_page)
    window.setWindowTitle("图书查询页面测试 (含排行榜)")
    window.resize(800, 700) # 增加高度以容纳排行榜
    window.show()
    sys.exit(app.exec())
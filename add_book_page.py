# add_book_page.py
import csv
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGridLayout, QGroupBox, QSpacerItem, QSizePolicy, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# 假设 db_utils.py 在同一目录下或 PYTHONPATH 中
try:
    from db_utils import execute_query, execute_modify
except ImportError:
    print("错误：无法从 db_utils 导入数据库函数。")
    def execute_query(query, params=None): return None
    def execute_modify(query, params=None): return None


class AddBookPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_recent_books() # 页面加载时显示最近入库的书籍

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- 上方区域：包含单本入库和批量导入 ---
        top_layout = QHBoxLayout()

        # --- 1. 单本图书入库区域 ---
        single_entry_group = QGroupBox("单本图书入库")
        single_entry_layout = QGridLayout(single_entry_group)
        single_entry_layout.setSpacing(10)

        self.entry_fields = {} # 存储输入框控件

        # 定义输入字段: (标签文本, 控件名, 行, 列, 列跨度)
        fields_info = [
            ("书号(ID)*:", 'BookNo', 0, 0, 1),
            ("类别:", 'BookType', 0, 2, 1),
            ("书名*:", 'BookName', 1, 0, 3), # 书名跨3列
            ("出版社:", 'Publisher', 2, 0, 1),
            ("年份:", 'Year', 2, 2, 1),
            ("作者:", 'Author', 3, 0, 1),
            ("价格:", 'Price', 3, 2, 1),
            ("数量*:", 'Quantity', 4, 0, 1),
        ]

        for label_text, name, row, col, col_span in fields_info:
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"输入{label_text.replace(':', '').replace('*', '')}")
            # 标记必填项
            if '*' in label_text:
                 line_edit.setProperty("required", True) # 自定义属性标记

            self.entry_fields[name] = line_edit
            single_entry_layout.addWidget(label, row, col * 2) # 标签占一列
            single_entry_layout.addWidget(line_edit, row, col * 2 + 1, 1, col_span * 2 -1) # 输入框占剩余列

        # 添加单本入库按钮
        self.add_single_button = QPushButton("添加单本图书")
        self.add_single_button.setStyleSheet("padding: 8px 15px; font-size: 14px;")
        single_entry_layout.addWidget(self.add_single_button, 5, 0, 1, 4) # 按钮跨4列

        top_layout.addWidget(single_entry_group, 2) # 单本入库占 2/3 宽度

        # --- 2. 批量导入区域 ---
        batch_import_group = QGroupBox("批量导入图书")
        batch_import_layout = QVBoxLayout(batch_import_group)
        batch_import_layout.setSpacing(10)
        batch_import_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # 顶部对齐

        import_label = QLabel("从 CSV/TXT 文件导入：\n文件格式: 书号,类别,书名,出版社,年份,作者,价格,数量\n(逗号分隔, UTF-8编码, 无表头)")
        import_label.setWordWrap(True) # 自动换行
        self.import_file_path_label = QLabel("未选择文件") # 显示选择的文件路径
        self.import_file_path_label.setStyleSheet("font-style: italic; color: gray;")
        self.select_file_button = QPushButton("选择文件")
        self.start_import_button = QPushButton("开始导入")
        self.start_import_button.setEnabled(False) # 初始不可用

        batch_import_layout.addWidget(import_label)
        batch_import_layout.addWidget(self.import_file_path_label)
        btn_layout = QHBoxLayout() # 横向布局放按钮
        btn_layout.addWidget(self.select_file_button)
        btn_layout.addWidget(self.start_import_button)
        batch_import_layout.addLayout(btn_layout)
        batch_import_layout.addStretch() # 添加伸缩，使控件靠上

        top_layout.addWidget(batch_import_group, 1) # 批量导入占 1/3 宽度

        main_layout.addLayout(top_layout)

        # --- 3. 最近入库显示表格 ---
        recent_group = QGroupBox("最近入库记录")
        recent_layout = QVBoxLayout(recent_group)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(9) # 与查询页面保持一致
        self.table_widget.setHorizontalHeaderLabels([
            "书号(ID)", "类别", "书名", "出版社", "年份", "作者", "价格", "总数", "库存"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget { gridline-color: #dcdcdc; alternate-background-color: #f8f8f8; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #dcdcdc; font-weight: bold;}
        """)
        recent_layout.addWidget(self.table_widget)
        main_layout.addWidget(recent_group)

        # --- 连接信号和槽 ---
        self.add_single_button.clicked.connect(self.add_single_book)
        self.select_file_button.clicked.connect(self.select_import_file)
        self.start_import_button.clicked.connect(self.start_batch_import)

    def load_recent_books(self, limit=50):
        """加载最近入库的图书"""
        query = "SELECT BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage FROM Books ORDER BY UpdateTime DESC LIMIT %s"
        results = execute_query(query, (limit,))
        self.populate_table(results)

    def populate_table(self, data):
        """填充表格数据 (与QueryPage类似)"""
        self.table_widget.setRowCount(0)
        if data is None or not data:
            return

        self.table_widget.setRowCount(len(data))
        column_keys = ["BookNo", "BookType", "BookName", "Publisher", "Year", "Author", "Price", "Total", "Storage"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = ""
                if value is not None:
                    if isinstance(value, float) and key == 'Price':
                        display_text = f"{value:.2f}"
                    else:
                        display_text = str(value)

                item = QTableWidgetItem(display_text)
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table_widget.setItem(row_index, col_index, item)

    def validate_single_entry(self):
        """校验单本入库的输入字段"""
        book_data = {}
        for name, field in self.entry_fields.items():
            text = field.text().strip()
            # 检查必填项
            if field.property("required") and not text:
                QMessageBox.warning(self, "输入错误", f"请填写必填项：{field.placeholderText()}")
                field.setFocus()
                return None

            # 类型和格式校验
            if name == 'Year' and text and not text.isdigit():
                QMessageBox.warning(self, "输入错误", "年份必须是纯数字！")
                field.setFocus()
                return None
            if name == 'Price' and text:
                try:
                    float(text) # 尝试转换为浮点数
                except ValueError:
                    QMessageBox.warning(self, "输入错误", "价格必须是有效的数字！")
                    field.setFocus()
                    return None
            if name == 'Quantity' and text:
                 if not text.isdigit() or int(text) <= 0:
                    QMessageBox.warning(self, "输入错误", "数量必须是大于0的整数！")
                    field.setFocus()
                    return None
                 # 对于单本入库，数量就是 Total 和 Storage
                 book_data['Total'] = int(text)
                 book_data['Storage'] = int(text)

            # 存储有效值 (年份和价格可能为空)
            if text:
                if name == 'Year':
                    book_data[name] = int(text)
                elif name == 'Price':
                    book_data[name] = float(text)
                elif name != 'Quantity': # Quantity 已处理
                    book_data[name] = text
            else:
                 book_data[name] = None # 对于非必填项，空字符串存为 None

        # 确保 Quantity 被处理
        if 'Quantity' not in book_data and self.entry_fields['Quantity'].property('required'):
             QMessageBox.warning(self, "输入错误", "请填写必填项：数量")
             self.entry_fields['Quantity'].setFocus()
             return None
        elif 'Quantity' in self.entry_fields and not self.entry_fields['Quantity'].text().strip() and self.entry_fields['Quantity'].property('required'):
             QMessageBox.warning(self, "输入错误", "请填写必填项：数量")
             self.entry_fields['Quantity'].setFocus()
             return None

        return book_data

    def add_single_book(self):
        """处理添加单本图书按钮点击"""
        book_data = self.validate_single_entry()
        if book_data is None:
            return # 校验失败

        book_no = book_data.get('BookNo')
        book_name = book_data.get('BookName')

        # --- 检查书号是否已存在 ---
        check_sql = "SELECT BookNo FROM Books WHERE BookNo = %s"
        existing = execute_query(check_sql, (book_no,))
        if existing:
            QMessageBox.warning(self, "操作失败", f"书号(ID) '{book_no}' 已存在，无法重复添加！")
            self.entry_fields['BookNo'].setFocus()
            return

        # --- 构造插入 SQL ---
        sql = """
        INSERT INTO Books (BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            book_data.get('BookNo'),
            book_data.get('BookType'),
            book_data.get('BookName'),
            book_data.get('Publisher'),
            book_data.get('Year'),
            book_data.get('Author'),
            book_data.get('Price'),
            book_data.get('Total'),
            book_data.get('Storage')
        )

        # --- 执行插入 ---
        try:
            execute_modify(sql, params)
            QMessageBox.information(self, "操作成功", f"图书 '{book_name}' 已成功入库！")
            # 清空输入框
            for field in self.entry_fields.values():
                field.clear()
            # 刷新表格显示
            self.load_recent_books()
            self.entry_fields['BookNo'].setFocus() # 将焦点设置回书号，方便连续输入

        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"图书入库时发生错误：\n{e}")


    def select_import_file(self):
        """打开文件选择对话框"""
        # 获取用户主目录或当前工作目录作为起始路径
        start_path = os.path.expanduser("~") or os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择导入文件",
            start_path, # 起始目录
            "CSV 文件 (*.csv);;文本文件 (*.txt);;所有文件 (*)" # 文件过滤器
        )
        if file_path:
            self.import_file_path = file_path
            # 在标签上只显示文件名，避免路径过长
            self.import_file_path_label.setText(f"已选: {os.path.basename(file_path)}")
            self.import_file_path_label.setStyleSheet("font-style: normal; color: black;") # 恢复正常样式
            self.start_import_button.setEnabled(True) # 启用开始导入按钮
        else:
            self.import_file_path = None
            self.import_file_path_label.setText("未选择文件")
            self.import_file_path_label.setStyleSheet("font-style: italic; color: gray;")
            self.start_import_button.setEnabled(False)

    def start_batch_import(self):
        """开始执行批量导入"""
        if not hasattr(self, 'import_file_path') or not self.import_file_path:
            QMessageBox.warning(self, "错误", "请先选择要导入的文件！")
            return

        success_count = 0
        fail_count = 0
        duplicate_count = 0
        line_num = 0
        errors = [] # 收集错误信息

        try:
            with open(self.import_file_path, 'r', encoding='utf-8') as csvfile:
                # 使用 csv.reader 处理逗号分隔，可以更好地处理包含逗号的字段（如果用引号包围）
                reader = csv.reader(csvfile)
                # next(reader) # 如果文件包含表头，跳过第一行

                for row in reader:
                    line_num += 1
                    if len(row) != 8: # 检查列数是否符合预期 (书号,类别,书名,出版社,年份,作者,价格,数量)
                        errors.append(f"第 {line_num} 行格式错误：列数 ({len(row)}) 不为 8。")
                        fail_count += 1
                        continue

                    # 数据清洗和转换
                    book_no, book_type, book_name, publisher, year_str, author, price_str, quantity_str = map(str.strip, row)

                    # 基础校验
                    if not book_no or not book_name or not quantity_str:
                         errors.append(f"第 {line_num} 行错误：书号、书名或数量不能为空。")
                         fail_count += 1
                         continue

                    try:
                        year = int(year_str) if year_str else None
                        price = float(price_str) if price_str else None
                        quantity = int(quantity_str)
                        if quantity <= 0: raise ValueError("数量必须大于0")
                    except ValueError as ve:
                        errors.append(f"第 {line_num} 行错误 (书号: {book_no}): 年份、价格或数量格式无效 - {ve}。")
                        fail_count += 1
                        continue

                    # 检查书号是否重复
                    check_sql = "SELECT BookNo FROM Books WHERE BookNo = %s"
                    existing = execute_query(check_sql, (book_no,))
                    if existing:
                        # errors.append(f"第 {line_num} 行跳过 (书号: {book_no}): 图书已存在。")
                        duplicate_count += 1
                        continue # 跳过重复项

                    # 构造插入 SQL
                    sql = """
                    INSERT INTO Books (BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (book_no, book_type or None, book_name, publisher or None, year, author or None, price, quantity, quantity) # 数量同时作为 Total 和 Storage

                    # 执行插入
                    try:
                        execute_modify(sql, params)
                        success_count += 1
                    except Exception as db_err:
                        errors.append(f"第 {line_num} 行错误 (书号: {book_no}): 数据库插入失败 - {db_err}。")
                        fail_count += 1

        except FileNotFoundError:
            QMessageBox.critical(self, "文件错误", f"文件未找到：{self.import_file_path}")
            return
        except Exception as e:
            QMessageBox.critical(self, "导入错误", f"处理文件时发生未知错误：\n{e}")
            return

        # 显示导入结果报告
        report_message = f"批量导入完成！\n\n成功导入: {success_count} 条\n失败或格式错误: {fail_count} 条\n因书号重复跳过: {duplicate_count} 条"
        if errors:
            # 如果错误数量不多，直接显示；如果过多，提示查看日志或只显示前几条
            error_details = "\n\n部分错误详情:\n" + "\n".join(errors[:10]) # 最多显示10条错误
            if len(errors) > 10:
                error_details += f"\n...(还有 {len(errors) - 10} 条错误未显示)"
            report_message += error_details

        QMessageBox.information(self, "导入结果", report_message)

        # 重置文件选择状态
        self.import_file_path = None
        self.import_file_path_label.setText("未选择文件")
        self.import_file_path_label.setStyleSheet("font-style: italic; color: gray;")
        self.start_import_button.setEnabled(False)

        # 刷新表格
        self.load_recent_books()


# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    add_book_page = AddBookPage()
    layout.addWidget(add_book_page)
    window.setWindowTitle("图书入库页面测试")
    window.resize(900, 700) # 调整窗口大小以容纳布局
    window.show()
    sys.exit(app.exec())
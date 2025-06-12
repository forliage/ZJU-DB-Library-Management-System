# card_manage_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QComboBox, QTextEdit # 导入 QTextEdit 用于显示统计信息
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor # 导入 QColor
import datetime # 需要 datetime 来比较日期

# 假设 db_utils.py 在可访问路径
try:
    from db_utils import execute_query, execute_modify
except ImportError as e:
    print(f"错误：导入数据库工具时出错 - {e}")
    def execute_query(query, params=None): return None
    def execute_modify(query, params=None): return None

class CardManagePage(QWidget):
    # 假设借阅期限（天），与 OverduePage 一致
    BORROW_DURATION_DAYS = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_fields = {} # 初始化添加字段字典
        self.setup_ui()
        self.load_cards() # 页面加载时显示所有借书证

    def setup_ui(self):
        main_layout = QHBoxLayout(self) # 改为主水平布局
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- 左侧区域：添加和列表 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0) # 子布局无外边距
        left_layout.setSpacing(15)

        # 添加新借书证区域
        add_group = QGroupBox("添加新借书证")
        add_layout = QHBoxLayout(add_group) # 横向布局
        add_layout.setSpacing(10)

        # 输入字段: (标签, 控件名, 占位符, 是否下拉框)
        fields_info = [
            ("卡号*:", 'CardNo', "输入唯一卡号", False),
            ("姓名*:", 'Name', "输入姓名", False),
            ("单位/部门:", 'Department', "输入单位或部门", False),
            ("类别*:", 'CardType', "", True), # 类别使用下拉框
        ]

        for label_text, name, placeholder, is_combo in fields_info:
            label = QLabel(label_text)
            add_layout.addWidget(label)
            if is_combo:
                combo = QComboBox()
                combo.addItems(["学生", "教师", "职工", "其他"])
                self.add_fields[name] = combo
                add_layout.addWidget(combo, 1) # 下拉框占1份宽度
            else:
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(placeholder)
                if '*' in label_text:
                    line_edit.setProperty("required", True)
                self.add_fields[name] = line_edit
                add_layout.addWidget(line_edit, 1) # 输入框占1份宽度

        # 添加按钮
        self.add_card_button = QPushButton("添加借书证")
        self.add_card_button.setStyleSheet("padding: 5px 15px;")
        self.add_card_button.clicked.connect(self.add_card)
        add_layout.addWidget(self.add_card_button)
        left_layout.addWidget(add_group) # 添加到左侧布局

        # 现有借书证列表区域
        display_group = QGroupBox("现有借书证列表 (单击行查看统计)") # 修改标题提示
        display_layout = QVBoxLayout(display_group)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5) # 卡号, 姓名, 单位, 类别, 更新时间
        self.table_widget.setHorizontalHeaderLabels([
            "卡号", "姓名", "单位/部门", "类别", "更新时间"
        ])
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # 自适应列宽
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # 单位可调
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # 时间可调
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # 整行选择
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget { gridline-color: #dcdcdc; alternate-background-color: #f8f8f8; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid #dcdcdc; font-weight: bold;}
        """)
        # 连接单元格选择变化信号
        self.table_widget.itemSelectionChanged.connect(self.display_reader_stats)
        display_layout.addWidget(self.table_widget)

        # 删除按钮
        self.delete_card_button = QPushButton("删除选中的借书证")
        self.delete_card_button.setStyleSheet("padding: 5px 15px; background-color: #c0392b; color: white;") # 红色
        self.delete_card_button.clicked.connect(self.delete_selected_card)
        delete_button_layout = QHBoxLayout()
        delete_button_layout.addStretch() # 添加弹性空间
        delete_button_layout.addWidget(self.delete_card_button)
        display_layout.addLayout(delete_button_layout)
        left_layout.addWidget(display_group) # 添加到左侧布局

        main_layout.addWidget(left_widget, 2) # 左侧占 2 份宽度

        # --- 右侧区域：读者画像统计信息 ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # 顶部对齐
        right_layout.setSpacing(10)

        stats_group = QGroupBox("读者借阅统计")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("请在左侧表格中选择一个读者查看统计信息。")
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_label.setStyleSheet("padding: 10px; font-style: italic; color: gray;")
        stats_layout.addWidget(self.stats_label)

        # 使用 QTextEdit 显示更详细的统计
        self.stats_text_edit = QTextEdit()
        self.stats_text_edit.setReadOnly(True)
        self.stats_text_edit.setFont(QFont("SimSun", 11)) # 宋体，11号
        self.stats_text_edit.setVisible(False) # 初始隐藏
        stats_layout.addWidget(self.stats_text_edit)

        right_layout.addWidget(stats_group)
        main_layout.addWidget(right_widget, 1) # 右侧占 1 份宽度

    def load_cards(self):
        """加载所有借书证信息到表格"""
        query = "SELECT CardNo, Name, Department, CardType, UpdateTime FROM LibraryCard ORDER BY UpdateTime DESC"
        results = execute_query(query)
        self.populate_table(results)

    def populate_table(self, data):
        """填充借书证表格"""
        self.table_widget.setRowCount(0) # 清空旧数据
        if data is None:
            QMessageBox.critical(self, "查询错误", "获取借书证列表时发生错误！")
            return
        if not data:
            return # 没有数据则显示空表

        self.table_widget.setRowCount(len(data))
        column_keys = ["CardNo", "Name", "Department", "CardType", "UpdateTime"]
        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(column_keys):
                value = row_data.get(key)
                display_text = ""
                if value is not None:
                     # 格式化时间
                    if isinstance(value, datetime.datetime): # 检查是否是 datetime 对象
                        display_text = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        display_text = str(value)

                item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table_widget.setItem(row_index, col_index, item)

    def validate_add_input(self):
        """校验添加借书证的输入"""
        card_data = {}
        for name, field in self.add_fields.items():
            if isinstance(field, QLineEdit):
                value = field.text().strip()
                if field.property("required") and not value:
                    QMessageBox.warning(self, "输入错误", f"请填写必填项：{field.placeholderText()}")
                    field.setFocus()
                    return None
                card_data[name] = value if value else None
            elif isinstance(field, QComboBox):
                value = field.currentText()
                if not value: # 理论上 ComboBox 总有当前文本
                    QMessageBox.warning(self, "选择错误", f"请选择类别！")
                    field.setFocus()
                    return None
                card_data[name] = value

        # 卡号唯一性校验
        card_no_to_check = card_data.get('CardNo')
        if not card_no_to_check: # 再次确认卡号非空
             QMessageBox.warning(self, "输入错误", "卡号不能为空！")
             self.add_fields['CardNo'].setFocus()
             return None

        check_sql = "SELECT CardNo FROM LibraryCard WHERE CardNo = %s"
        existing = execute_query(check_sql, (card_no_to_check,))
        if existing:
            QMessageBox.warning(self, "操作失败", f"卡号 '{card_no_to_check}' 已存在，请使用其他卡号！")
            self.add_fields['CardNo'].setFocus()
            return None

        return card_data

    def add_card(self):
        """添加新的借书证"""
        card_data = self.validate_add_input()
        if card_data is None:
            return # 校验失败或卡号重复

        sql = """
        INSERT INTO LibraryCard (CardNo, Name, Department, CardType)
        VALUES (%s, %s, %s, %s)
        """
        params = (
            card_data.get('CardNo'),
            card_data.get('Name'),
            card_data.get('Department'),
            card_data.get('CardType')
        )

        try:
            execute_modify(sql, params)
            QMessageBox.information(self, "操作成功", f"借书证 '{card_data.get('CardNo')}' 添加成功！")
            # 清空输入框
            for name, field in self.add_fields.items():
                if isinstance(field, QLineEdit):
                    field.clear()
                elif isinstance(field, QComboBox):
                    field.setCurrentIndex(0) # 重置为第一个选项
            # 刷新表格
            self.load_cards()
            self.add_fields['CardNo'].setFocus() # 焦点设置回卡号

        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"添加借书证时发生错误：\n{e}")


    def delete_selected_card(self):
        """删除表格中选中的借书证"""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "操作无效", "请先在表格中选中要删除的借书证！")
            return

        selected_row_index = selected_rows[0].row()
        card_no_item = self.table_widget.item(selected_row_index, 0) # 卡号在第一列
        name_item = self.table_widget.item(selected_row_index, 1)    # 姓名在第二列

        if not card_no_item:
            QMessageBox.critical(self, "错误", "无法获取选中行的卡号信息！")
            return

        card_no_to_delete = card_no_item.text()
        name_to_delete = name_item.text() if name_item else ""

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除卡号为 '{card_no_to_delete}' (姓名: {name_to_delete}) 的借书证吗？\n\n"
            f"警告：删除借书证可能会导致关联的借阅记录也被删除或更新 (取决于数据库外键设置)。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No # 默认选中 No
        )

        if reply == QMessageBox.StandardButton.Yes:
            delete_sql = "DELETE FROM LibraryCard WHERE CardNo = %s"
            try:
                execute_modify(delete_sql, (card_no_to_delete,))
                QMessageBox.information(self, "操作成功", f"借书证 '{card_no_to_delete}' 已成功删除！")
                self.load_cards() # 刷新表格
                self.clear_stats_display() # 清空右侧统计显示
            except Exception as e:
                QMessageBox.critical(self, "数据库错误", f"删除借书证时发生错误：\n{e}")

    def display_reader_stats(self):
        """当表格选择变化时，查询并显示选中读者的统计信息"""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_stats_display()
            return

        selected_row_index = selected_rows[0].row()
        card_no_item = self.table_widget.item(selected_row_index, 0)
        name_item = self.table_widget.item(selected_row_index, 1)

        if not card_no_item:
            self.clear_stats_display()
            return

        card_no = card_no_item.text()
        reader_name = name_item.text() if name_item else "未知"

        # --- 查询统计数据 ---
        # 1. 累计借阅次数
        total_borrow_query = "SELECT COUNT(FID) AS TotalCount FROM LibraryRecords WHERE CardNo = %s"
        total_result = execute_query(total_borrow_query, (card_no,))
        total_count = total_result[0]['TotalCount'] if total_result else 0

        # 2. 当前借阅数量
        current_borrow_query = "SELECT COUNT(FID) AS CurrentCount FROM LibraryRecords WHERE CardNo = %s AND ReturnDate IS NULL"
        current_result = execute_query(current_borrow_query, (card_no,))
        current_count = current_result[0]['CurrentCount'] if current_result else 0

        # 3. 是否有逾期记录 (使用数据库日期函数)
        overdue_query = f"""
        SELECT COUNT(FID) AS OverdueCount
        FROM LibraryRecords
        WHERE CardNo = %s
          AND ReturnDate IS NULL
          AND LentDate < DATE_SUB(CURDATE(), INTERVAL {self.BORROW_DURATION_DAYS} DAY)
        """
        overdue_result = execute_query(overdue_query, (card_no,))
        overdue_count = overdue_result[0]['OverdueCount'] if overdue_result else 0

        # --- 显示统计信息 ---
        self.stats_label.setVisible(False) # 隐藏初始提示标签
        self.stats_text_edit.setVisible(True) # 显示统计文本框

        stats_html = f"""
        <html><head/><body>
        <p><span style=" font-weight:600;">读者:</span> {reader_name} (卡号: {card_no})</p>
        <hr/>
        <ul style="list-style-type: none; padding-left: 0;">
            <li><span style=" font-weight:600;">累计借阅总次数:</span> {total_count}</li>
            <li><span style=" font-weight:600;">当前借阅中数量:</span> {current_count}</li>
            <li><span style=" font-weight:600;">是否有逾期记录:</span> <span style=" color:{'red' if overdue_count > 0 else 'green'};">{ '是' if overdue_count > 0 else '否'}</span> (逾期 {overdue_count} 本)</li>
        </ul>
        </body></html>
        """
        self.stats_text_edit.setHtml(stats_html) # 使用 HTML 格式化显示

    def clear_stats_display(self):
        """清空右侧的统计信息显示"""
        self.stats_label.setVisible(True) # 显示提示标签
        self.stats_text_edit.setVisible(False) # 隐藏文本框
        self.stats_text_edit.clear() # 清空内容


# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # 不需要单独的窗口和布局来测试，页面本身就是 QWidget
    card_page = CardManagePage()
    card_page.setWindowTitle("借书证管理页面测试 (含统计)")
    card_page.resize(950, 600) # 调整窗口大小以容纳左右布局
    card_page.show()
    sys.exit(app.exec())
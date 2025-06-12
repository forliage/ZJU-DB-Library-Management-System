# ai_assistant_page.py
import requests
from bs4 import BeautifulSoup
import urllib.parse # 用于 URL 编码
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem, QGroupBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal # 使用线程处理网络请求，避免界面卡顿
from PyQt6.QtGui import QFont

# 假设 db_utils.py 在可访问路径
try:
    from db_utils import execute_query
except ImportError as e:
    print(f"错误：导入数据库工具时出错 - {e}")
    def execute_query(query, params=None): return None

# --- 负责执行网络搜索的线程 ---
class SearchThread(QThread):
    # 定义信号，参数类型为 list (搜索结果) 和 str (错误信息)
    results_ready = pyqtSignal(list, str)

    def __init__(self, query):
        super().__init__()
        self.query = query
        self.headers = { # 模拟浏览器
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.is_running = True

    def run(self):
        """执行搜索和解析"""
        error_message = ""
        results = []
        if not self.is_running:
            return

        # 构造百度搜索 URL
        # 添加 "书籍" 或 "小说" 等关键词可能有助于缩小范围
        search_term = f"{self.query} 书籍"
        encoded_query = urllib.parse.quote(search_term)
        url = f"https://www.baidu.com/s?wd={encoded_query}"
        print(f"AI Assistant: Searching URL: {url}") # 调试输出

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding # 或者 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser') # 使用 Python 内建解析器，或尝试 'lxml'

            # 解析百度搜索结果 - 这部分选择器可能因百度改版而失效，需要灵活调整
            # 尝试查找包含标题的常见容器
            # Baidu PC 结果通常在 class="result" 或 class="c-container" 的 div 中
            result_containers = soup.find_all('div', class_=lambda x: x and ('result' in x or 'c-container' in x))

            if not result_containers: # 如果没找到，尝试其他可能的 class
                 result_containers = soup.find_all('div', class_='result-op')

            print(f"AI Assistant: Found {len(result_containers)} result containers.") # 调试输出

            for container in result_containers:
                if not self.is_running: break # 允许提前停止

                # 查找标题链接 <a>
                title_tag = container.find('h3') # 标题通常在 h3 中
                if not title_tag:
                     title_tag = container.find('a') # 有时直接是 a 标签

                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    # 简单规则：如果标题包含书名号《》，则很可能是书名
                    if '《' in title_text and '》' in title_text:
                        # 尝试提取书名号内的内容
                        import re
                        match = re.search(r'《([^》]+)》', title_text)
                        if match:
                            book_title = match.group(1).strip()
                            if book_title and book_title not in results: # 避免重复
                                print(f"AI Assistant: Found potential book: {book_title}") # 调试输出
                                results.append(book_title)
                    # (可选) 补充其他启发式规则，比如标题包含“著”、“作者”、“出版社”等

            if not results:
                 error_message = "未能从搜索结果中提取到明确的书名信息。"

        except requests.exceptions.RequestException as e:
            error_message = f"网络请求失败: {e}"
        except Exception as e:
            error_message = f"解析搜索结果时发生错误: {e}"
        finally:
            if self.is_running:
                self.results_ready.emit(results, error_message) # 发送信号

    def stop(self):
        self.is_running = False

# --- AI 助手页面 ---
class AIAssistantPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_thread = None # 初始化搜索线程变量
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        title_label = QLabel("智能搜书助手")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        info_label = QLabel("请输入关于书籍的任意描述（如内容梗概、人物、作者字号、部分书名等），助手将尝试为您查找相关书籍。")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # 查询输入区域
        search_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("例如：雨果写的关于巴黎圣母院的小说、仲甫写的文章、红楼...")
        self.query_input.returnPressed.connect(self.start_search) # 回车触发搜索
        self.search_button = QPushButton("智能搜索")
        self.search_button.clicked.connect(self.start_search)
        search_layout.addWidget(self.query_input, 1) # 输入框占主要宽度
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # 结果显示区域
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)

        self.status_label = QLabel("等待输入查询条件...") # 显示状态信息
        self.status_label.setStyleSheet("font-style: italic; color: gray;")
        results_layout.addWidget(self.status_label)

        self.results_list = QListWidget() # 使用列表显示结果
        self.results_list.setAlternatingRowColors(True)
        # 双击列表项可以尝试在本地数据库中模糊搜索
        self.results_list.itemDoubleClicked.connect(self.search_local_db)
        results_layout.addWidget(self.results_list)

        main_layout.addWidget(results_group)


    def start_search(self):
        """开始执行搜索"""
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入查询内容！")
            return

        # 如果上一个线程还在运行，先停止它
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait() # 等待线程结束

        # 禁用按钮，显示状态
        self.search_button.setEnabled(False)
        self.query_input.setEnabled(False)
        self.status_label.setText("正在搜索，请稍候...")
        self.status_label.setStyleSheet("font-style: normal; color: blue;")
        self.results_list.clear() # 清空上次结果

        # 创建并启动新线程
        self.search_thread = SearchThread(query)
        self.search_thread.results_ready.connect(self.show_results) # 连接信号到槽
        self.search_thread.finished.connect(self.search_finished) # 线程结束后恢复按钮状态
        self.search_thread.start()


    def show_results(self, results, error_message):
        """在列表中显示搜索结果"""
        self.results_list.clear()

        if error_message:
            self.status_label.setText(f"搜索出错: {error_message}")
            self.status_label.setStyleSheet("font-style: normal; color: red;")
        elif not results:
            self.status_label.setText("未能找到相关的书籍信息。")
            self.status_label.setStyleSheet("font-style: italic; color: gray;")
        else:
            self.status_label.setText(f"找到 {len(results)} 个可能相关的书名 (双击可在本地库搜索):")
            self.status_label.setStyleSheet("font-style: normal; color: green;")
            for title in results:
                item = QListWidgetItem(f"《{title}》")
                self.results_list.addItem(item)


    def search_finished(self):
        """搜索线程结束后恢复界面状态"""
        self.search_button.setEnabled(True)
        self.query_input.setEnabled(True)
        # 可以根据最终结果设置状态标签的最终文本，show_results 中已设置


    def search_local_db(self, item):
        """(可选增强) 双击结果列表项时，在本地数据库模糊搜索"""
        book_title = item.text().strip('《》') # 获取书名
        if not book_title: return

        query = "SELECT BookNo, BookName, Author, Storage FROM Books WHERE BookName LIKE %s"
        # 使用更宽松的模糊匹配
        search_pattern = f"%{book_title}%"
        results = execute_query(query, (search_pattern,))

        if results:
            # 可以弹出一个新对话框显示本地搜索结果，或在状态栏提示
            details = [f"本地库中找到与《{book_title}》相关的书籍："]
            for book in results:
                 status = "有库存" if book['Storage'] > 0 else "无库存"
                 details.append(f"- 《{book['BookName']}》 作者: {book.get('Author', 'N/A')} (ID: {book['BookNo']}, {status})")
            QMessageBox.information(self, "本地库搜索结果", "\n".join(details))
        else:
            QMessageBox.information(self, "本地库搜索结果", f"在本地数据库中未能找到与《{book_title}》直接匹配的书籍。")

    # 确保在窗口关闭时能正确停止线程
    def closeEvent(self, event):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()
        super().closeEvent(event)


# --- 用于独立测试页面 ---
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = AIAssistantPage()
    window.setWindowTitle("AI 助手页面测试")
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())
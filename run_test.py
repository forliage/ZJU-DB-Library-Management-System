# run_tests.py
import unittest
import os
import sys
import datetime

# --- 设置环境变量，让 db_utils 加载测试配置 ---
# 必须在导入 db_utils 之前设置
os.environ['LIBRARY_CONFIG'] = 'test_config.py'
print(f"已设置测试配置文件: {os.environ['LIBRARY_CONFIG']}")

# 现在导入 db_utils，它应该会加载 test_config.py
try:
    from db_utils_test import (
        create_connection, close_connection, execute_query, execute_modify,
        setup_test_database, cleanup_test_database # 导入测试辅助函数
    )
    # 检查是否成功加载了测试配置
    from test_config import DB_CONFIG as TEST_DB_CONFIG
    if 'test_library_system' not in TEST_DB_CONFIG.get('database', ''):
         print("错误：未能正确加载 test_config.py 中的数据库配置！")
         sys.exit(1)

except ImportError:
    print("错误：无法导入 db_utils 或 test_config。请确保它们存在且路径正确。")
    sys.exit(1)

# (如果你的核心逻辑分散在页面类中，理论上应该模拟UI交互来测试)
# (但这里为了简化，我们直接测试与数据库交互的逻辑，假设页面类会正确调用这些逻辑)
# (这意味着我们需要重新实现部分核心逻辑或直接操作数据库进行验证)

# 全局测试数据
TEST_ADMIN_USER = {'UserID': 'testadmin', 'Password': 'password123', 'Name': '测试管理员'}
TEST_PATRON_USER = {'CardNo': 'T001', 'Name': '测试读者', 'Department': '测试部门', 'CardType': '学生'}
TEST_BOOK_1 = {'BookNo': 'ISBN001', 'BookType': '小说', 'BookName': '测试书籍1', 'Publisher': '测试出版社', 'Year': 2023, 'Author': '作者A', 'Price': 50.00, 'Total': 5, 'Storage': 5}
TEST_BOOK_2 = {'BookNo': 'ISBN002', 'BookType': '计算机', 'BookName': '测试书籍2', 'Publisher': '测试出版社', 'Year': 2022, 'Author': '作者B', 'Price': 80.00, 'Total': 3, 'Storage': 3}
TEST_BOOK_NO_STOCK = {'BookNo': 'ISBN003', 'BookType': '历史', 'BookName': '无库存书籍', 'Publisher': '历史出版社', 'Year': 2020, 'Author': '作者C', 'Price': 60.00, 'Total': 2, 'Storage': 0}


class TestLibrarySystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前，设置测试数据库"""
        print("\n--- 开始测试套件 ---")
        setup_test_database() # 创建/清空测试数据库表

    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后，清理测试数据库 (可选)"""
        print("\n--- 测试套件结束 ---")
        # cleanup_test_database() # 如果需要测试后删除表，取消此行注释

    def setUp(self):
        """在每个测试方法开始前，插入基础数据"""
        # 插入管理员
        sql = "INSERT INTO Users (UserID, Password, Name) VALUES (%s, %s, %s)"
        execute_modify(sql, (TEST_ADMIN_USER['UserID'], TEST_ADMIN_USER['Password'], TEST_ADMIN_USER['Name']))
        # 插入读者
        sql = "INSERT INTO LibraryCard (CardNo, Name, Department, CardType) VALUES (%s, %s, %s, %s)"
        execute_modify(sql, (TEST_PATRON_USER['CardNo'], TEST_PATRON_USER['Name'], TEST_PATRON_USER['Department'], TEST_PATRON_USER['CardType']))
        # 插入书籍
        sql = "INSERT INTO Books (BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        execute_modify(sql, (TEST_BOOK_1['BookNo'], TEST_BOOK_1['BookType'], TEST_BOOK_1['BookName'], TEST_BOOK_1['Publisher'], TEST_BOOK_1['Year'], TEST_BOOK_1['Author'], TEST_BOOK_1['Price'], TEST_BOOK_1['Total'], TEST_BOOK_1['Storage']))
        execute_modify(sql, (TEST_BOOK_2['BookNo'], TEST_BOOK_2['BookType'], TEST_BOOK_2['BookName'], TEST_BOOK_2['Publisher'], TEST_BOOK_2['Year'], TEST_BOOK_2['Author'], TEST_BOOK_2['Price'], TEST_BOOK_2['Total'], TEST_BOOK_2['Storage']))
        execute_modify(sql, (TEST_BOOK_NO_STOCK['BookNo'], TEST_BOOK_NO_STOCK['BookType'], TEST_BOOK_NO_STOCK['BookName'], TEST_BOOK_NO_STOCK['Publisher'], TEST_BOOK_NO_STOCK['Year'], TEST_BOOK_NO_STOCK['Author'], TEST_BOOK_NO_STOCK['Price'], TEST_BOOK_NO_STOCK['Total'], TEST_BOOK_NO_STOCK['Storage']))
        print(f"\n[{self._testMethodName}] 测试数据准备完毕。")

    def tearDown(self):
        """在每个测试方法结束后，清理测试数据 (删除所有记录)"""
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            # 清空表，保留结构
            cursor.execute("TRUNCATE TABLE LibraryRecords;")
            cursor.execute("TRUNCATE TABLE Books;")
            cursor.execute("TRUNCATE TABLE LibraryCard;")
            cursor.execute("TRUNCATE TABLE Users;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()
            close_connection(conn)
            print(f"[{self._testMethodName}] 测试数据清理完毕。")


    # --- 测试用例 ---

    def test_01_admin_login(self):
        """测试管理员登录"""
        print("测试管理员登录...")
        # 模拟 LoginDialog 中的验证逻辑
        sql = "SELECT UserID FROM Users WHERE UserID = %s AND Password = %s"
        # 正确登录
        result = execute_query(sql, (TEST_ADMIN_USER['UserID'], TEST_ADMIN_USER['Password']))
        self.assertIsNotNone(result, "正确用户名密码应能查到用户")
        self.assertTrue(len(result) > 0, "正确用户名密码应返回至少一条记录")
        # 错误密码
        result_wrong_pass = execute_query(sql, (TEST_ADMIN_USER['UserID'], 'wrongpassword'))
        self.assertEqual(len(result_wrong_pass), 0, "错误密码不应返回记录")
        # 错误用户名
        result_wrong_user = execute_query(sql, ('wronguser', TEST_ADMIN_USER['Password']))
        self.assertEqual(len(result_wrong_user), 0, "错误用户名不应返回记录")
        print("管理员登录测试通过。")

    def test_02_book_query(self):
        """测试图书查询"""
        print("测试图书查询...")
        # 查询所有 (不带条件)
        sql_all = "SELECT BookNo FROM Books"
        result_all = execute_query(sql_all)
        self.assertEqual(len(result_all), 3, "应查到所有3本书")
        # 按书名模糊查询
        sql_name = "SELECT BookNo FROM Books WHERE BookName LIKE %s"
        result_name = execute_query(sql_name, ('%测试书籍%',))
        self.assertEqual(len(result_name), 2, "书名包含'测试书籍'的应有2本")
        # 按作者查询
        sql_author = "SELECT BookNo FROM Books WHERE Author = %s"
        result_author = execute_query(sql_author, (TEST_BOOK_1['Author'],))
        self.assertEqual(len(result_author), 1, "查询作者A应找到1本书")
        self.assertEqual(result_author[0]['BookNo'], TEST_BOOK_1['BookNo'], "查询作者A找到的书应是测试书籍1")
        # 查询不存在的书名
        result_not_exist = execute_query(sql_name, ('%不存在的书%',))
        self.assertEqual(len(result_not_exist), 0, "查询不存在的书名应返回0条记录")
        print("图书查询测试通过。")

    def test_03_add_single_book(self):
        """测试单本图书入库"""
        print("测试单本图书入库...")
        new_book = {'BookNo': 'ISBNNEW', 'BookType': '测试', 'BookName': '新书', 'Publisher': '新出版社', 'Year': 2024, 'Author': '新作者', 'Price': 99.99, 'Total': 10, 'Storage': 10}
        sql_insert = "INSERT INTO Books (BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = tuple(new_book.values()) # 确保顺序和类型正确
        execute_modify(sql_insert, params)
        # 验证是否插入成功
        sql_check = "SELECT BookName FROM Books WHERE BookNo = %s"
        result = execute_query(sql_check, (new_book['BookNo'],))
        self.assertEqual(len(result), 1, "新书应能被查询到")
        self.assertEqual(result[0]['BookName'], new_book['BookName'], "查询到的新书书名应匹配")
        # 尝试插入重复 BookNo (应失败, 但 execute_modify 不会抛错，我们检查数量没变)
        execute_modify(sql_insert, params)
        sql_count = "SELECT COUNT(*) AS count FROM Books"
        result_count = execute_query(sql_count)
        self.assertEqual(result_count[0]['count'], 4, "插入重复书号后，总数应仍为4")
        print("单本图书入库测试通过。")

    def test_04_borrow_book_success(self):
        """测试成功借书"""
        print("测试成功借书...")
        # 模拟 BorrowPage 的 perform_borrow
        book_to_borrow = TEST_BOOK_1
        borrower_card_no = TEST_PATRON_USER['CardNo']
        operator_id = TEST_ADMIN_USER['UserID']

        # 1. 更新库存
        sql_update_stock = "UPDATE Books SET Storage = Storage - 1 WHERE BookNo = %s AND Storage > 0"
        execute_modify(sql_update_stock, (book_to_borrow['BookNo'],))

        # 2. 添加借阅记录
        sql_insert_record = "INSERT INTO LibraryRecords (CardNo, BookNo, LentDate, Operator) VALUES (%s, %s, %s, %s)"
        lent_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        execute_modify(sql_insert_record, (borrower_card_no, book_to_borrow['BookNo'], lent_date, operator_id))

        # 验证库存
        sql_check_stock = "SELECT Storage FROM Books WHERE BookNo = %s"
        result_stock = execute_query(sql_check_stock, (book_to_borrow['BookNo'],))
        self.assertEqual(result_stock[0]['Storage'], book_to_borrow['Storage'] - 1, "借书后库存应减1")
        # 验证借阅记录
        sql_check_record = "SELECT FID FROM LibraryRecords WHERE CardNo = %s AND BookNo = %s AND ReturnDate IS NULL"
        result_record = execute_query(sql_check_record, (borrower_card_no, book_to_borrow['BookNo']))
        self.assertEqual(len(result_record), 1, "应能查到该借阅记录")
        print("成功借书测试通过。")

    def test_05_borrow_book_no_stock(self):
        """测试借阅无库存图书"""
        print("测试借阅无库存图书...")
        book_to_borrow = TEST_BOOK_NO_STOCK
        borrower_card_no = TEST_PATRON_USER['CardNo']
        operator_id = TEST_ADMIN_USER['UserID']

        # 检查库存
        sql_check_stock = "SELECT Storage FROM Books WHERE BookNo = %s"
        result_stock = execute_query(sql_check_stock, (book_to_borrow['BookNo'],))
        self.assertEqual(result_stock[0]['Storage'], 0, "确认测试书库存为0")

        # 尝试更新库存 (理论上不应成功或无效果)
        sql_update_stock = "UPDATE Books SET Storage = Storage - 1 WHERE BookNo = %s AND Storage > 0"
        execute_modify(sql_update_stock, (book_to_borrow['BookNo'],))
        result_stock_after = execute_query(sql_check_stock, (book_to_borrow['BookNo'],))
        self.assertEqual(result_stock_after[0]['Storage'], 0, "借阅无库存书后，库存应仍为0")

        # 确认没有添加借阅记录
        sql_check_record = "SELECT FID FROM LibraryRecords WHERE CardNo = %s AND BookNo = %s AND ReturnDate IS NULL"
        result_record = execute_query(sql_check_record, (borrower_card_no, book_to_borrow['BookNo']))
        self.assertEqual(len(result_record), 0, "借阅无库存书不应产生借阅记录")
        print("借阅无库存图书测试通过。")

    def test_06_return_book(self):
        """测试还书"""
        print("测试还书...")
        # 先执行一次成功借书
        self.test_04_borrow_book_success()
        print(" - 前置借书完成")

        book_to_return = TEST_BOOK_1
        borrower_card_no = TEST_PATRON_USER['CardNo']

        # 模拟 ReturnPage 的 perform_return
        # 1. 查找要还的记录 FID
        sql_find_record = "SELECT FID FROM LibraryRecords WHERE CardNo = %s AND BookNo = %s AND ReturnDate IS NULL"
        record_result = execute_query(sql_find_record, (borrower_card_no, book_to_return['BookNo']))
        self.assertEqual(len(record_result), 1, "还书前应能查到未还记录")
        record_fid = record_result[0]['FID']

        # 2. 更新记录 ReturnDate
        sql_update_record = "UPDATE LibraryRecords SET ReturnDate = %s WHERE FID = %s"
        return_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        execute_modify(sql_update_record, (return_date, record_fid))

        # 3. 更新库存 Storage + 1
        sql_update_stock = "UPDATE Books SET Storage = Storage + 1 WHERE BookNo = %s"
        execute_modify(sql_update_stock, (book_to_return['BookNo'],))

        # 验证库存
        sql_check_stock = "SELECT Storage FROM Books WHERE BookNo = %s"
        result_stock = execute_query(sql_check_stock, (book_to_return['BookNo'],))
        # 库存应恢复到初始值 (因为 setUp 中插入的是初始值，借书时-1，还书时+1)
        self.assertEqual(result_stock[0]['Storage'], TEST_BOOK_1['Storage'], "还书后库存应恢复初始值")
        # 验证借阅记录已还
        sql_check_record_returned = "SELECT FID FROM LibraryRecords WHERE FID = %s AND ReturnDate IS NOT NULL"
        result_returned = execute_query(sql_check_record_returned, (record_fid,))
        self.assertEqual(len(result_returned), 1, "还书后记录的 ReturnDate 应不为 NULL")
        # 确认没有未还记录了
        result_not_returned = execute_query(sql_find_record, (borrower_card_no, book_to_return['BookNo']))
        self.assertEqual(len(result_not_returned), 0, "还书后不应再查到该书的未还记录")
        print("还书测试通过。")


    def test_07_add_library_card(self):
        """测试添加借书证"""
        print("测试添加借书证...")
        new_card = {'CardNo': 'NEW001', 'Name': '新读者', 'Department': '新部门', 'CardType': '教师'}
        sql_insert = "INSERT INTO LibraryCard (CardNo, Name, Department, CardType) VALUES (%s, %s, %s, %s)"
        execute_modify(sql_insert, tuple(new_card.values()))
        # 验证
        sql_check = "SELECT Name FROM LibraryCard WHERE CardNo = %s"
        result = execute_query(sql_check, (new_card['CardNo'],))
        self.assertEqual(len(result), 1, "新借书证应能查到")
        # 尝试重复添加 (应失败，检查数量)
        execute_modify(sql_insert, tuple(new_card.values()))
        sql_count = "SELECT COUNT(*) AS count FROM LibraryCard"
        result_count = execute_query(sql_count)
        # 初始1个 + 新增1个 = 2个
        self.assertEqual(result_count[0]['count'], 2, "插入重复卡号后，总数应为2")
        print("添加借书证测试通过。")

    def test_08_delete_library_card(self):
        """测试删除借书证"""
        print("测试删除借书证...")
        card_to_delete = TEST_PATRON_USER['CardNo']
        # 先借一本书，测试级联删除 (如果设置了 ON DELETE CASCADE)
        self.test_04_borrow_book_success()
        print(" - 前置借书完成 (用于测试级联)")

        # 执行删除
        sql_delete = "DELETE FROM LibraryCard WHERE CardNo = %s"
        execute_modify(sql_delete, (card_to_delete,))

        # 验证卡是否已删除
        sql_check_card = "SELECT CardNo FROM LibraryCard WHERE CardNo = %s"
        result_card = execute_query(sql_check_card, (card_to_delete,))
        self.assertEqual(len(result_card), 0, "借书证应已被删除")

        # 验证关联的借阅记录是否也已删除 (因为设置了 ON DELETE CASCADE)
        sql_check_record = "SELECT FID FROM LibraryRecords WHERE CardNo = %s"
        result_record = execute_query(sql_check_record, (card_to_delete,))
        self.assertEqual(len(result_record), 0, "关联的借阅记录应因级联删除而被删除")
        print("删除借书证测试通过。")

    # --- 高级功能测试 (简单验证数据库逻辑) ---

    def test_09_borrow_ranking_logic(self):
        """测试借阅排行榜逻辑"""
        print("测试借阅排行榜逻辑...")
        # 模拟多次借阅
        # Book1 被借 3 次
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_1['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_1['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_1['BookNo']))
        # Book2 被借 2 次
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_2['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_2['BookNo']))

        # 查询排行榜 Top 1
        query = """
        SELECT lr.BookNo, COUNT(lr.FID) AS BorrowCount
        FROM LibraryRecords lr GROUP BY lr.BookNo ORDER BY BorrowCount DESC LIMIT 1
        """
        result = execute_query(query)
        self.assertEqual(len(result), 1, "排行榜应至少有1条记录")
        self.assertEqual(result[0]['BookNo'], TEST_BOOK_1['BookNo'], "排行榜第一名应是 Book1")
        self.assertEqual(result[0]['BorrowCount'], 3, "Book1 的借阅次数应为 3")
        print("借阅排行榜逻辑测试通过。")

    def test_10_borrowing_habit_logic(self):
        """测试借阅习惯（最常借阅类别）逻辑"""
        print("测试借阅习惯逻辑...")
        # 模拟借阅: 小说(Book1) 2次, 计算机(Book2) 3次
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_1['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_1['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_2['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_2['BookNo']))
        execute_modify("INSERT INTO LibraryRecords (CardNo, BookNo) VALUES (%s, %s)", (TEST_PATRON_USER['CardNo'], TEST_BOOK_2['BookNo']))

        # 查询最常借阅类别
        query = """
        SELECT b.BookType, COUNT(lr.FID) AS BorrowCount
        FROM LibraryRecords lr JOIN Books b ON lr.BookNo = b.BookNo
        WHERE lr.CardNo = %s AND b.BookType IS NOT NULL AND b.BookType != ''
        GROUP BY b.BookType ORDER BY BorrowCount DESC LIMIT 1
        """
        result = execute_query(query, (TEST_PATRON_USER['CardNo'],))
        self.assertEqual(len(result), 1, "应能查询到最常借阅类别")
        self.assertEqual(result[0]['BookType'], TEST_BOOK_2['BookType'], "最常借阅类别应是'计算机'")
        self.assertEqual(result[0]['BorrowCount'], 3, "计算机类别的借阅次数应为 3")
        print("借阅习惯逻辑测试通过。")

    # ... 可以继续添加对推荐、逾期、读者画像等逻辑的测试 ...


if __name__ == '__main__':
    # 使用 unittest 运行测试
    unittest.main()
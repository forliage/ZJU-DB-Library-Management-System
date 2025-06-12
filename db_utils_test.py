# db_utils.py
import mysql.connector
from mysql.connector import Error
import os
import importlib.util
import sys

def get_config_module_path():
    """根据环境变量决定加载哪个配置文件"""
    config_filename = os.environ.get('LIBRARY_CONFIG', 'config.py') # 默认为 config.py
    if getattr(sys, 'frozen', False): # 打包后
        base_path = os.path.dirname(sys.executable)
    else: # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, config_filename)

DB_CONFIG = {}
config_path = get_config_module_path()

if os.path.exists(config_path):
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        DB_CONFIG = getattr(config_module, 'DB_CONFIG', {})
        if not DB_CONFIG:
            print(f"警告：在 {config_path} 中未找到 DB_CONFIG 或其为空。")
    except Exception as e:
        print(f"错误：加载配置文件 {config_path} 时出错: {e}")
else:
    print(f"错误：配置文件 {config_path} 未找到。")
    # 可以设置默认值或退出
    # DB_CONFIG = {'host': 'localhost', ...}

def create_connection():
    """ 创建数据库连接 """
    # ... (连接逻辑不变, 使用 DB_CONFIG) ...
    connection = None
    if not DB_CONFIG:
        print("数据库配置未加载，无法创建连接。")
        return None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"连接 MySQL 时发生错误 ({DB_CONFIG.get('database')}): {e}")
        return None
    return None # Added return None here

def close_connection(connection):
    """ 关闭数据库连接 """
    # ... (不变) ...
    if connection and connection.is_connected():
         connection.close()

def execute_query(query, params=None):
    """ 执行 SELECT 查询 """
    # ... (不变, 确保正确处理连接失败) ...
    connection = create_connection()
    # ... (rest of the function) ...
    cursor = None
    result = None
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"执行查询时出错: {e}")
            return None
        finally:
            if cursor: cursor.close()
            close_connection(connection)
    return None


def execute_modify(query, params=None):
    """ 执行 INSERT, UPDATE, DELETE 等修改操作 """
    # ... (不变, 确保正确处理连接失败) ...
    connection = create_connection()
    # ... (rest of the function) ...
    cursor = None
    last_row_id = None # Initialize last_row_id
    if connection:
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            last_row_id = cursor.lastrowid # Assign after commit
            #print("修改操作执行成功") # Debug
            return last_row_id # Return ID or None
        except Error as e:
            print(f"执行修改操作时出错: {e}")
            connection.rollback()
            return None
        finally:
            if cursor: cursor.close()
            close_connection(connection)
    return None # Return None if connection failed

def setup_test_database():
    """ (仅用于测试) 创建测试数据库表结构 """
    connection = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE {DB_CONFIG['database']};")
        print(f"正在设置测试数据库 '{DB_CONFIG['database']}'...")

        # 删除已存在的表 (确保每次测试都是干净的)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables = ['LibraryRecords', 'Books', 'LibraryCard', 'Users']
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            print(f" - 已删除表 (如果存在): {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # 创建表结构 (与主程序一致)
        sql_commands = """
            CREATE TABLE Books (
                BookNo VARCHAR(50) PRIMARY KEY, BookType VARCHAR(50), BookName VARCHAR(100) NOT NULL,
                Publisher VARCHAR(100), Year INT, Author VARCHAR(100), Price DECIMAL(10, 2),
                Total INT DEFAULT 0, Storage INT DEFAULT 0,
                UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            CREATE TABLE LibraryCard (
                CardNo VARCHAR(50) PRIMARY KEY, Name VARCHAR(50) NOT NULL, Department VARCHAR(50),
                CardType VARCHAR(50), UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            CREATE TABLE Users (
                UserID VARCHAR(50) PRIMARY KEY, Password VARCHAR(255) NOT NULL, Name VARCHAR(50),
                Contact VARCHAR(50), UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            CREATE TABLE LibraryRecords (
                FID INT AUTO_INCREMENT PRIMARY KEY, CardNo VARCHAR(50) NOT NULL, BookNo VARCHAR(50) NOT NULL,
                LentDate DATETIME DEFAULT CURRENT_TIMESTAMP, ReturnDate DATETIME NULL, Operator VARCHAR(50),
                FOREIGN KEY (CardNo) REFERENCES LibraryCard(CardNo) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (BookNo) REFERENCES Books(BookNo) ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (Operator) REFERENCES Users(UserID) ON DELETE SET NULL ON UPDATE CASCADE
            );
        """
        for command in sql_commands.split(';'):
             if command.strip():
                 cursor.execute(command.strip() + ';')
                 print(f" - 已执行: {command.strip()[:50]}...") # 打印部分命令

        connection.commit()
        print("测试数据库表结构设置完成。")

    except Error as e:
        print(f"设置测试数据库时出错: {e}")
    finally:
        cursor.close()
        connection.close()

# (可选) 添加一个清理函数
def cleanup_test_database():
    """ (仅用于测试) 删除测试数据库中的所有表 """
    connection = create_connection()
    if not connection: return
    cursor = connection.cursor()
    try:
        print(f"正在清理测试数据库 '{DB_CONFIG['database']}'...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables = ['LibraryRecords', 'Books', 'LibraryCard', 'Users']
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            print(f" - 已删除表: {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connection.commit()
        print("测试数据库清理完成。")
    except Error as e:
        print(f"清理测试数据库时出错: {e}")
    finally:
        cursor.close()
        close_connection(connection)
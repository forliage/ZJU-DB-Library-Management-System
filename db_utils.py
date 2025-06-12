from pickletools import read_unicodestringnl

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG # 从配置文件导入数据库信息

def create_connection():
    """创建数据库连接"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG) # 使用字典解包传递参数
        if connection.is_connected():
            #print("成功连接到MySQL数据库") # 可以取消注释以用于测试
            return connection
    except Error as e:
        print(f"连接MySQL时发生错误:{e}")
        return None

def close_connection(connection):
    """关闭数据库连接"""
    if connection and connection.is_connected():
        connection.close()
        #print("MySQL连接关闭") # 可以取消注释以用于测试

# --- 更多数据库操作的辅助函数，如执行查询、插入等（可选）  ---

def execute_query(query, params=None):
    """执行SELECT查询"""
    connection = create_connection()
    cursor = None
    result = None
    if connection:
        try:
            cursor = connection.cursor(dictionary=True) # 让结果以字典形式返回
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"执行查询时出错:{e}")
            return None
        finally:
            if cursor:
                cursor.close()
            close_connection(connection)
    return None

def execute_modify(query, params=None):
    """执行INSERT,UPDATE,DELETE等修改操作"""
    connection = create_connection()
    cursor = None
    if connection:
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit() # 提交事务
            #print("修改操作执行成功") # 可以取消注释用于测试
            return cursor.lastrowid # 对于INSERT，可以返回最后插入行的ID
        except Error as e:
            print(f"执行修改操作时出错：{e}")
            connection.rollback() # 出错时回滚
            return None
        finally:
            if cursor:
                cursor.close()
            close_connection(connection)
    return None

# 测试连接（可以直接运行这个文件进行测试）
if __name__ == "__main__":
    conn = create_connection()
    if conn:
        print("数据库连接测试成功！")
        # 示例，查询Users表（如果表是空的，结果就是空的）
        users = execute_query("SELECT UserID, Name FROM Users")
        if users is not None:
            if users:
                print("查询到用户:",users)
            else:
                print("Users表为空或查询用户失败。")
        else:
            print("查询Users发生错误。")
        close_connection(conn)
    else:
        print("数据库连接测试失败！请检查 config.py 中的配置和 MySQL 服务状态。")




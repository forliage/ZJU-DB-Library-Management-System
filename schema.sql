CREATE DATABASE library_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE library_management_system;

-- 1.图书信息（Books）
CREATE TABLE Books (
    BookNo VARCHAR(50) PRIMARY KEY,   -- 书号（主键）
    BookType VARCHAR(50),             -- 图书类别
    BookName VARCHAR(100) NOT NULL,   -- 书名（不允许为空）
    Publisher VARCHAR(100),           -- 出版社
    Year INT,                         -- 出版年份
    Author VARCHAR(100),              -- 作者
    Price DECIMAL(10, 2),             -- 图书单价 (总共10位，小数点后2位)
    Total INT DEFAULT 0,              -- 总藏书数（默认为0）
    Storage INT DEFAULT 0,            -- 当前库存数（默认为0）
    UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- 添加或更新时间
);

-- 2.借书证表（LibraryCard）
CREATE TABLE LibraryCard (
    CardNo VARCHAR(50) PRIMARY KEY,   -- 卡号（主键）
    Name VARCHAR(50) NOT NULL ,       -- 姓名（不允许为空）
    Department VARCHAR(50),           -- 单位/部门
    CardType VARCHAR(50),             -- 借书证类别（如：学生/教师）
    UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- 添加或更新时间
);

-- 3.用户表（Users）
CREATE TABLE Users (
    UserID VARCHAR(50) PRIMARY KEY,   -- 用户/管理员ID（主键）
    Password VARCHAR(255) NOT NULL,   -- 密码（不允许为空，实际应用应存储哈希值）
    Name VARCHAR(50),                 -- 姓名
    Contact VARCHAR(50),              -- 联系方式
    UpdateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- 添加或更新时间
);

-- 4.借书记录表（LibraryRecords）
CREATE TABLE LibraryRecords (
    FID INT AUTO_INCREMENT PRIMARY KEY,    -- 记录ID（自增主键）
    CardNo VARCHAR(50) NOT NULL,           -- 借书卡号（外键关联LibraryCard）
    BookNo VARCHAR(50) NOT NULL,           -- 书号（外键关联Books）
    LentDate DATETIME DEFAULT CURRENT_TIMESTAMP, -- 借书日期（默认为当前时间）
    ReturnDate DATETIME NULL,              -- 还书日期（允许为空，表示未还）
    Operator VARCHAR(50),                  -- 经手人（管理员ID）
    FOREIGN KEY (CardNo) REFERENCES LibraryCard(CardNo) ON DELETE CASCADE ON UPDATE CASCADE, -- 外键约束
    FOREIGN KEY (BookNo) REFERENCES Books(BookNo) ON DELETE CASCADE ON UPDATE CASCADE,       -- 外键约束
    FOREIGN KEY (Operator) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE      -- 外键约束 (如果管理员被删除，记录保留但经手人设为NULL)
);
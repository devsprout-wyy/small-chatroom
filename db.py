"""阶段1：数据库代码（SQLite）"""
import sqlite3
#为什么选择sqlite3?
from pathlib import Path
from typing import Any, Sequence

# 数据库文件放到本文件同目录，这样在哪个目录启动都不会找错
DB_PATH: Path = Path(__file__).resolve().parent / "chat.db"


def get_db():
    """打开数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # 查询结果可以用 row["字段名"] 取值
    conn.execute("PRAGMA busy_timeout = 5000")  # 数据库被占用时最多等 5 秒，不直接报错
    return conn
#def get_db():
#定义函数get_db，作用：获取数据库连接对象，后面代码要操作数据库时就调用这个函数。




def init_db():
    """建表（已存在就跳过）"""
    conn = get_db()
    # 房间表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    # 消息表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id    INTEGER NOT NULL,
            username   TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id)")
    # 默认房间，保证页面一打开就有地方说话
    conn.execute("INSERT OR IGNORE INTO rooms (name) VALUES ('大厅')")
    #插入默认房间大厅。INSERT OR IGNORE：如果名字大厅已经存在，就不重复插入，避免重复创建同名房间。保证项目初始
    conn.commit()
    #提交事务！上面所有建表、插入房间的操作，全部写入数据库文件。没有commit，改动不会保存。
    conn.close()


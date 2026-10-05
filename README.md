# 项目简介

# 如何启动

# 已实现功能

# 未完成

# 已知问题


# 做过的试验

>1.在initial commit:only db.py的db.py中插入一条测试数据并且验证row_factory



# 修改痕迹/踩过的坑


>**1.代码语法不现代**：
在intial commit:only db.py的db.py（数据库代码）中发现了一些不太现代的语法：
```python
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.db") #修改前

Path(__file__).resolve().parent / "chat.db" #修改后
```
>**2.没有类型注解**：
2.2版本的代码有点小问题 ，函数定义后没有类型注解，我给他添加上去了。
>
>**3.存在连接可能不关闭的现象**：
2.2版本三个 conn.close() 都直接跟在查询后面。如果查询中途抛异常（比如数据库被删、表结构不对、chat.db 被锁），close() 这行不会执行 → 连接泄漏。Windows 上泄漏的连接会锁住 chat.db 文件，会删不掉、改不了它。
修改后 try 里的 raise HTTPException 也不再需要手动 conn.close() 了，更安全。

```python
#以get_messages为例修改后代码
@app.get("/api/messages/{room_id}")
def get_messages(room_id: int) -> dict:
    """2. 根据房间 id 查询该房间的历史消息"""
    conn = db.get_db()
    try:
        room = conn.execute("SELECT name FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if room is None:
            raise HTTPException(status_code=404, detail=f"房间 {room_id} 不存在")

        rows = conn.execute(
            "SELECT id, username, content, created_at FROM messages "
            "WHERE room_id = ? ORDER BY id",
            (room_id,))
        messages = [dict(row) for row in rows]
    finally:
        conn.close()          # 无论成功还是抛异常，一定关掉

    return {"room_id": room_id, "room_name": room["name"], "messages": messages}
```

## 项目简介

## 如何启动

## 已实现功能

## 未完成

## 已知问题



## 版本替代

>**版本1.1：编写数据库代码**
包含：sqlite连接、建表SQL，开启row_factory，配置busy_timeout

>**版本1.2:使语法更现代**

>**版本2.1：编写FastAPI基础骨架，写2个简单HTTP接口**
获取全部房间列表，同时根据房间id，查询该房间历史消息

>**版本2.2：**

>**版本2.3：**

>**版本2.4：**

>**版本3.0：编写WebSocket核心代码：**
维护各个房间的在线客户端连接，收到消息后：将消息存入数据库；广播给同房间所有在线用户

>**版本3.1：清理了幽灵数据和脏数据，取消git对chat.db的跟踪**




# 做过的试验

>1.在initial commit:only db.py的db.py中插入一条测试数据并且验证row_factory



## 修改痕迹/踩过的坑


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

>**4.数据库里有脏数据和幽灵数据40条：**
在3.0版本中发现：房间2被删掉了，但消息还在，造成幽灵数据36条，房间2什么时候删掉的我没有印象；还有一些超长消息。
这些大概是deepseek的探针和我自测时产生的。但根本原因还是main.py缺少房间校验导致的，直接把任何 room_id 存进库，根本不管房间存不存在。要根治的话还是得修main.py的代码。这样"给不存在的房间发消息"会在入口就被拒绝，不会再产生幽灵数据。同理 content[:2000] 能挡住超长消息。同时我还将chat.db的数据全部删掉。
```python
# 在 websocket.accept() 之后、登记连接之前加：
conn = db.get_db()
room = conn.execute("SELECT name FROM rooms WHERE id = ?", (room_id,)).fetchone()
if room is None:
    conn.close()
    await websocket.close(code=1008, reason=f"房间 {room_id} 不存在")
    return
```

>**5..gitignore 对 chat.db 无效**
原因：chat.db 在写这条规则之前就已经被提交了。
我直接在终端中取消git对chat.db的跟踪。
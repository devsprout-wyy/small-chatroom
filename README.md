# 极简聊天室
一个轻量聊天室：FastAPI + SQLite + 原生 HTML/JS，支持多房间隔离与实时消息广播。

- 后端：FastAPI（HTTP 接口 + WebSocket）
- 存储：SQLite（单文件，零配置）
- 前端：单个 HTML 文件，原生 JavaScript，不依赖任何前端框架和 CDN


## 一、如何启动
**方法一：一键启动**
双击项目根目录的 start.bat，脚本会自动完成：
- 检查虚拟环境 venv\，没有就自动创建
- 检查依赖，缺失就按 requirements.txt 自动安装
- 启动服务并自动打开浏览器

**方法二：手动启动**
```
cd "D:\small chatroom"

# 首次运行需要建虚拟环境并装依赖
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 启动服务
python main.py
```

**启动后终端显示：**
```
Uvicorn running on http://127.0.0.1:8010 (Press CTRL+C to quit)
```


**访问地址：**
http://127.0.0.1:8010/	聊天页面
http://127.0.0.1:8010/docs	FastAPI 自动生成的接口文档（可直接点击调试）




## 二、已实现功能

1多房间隔离：每个房间有独立的连接表和消息，互不干扰
2WebSocket实时广播：一人发言，同房间所有在线用户立刻收到
3消息持久化：每条消息先写入 SQLite 再广播，刷新页面不丢
4历史消息加载：进入房间时自动推送该房间的全部历史消息
5房间列表：下拉框选择房间，每 5 秒自动刷新
6输入校验：昵称限 20 字、消息限 2000 字、空消息不发送
7异常提示：消息格式错误时返回提示而不是断开连接







## 三、未完成

- 登录注册（昵称由用户自己填，不做身份验证）
- 头像、图片、文件上传
- 敏感词过滤
- 在线用户列表
- 消息分页（历史消息一次性全量推送）
- 新建房间的界面（只能在 db.py 初始化时插入「大厅」）


## 四、已知问题
- 输入框不支持换行，Enter 直接发送，没有 Shift+Enter 换行。气泡样式用的是 white-space: pre-wrap（本身能显示换行），但前端没有发送换行符的途径。
- 昵称相同无法区分，两个人都叫「张三」时，双方看到的消息都会带自己的名字（前端靠 msg.username === who 判断是否靠右显示）
- 没有房间删除功能	只能建、不能删。
- 聊天记录永久保留	任何进入房间的人都能看到全部历史消息，没有「清空聊天记录」的入口




## 五、修改痕迹/踩过的坑


**1.代码语法不现代**：

在intial commit:only db.py的db.py（数据库代码）中发现了一些不太现代的语法：
```python
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.db") #修改前

Path(__file__).resolve().parent / "chat.db" #修改后
```
**2.没有类型注解**：

2.2的代码有点小问题 ，函数定义后没有类型注解，我给他添加上去了。

**3.存在连接可能不关闭的现象**：

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

**4.数据库里有脏数据和幽灵数据40条：**

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

**5.在3.0中.gitignore 对 chat.db 无效**

原因：chat.db 在写这条规则之前就已经被提交了。
我直接在终端中取消git对chat.db的跟踪。

**6.3.1中ensure_ascii 让广播完全失效**

错因：Starlette 的 WebSocket.send_json()只有 data 和 mode 两个参数，没有 ensure_ascii。传进去直接抛：TypeError: WebSocket.send_json() got an unexpected keyword argument 'ensure_ascii'
而这个异常立刻被下一行的 except Exception: pass 吞掉。导致消息正常入库，但一个字都发不出去。客户端傻等、服务端无日志，核心功能（实时聊天）完全失效。把裸 except 加上打印是为了下次出错时能够查到

```python
#修改前
try:
    await ws.send_json(frame, ensure_ascii=False)
except Exception:
    pass         

#修改后
try:
    await ws.send_json(frame)
except Exception as e:
    print(f"[广播失败] {type(e).__name__}: {e}")
    pass  
```


**7.在3.1中昵称没有长度限制**

username 来自 URL query，完全没限制。昵称会被拼进 WebSocket 的握手 URL，请求行超长时 uvicorn 直接返回：INFO: HTTP response sent (414 URI Too Long)
客户端拿到的是 TimeoutError: timed out during opening handshake——连接根本建立不起来，用户连房间都进不去。
所以我将其改成在 accept() 之后立刻清洗，限长 20。
or "匿名" 同时解决另一个小问题：URL 写成 username= 时会产生无名用户。


```python
#修改前
async def chat_ws(websocket: WebSocket, room_id: int, username: str = "匿名"):

#修改后
await websocket.accept()
username = username.strip()[:20] or "匿名"      
```



**8.在3.1中消息内容没有长度限制**

判断了"是否为空"，但没判断"是否过长"。导致20000 字的消息会原样入库并且原样广播。而且还会产生一个问题：因为历史消息是一次性全量推送的，房间里堆了超长消息后，每个新用户进房间都要接收一个巨型 history 帧。

```python
#修改前
content = str(data.get("content", "")).strip()
if not content:
    continue

#修改后
content = str(data.get("content", "")).strip()
if not content:
    continue
content = content[:2000]        
```




**9.StaticFiles 挂在 / 会吞掉路由**

在写挂载时，我将以下代码：
```python
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")   
```
写在文件开头，导致后面注册的接口都死了，原因是挂载将后面的路由都吞掉
页面能打开，但所有数据接口都死了——现象是"页面打开了但一片空白"
把 mount 挪到文件最末尾，即所有路由注册完之后



**10.在4.0的main.py中同一个函数两次开库**
改成开一次库，少一个"开了要记得关"的地方，就少一次忘记关的风险。











## 六、版本替代说明

**版本1.1：编写数据库代码**
包含：sqlite连接、建表SQL，开启row_factory，配置busy_timeout

**版本1.2:使语法更现代**

**版本2.1：编写FastAPI基础骨架，写2个简单HTTP接口**
获取全部房间列表，同时根据房间id，查询该房间历史消息

**版本2.2：**

**版本2.3：**

**版本2.4：**

**版本3.0：编写WebSocket核心代码：**
维护各个房间的在线客户端连接，收到消息后：将消息存入数据库；广播给同房间所有在线用户

**版本3.1：清理了幽灵数据和脏数据，取消git对chat.db的跟踪**

**版本3.2：修改了一些3.1遗留的bug**

**版本4.0：初步完成前页面的代码**

**版本4.1：重新保存，之前的main.py和README.md没有保存**

**版本4.2：进一步修改main.py，提高性能**
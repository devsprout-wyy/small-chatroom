
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

import db

app = FastAPI(title="极简聊天室")

db.init_db()          # 启动时建表，已存在就跳过

# 在线连接表： {房间id: [(websocket, 用户名), ...]}
rooms: dict[int, list[tuple[WebSocket, str]]] = {}


@app.get("/")
def home():
    """根路径，用来确认服务是否活着"""
    return {"service": "极简聊天室", "status": "ok", "docs": "/docs"}


@app.get("/api/rooms")
def get_rooms():
    """1. 获取全部房间列表"""
    conn = db.get_db()
    rows = conn.execute("SELECT id, name FROM rooms ORDER BY id")
    rooms_list = [dict(row) for row in rows]
    conn.close()
    return rooms_list


@app.get("/api/messages/{room_id}")
def get_messages(room_id: int):
    """2. 根据房间 id 查询该房间的历史消息"""
    conn = db.get_db()

    room = conn.execute("SELECT name FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if room is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"房间 {room_id} 不存在")

    rows = conn.execute(
        "SELECT id, username, content, created_at FROM messages "
        "WHERE room_id = ? ORDER BY id",
        (room_id,))
    messages = [dict(row) for row in rows]
    conn.close()

    return {"room_id": room_id, "room_name": room["name"], "messages": messages}


@app.websocket("/ws")
async def chat_ws(websocket: WebSocket, room_id: int, username: str = "匿名"):
    """实时聊天：连上先收历史消息，之后收到消息就存库并广播给同房间所有人"""
    await websocket.accept()

    conn = db.get_db()
    room = conn.execute("SELECT name FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if room is None:
        conn.close()
        await websocket.close(code=1008, reason=f"房间 {room_id} 不存在")
        return

    # 登记这条连接
    rooms.setdefault(room_id, []).append((websocket, username))

    # 进房间先发历史消息
    conn = db.get_db()
    rows = conn.execute(
        "SELECT id, username, content, created_at FROM messages "
        "WHERE room_id = ? ORDER BY id",
        (room_id,))
    await websocket.send_json(
        {"type": "history", "room_id": room_id,
         "messages": [dict(row) for row in rows]})
    conn.close()

    try:
        while True:
            data = await websocket.receive_json()      # 等这个客户端发消息
            content = str(data.get("content", "")).strip()
            if not content:
                continue                               # 空消息不存也不发

            # ① 存进数据库。用参数化插入，不拼 SQL，天然防注入
            conn = db.get_db()
            cur = conn.execute(
                "INSERT INTO messages (room_id, username, content) VALUES (?, ?, ?)",
                (room_id, username, content))
            conn.commit()
            row = conn.execute(
                "SELECT id, username, content, created_at FROM messages WHERE id = ?",
                (cur.lastrowid,)).fetchone()
            conn.close()

            # ② 广播给同房间所有在线用户（含发消息的人自己）
            frame = {"type": "message", "room_id": room_id, **dict(row)}
            for ws, _ in list(rooms[room_id]):
                try:
                    await ws.send_json(frame, ensure_ascii=False)   # ← Bug 2
                except Exception:
                    pass          # 这个连接已经断了，忽略即可

    except WebSocketDisconnect:
        pass                  # 正常关页面/关标签页，不算错误
    except Exception as e:
        print(f"[WebSocket 异常] 房间{room_id} 用户{username}：{type(e).__name__}: {e}")
    finally:
        # 客户端离开：从在线表里摘掉，房间空了就删掉这个 key
        rooms[room_id] = [(ws, u) for ws, u in rooms.get(room_id, []) if ws is not websocket]
        if not rooms[room_id]:        # ← Bug 5：key 不存在时 KeyError
            del rooms[room_id]


if __name__ == "__main__":
    import uvicorn

    # 端口用 8010：8000 是好几个项目的默认端口，容易和别的服务撞车
    uvicorn.run("main:app", host="127.0.0.1", port=8010, reload=True)

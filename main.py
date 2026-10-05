"""阶段2：FastAPI 基础骨架 + 2 个 HTTP 接口

运行：python main.py
接口：GET /                   服务状态
      GET /api/rooms          房间列表
      GET /api/messages/{id}  某房间的历史消息
"""

from fastapi import FastAPI

import db

app = FastAPI(title="极简聊天室")

db.init_db()          # 启动时建表，已存在就跳过


@app.get("/")
def home():
    """根路径，用来确认服务是否活着"""
    return {"service": "极简聊天室", "status": "ok", "docs": "/docs"}


@app.get("/api/rooms")
def get_rooms():
    """1. 获取全部房间列表"""
    return db.query("SELECT id, name FROM rooms ORDER BY id")


@app.get("/api/messages/{room_id}")
def get_messages(room_id: int):
    """2. 根据房间 id 查询该房间的历史消息"""
    room = db.query("SELECT name FROM rooms WHERE id = :id", {"id": room_id})
    if not room:
        return {"error": f"房间 {room_id} 不存在"}

    rows = db.query(
        "SELECT id, username, content, created_at FROM messages "
        "WHERE room_id = :id ORDER BY id",
        {"id": room_id})
    return {"room_id": room_id, "room_name": room[0]["name"], "messages": rows}


if __name__ == "__main__":
    import uvicorn

    # 端口用 8010：8000 是好几个项目的默认端口，容易和别的服务撞车
    uvicorn.run("main:app", host="127.0.0.1", port=8010, reload=True)

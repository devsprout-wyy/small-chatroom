"""阶段2：FastAPI 基础骨架 + 2 个 HTTP 接口

运行：python main.py
接口：GET /                   服务状态
      GET /api/rooms          房间列表
      GET /api/messages/{id}  某房间的历史消息

数据库用法对齐 db.py：只用 get_db() 和 init_db()，
每个接口自己开连接、查完就关，不在 db 层再包一层 query()。
"""

from fastapi import FastAPI, HTTPException
#导入FastAPI框架，HTTPException 用来返回自定义错误提示（比如房间不存在返回404）

import db
#导入我们自己写的db.py数据库模块，调用里面的get_db()、init_db()
app = FastAPI(title="极简聊天室")
#创建FastAPI实例app，title是接口文档页面显示的项目名称，访问 /docs 就能看到自动生成的API文档。

db.init_db()          # 启动时建表，已存在就跳过（reload=True 开发模式下，uvicorn 会重新导入模块，init_db() 会执行两次。我实测过，因为 init_db 里用了 CREATE TABLE IF NOT EXISTS 和 INSERT OR IGNORE，所以不会出问题——这里代码是对的，只是说明一下这个设计是靠"幂等"兜住的，不是巧合。）
#项目启动立刻执行数据库初始化，调用db.py的init_db函数，自动创建rooms、messages两张表；如果表已经存在，不会重复创建。

@app.get("/")  #接口装饰器，定义一个GET请求接口，访问地址：http://127.0.0.1:8010/
def home() -> dict:
    """根路径，用来确认服务是否活着"""
    return {"service": "极简聊天室", "status": "ok", "docs": "/docs"}
#return 返回json，浏览器访问根路径，会看到这段json，确认服务正常运行；/docs是自动生成的API在线文档地址。

@app.get("/api/rooms")  #GET接口，地址/api/rooms，获取所有聊天室房间
def get_rooms() -> dict:
    """1. 获取全部房间列表"""
    conn = db.get_db()  #调用db模块，拿到数据库连接conn（自带row_factory）
    rooms = [dict(row) for row in conn.execute("SELECT id, name FROM rooms ORDER BY id")]
    #SELECT id, name FROM rooms ORDER BY id，查询rooms表的id、房间名称，按id从小到大排序
    #[dict(row) for row in ...] 列表推导式：把sqlite3.Row对象转成字典，FastAPI可以直接转为JSON返回给前端（数据库查询出来是sqlite3.Row对象，dict(row)把Row转为字典，就可以返回给前端。）
    conn.close()
    return rooms  #把房间列表JSON返回给前端。


@app.get("/api/messages/{room_id}")
def get_messages(room_id: int) -> dict:
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


if __name__ == "__main__":
    import uvicorn

    # 端口用 8010：8000 是好几个项目的默认端口，容易和别的服务撞车
    uvicorn.run("main:app", host="127.0.0.1", port=8010, reload=True)


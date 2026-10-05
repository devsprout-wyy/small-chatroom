# 项目简介

# 如何启动

# 已实现功能

# 未完成

# 已知问题


# 做过的试验

>1.在initial commit:only db.py的db.py中插入一条测试数据并且验证row_factory
![试验代码运行结果截图，显示TypeError: tuple indices must be integers or slices, not str]()


# 修改痕迹


>1.在intial commit:only db.py的db.py（数据库代码）中发现了一些不太现代的语法：
-  路径
```python
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.db") #修改前

Path(__file__).resolve().parent / "chat.db" #修改后
```


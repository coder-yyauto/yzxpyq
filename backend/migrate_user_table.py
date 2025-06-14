import os
import sqlite3
from app import app, db, User

print("开始迁移用户表...")

# 确保实例目录存在
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'school.db')

# 检查数据库是否存在
if not os.path.exists(db_path):
    print(f"数据库文件 {db_path} 不存在，将创建新数据库")
    with app.app_context():
        db.create_all()
        print("创建新数据库完成")
else:
    # 连接数据库
    print(f"连接到现有数据库 {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查用户表中是否已存在新字段
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    changes_made = False
    
    # 检查并添加 is_first_login 字段
    if 'is_first_login' not in columns:
        print("添加 is_first_login 字段...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_first_login BOOLEAN DEFAULT 0")
        changes_made = True
    
    # 检查并添加 can_post 字段
    if 'can_post' not in columns:
        print("添加 can_post 字段...")
        cursor.execute("ALTER TABLE user ADD COLUMN can_post BOOLEAN DEFAULT 1")
        changes_made = True
    
    # 提交更改
    if changes_made:
        conn.commit()
        print("表结构更新完成")
    else:
        print("无需更新表结构")
    
    # 检查 real_name 字段的约束
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
    table_sql = cursor.fetchone()[0]
    
    # 如果需要更改 real_name 约束，我们需要重建表
    # SQLite 不支持直接修改列约束，所以这里我们更新SQLAlchemy模型后
    # 让它通过 reflection 映射到现有表上
    
    # 关闭连接
    conn.close()

print("迁移用户表完成") 
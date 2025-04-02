import os
import sqlite3
from app import app, db

# 删除现有的数据库文件
db_path = os.path.join(app.instance_path, 'school.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"已删除旧数据库: {db_path}")

# 确保上传目录存在
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']), exist_ok=True)

# 创建新数据库
with app.app_context():
    db.create_all()
    print("已创建新数据库")

print("数据库初始化完成") 
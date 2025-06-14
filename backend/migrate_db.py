import os
from app import app, db, SystemConfig
import sqlite3

print("开始数据库迁移...")

# 确保实例目录存在
os.makedirs(app.instance_path, exist_ok=True)

# 创建新表但不删除现有数据
with app.app_context():
    # 检查system_config表是否已存在
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'system_config' not in tables:
        print("创建system_config表...")
        # 创建system_config表
        db.create_all()
        
        # 添加默认配置
        if not SystemConfig.query.filter_by(key='register_enabled').first():
            SystemConfig.set_config('register_enabled', 'true', '是否开启用户注册功能')
            print("添加默认配置: register_enabled = true")
        
        print("system_config表创建成功")
    else:
        print("system_config表已存在，无需创建")

def migrate_database():
    # 获取数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'school.db')
    
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查comments_disabled列是否存在
        cursor.execute("PRAGMA table_info(post)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'comments_disabled' not in columns:
            print("添加 comments_disabled 列...")
            cursor.execute("ALTER TABLE post ADD COLUMN comments_disabled BOOLEAN DEFAULT 0")
            conn.commit()
            print("成功添加 comments_disabled 列")
        else:
            print("comments_disabled 列已存在")
            
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

print("数据库迁移完成") 
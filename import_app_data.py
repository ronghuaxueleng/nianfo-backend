#!/usr/bin/env python3
"""
从Flutter app的SQLite数据库导入数据到后台MySQL数据库
"""

import sqlite3
import sys
import os
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import db
from models.user import User
from models.chanting import Chanting
from models.dedication import Dedication
from models.chanting_record import ChantingRecord
from models.daily_stats import DailyStats
from models.dedication_template import DedicationTemplate

def find_app_database():
    """查找app数据库文件"""
    possible_paths = [
        '/mnt/e/GitHub/nianfo/app/nianfo.db',
        '/mnt/e/GitHub/nianfo/nianfo.db',
        './nianfo.db',
        '../app/nianfo.db',
        # Windows路径
        'C:\\Users\\%USERNAME%\\AppData\\Local\\nianfo\\nianfo.db',
        # 模拟器路径
        '/data/data/com.example.nianfo_app/databases/nianfo.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"找到数据库文件: {path}")
            return path
    
    print("未找到app数据库文件")
    print("请提供数据库文件路径作为参数:")
    print("python import_app_data.py /path/to/nianfo.db")
    return None

def connect_sqlite(db_path):
    """连接SQLite数据库"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
        print(f"成功连接到SQLite数据库: {db_path}")
        return conn
    except Exception as e:
        print(f"连接SQLite数据库失败: {e}")
        return None

def import_users(sqlite_conn, app_context):
    """导入用户数据"""
    print("\n🧑 导入用户数据...")
    with app_context:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        imported_count = 0
        for row in users:
            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=row['username']).first()
            if existing_user:
                print(f"用户 {row['username']} 已存在，跳过")
                continue
            
            user = User(
                username=row['username'],
                password=row['password'],  # 直接使用已哈希的密码
                avatar=row['avatar'] if 'avatar' in row.keys() and row['avatar'] else None,
                avatar_type=row['avatar_type'] if 'avatar_type' in row.keys() and row['avatar_type'] else 'emoji',
                nickname=row['nickname'] if 'nickname' in row.keys() and row['nickname'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            
            db.session.add(user)
            imported_count += 1
            print(f"导入用户: {user.username}")
        
        db.session.commit()
        print(f"✅ 用户导入完成，共导入 {imported_count} 个用户")

def import_chantings(sqlite_conn, app_context):
    """导入佛号经文数据"""
    print("\n📿 导入佛号经文数据...")
    with app_context:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM chantings WHERE is_deleted = 0")
        chantings = cursor.fetchall()
        
        imported_count = 0
        for row in chantings:
            # 检查是否已存在
            existing = Chanting.query.filter_by(title=row['title'], content=row['content']).first()
            if existing:
                print(f"佛号经文 {row['title']} 已存在，跳过")
                continue
            
            # 处理类型转换
            chanting_type = row['type'] if 'type' in row.keys() and row['type'] else 'buddha'
            if chanting_type == 'buddhaNam':
                chanting_type = 'buddha'
            
            chanting = Chanting(
                title=row['title'],
                content=row['content'],
                pronunciation=row['pronunciation'] if 'pronunciation' in row.keys() and row['pronunciation'] else None,
                type=chanting_type,
                is_built_in=bool(row['is_built_in'] if 'is_built_in' in row.keys() else 0),
                is_deleted=False,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            
            db.session.add(chanting)
            imported_count += 1
            print(f"导入佛号经文: {chanting.title} ({chanting.type})")
        
        db.session.commit()
        print(f"✅ 佛号经文导入完成，共导入 {imported_count} 条记录")

def import_dedications(sqlite_conn, app_context):
    """导入回向数据"""
    print("\n🙏 导入回向数据...")
    with app_context:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM dedications")
        dedications = cursor.fetchall()
        
        imported_count = 0
        for row in dedications:
            # 检查是否已存在
            existing = Dedication.query.filter_by(title=row['title'], content=row['content']).first()
            if existing:
                print(f"回向 {row['title']} 已存在，跳过")
                continue
            
            # 查找关联的佛号经文
            chanting_id = None
            if 'chanting_id' in row.keys() and row['chanting_id']:
                # 先查找SQLite中的佛号经文
                cursor.execute("SELECT title, content FROM chantings WHERE id = ?", (row['chanting_id'],))
                chanting_row = cursor.fetchone()
                if chanting_row:
                    # 在MySQL中查找对应的佛号经文
                    chanting = Chanting.query.filter_by(
                        title=chanting_row['title'], 
                        content=chanting_row['content']
                    ).first()
                    if chanting:
                        chanting_id = chanting.id
            
            dedication = Dedication(
                title=row['title'],
                content=row['content'],
                chanting_id=chanting_id,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            
            db.session.add(dedication)
            imported_count += 1
            print(f"导入回向: {dedication.title}")
        
        db.session.commit()
        print(f"✅ 回向导入完成，共导入 {imported_count} 条记录")

def import_chanting_records(sqlite_conn, app_context):
    """导入修行记录数据"""
    print("\n📔 导入修行记录数据...")
    with app_context:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM chanting_records")
        records = cursor.fetchall()
        
        imported_count = 0
        for row in records:
            # 查找关联的佛号经文
            cursor.execute("SELECT title, content FROM chantings WHERE id = ?", (row['chanting_id'],))
            chanting_row = cursor.fetchone()
            if not chanting_row:
                print(f"修行记录关联的佛号经文不存在，跳过记录ID: {row['id']}")
                continue
            
            # 在MySQL中查找对应的佛号经文
            chanting = Chanting.query.filter_by(
                title=chanting_row['title'], 
                content=chanting_row['content']
            ).first()
            if not chanting:
                print(f"MySQL中未找到对应的佛号经文: {chanting_row['title']}")
                continue
            
            # 检查记录是否已存在
            existing = ChantingRecord.query.filter_by(chanting_id=chanting.id).first()
            if existing:
                print(f"修行记录已存在: {chanting.title}")
                continue
            
            record = ChantingRecord(
                chanting_id=chanting.id,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            
            db.session.add(record)
            imported_count += 1
            print(f"导入修行记录: {chanting.title}")
        
        db.session.commit()
        print(f"✅ 修行记录导入完成，共导入 {imported_count} 条记录")

def import_daily_stats(sqlite_conn, app_context):
    """导入每日统计数据"""
    print("\n📊 导入每日统计数据...")
    with app_context:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM daily_stats")
        stats = cursor.fetchall()
        
        imported_count = 0
        for row in stats:
            # 查找关联的佛号经文
            cursor.execute("SELECT title, content FROM chantings WHERE id = ?", (row['chanting_id'],))
            chanting_row = cursor.fetchone()
            if not chanting_row:
                continue
            
            # 在MySQL中查找对应的佛号经文
            chanting = Chanting.query.filter_by(
                title=chanting_row['title'], 
                content=chanting_row['content']
            ).first()
            if not chanting:
                continue
            
            # 检查统计数据是否已存在
            stat_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
            existing = DailyStats.query.filter_by(
                chanting_id=chanting.id,
                date=stat_date
            ).first()
            if existing:
                # 更新计数
                existing.count = max(existing.count, row['count'])
                print(f"更新统计数据: {chanting.title} {stat_date} -> {existing.count}")
            else:
                stat = DailyStats(
                    chanting_id=chanting.id,
                    count=row['count'],
                    date=stat_date,
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
                )
                db.session.add(stat)
                imported_count += 1
                print(f"导入统计数据: {chanting.title} {stat_date} -> {row['count']}")
        
        db.session.commit()
        print(f"✅ 每日统计导入完成，共导入 {imported_count} 条记录")

def import_dedication_templates(sqlite_conn, app_context):
    """导入回向模板数据"""
    print("\n📝 导入回向模板数据...")
    with app_context:
        try:
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT * FROM dedication_templates")
            templates = cursor.fetchall()
            
            imported_count = 0
            for row in templates:
                # 检查模板是否已存在
                existing = DedicationTemplate.query.filter_by(title=row['title']).first()
                if existing:
                    print(f"回向模板 {row['title']} 已存在，跳过")
                    continue
                
                template = DedicationTemplate(
                    title=row['title'],
                    content=row['content'],
                    is_built_in=bool(row['is_built_in'] if 'is_built_in' in row.keys() else 0),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
                )
                
                db.session.add(template)
                imported_count += 1
                print(f"导入回向模板: {template.title}")
            
            db.session.commit()
            print(f"✅ 回向模板导入完成，共导入 {imported_count} 条记录")
        except Exception as e:
            print(f"导入回向模板时出错（表可能不存在）: {e}")

def main():
    """主函数"""
    print("🔄 开始导入Flutter app数据到后台数据库...")
    
    # 获取数据库路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = find_app_database()
    
    if not db_path or not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    # 连接SQLite数据库
    sqlite_conn = connect_sqlite(db_path)
    if not sqlite_conn:
        return
    
    # 创建Flask app上下文
    app = create_app()
    
    try:
        with app.app_context():
            # 按顺序导入数据
            import_users(sqlite_conn, app.app_context())
            import_chantings(sqlite_conn, app.app_context())
            import_dedications(sqlite_conn, app.app_context())
            import_chanting_records(sqlite_conn, app.app_context())
            import_daily_stats(sqlite_conn, app.app_context())
            import_dedication_templates(sqlite_conn, app.app_context())
            
            print("\n🎉 数据导入完成！")
            print("南无阿弥陀佛 🙏")
    
    except Exception as e:
        print(f"❌ 导入过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        sqlite_conn.close()

if __name__ == '__main__':
    main()
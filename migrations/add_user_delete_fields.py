#!/usr/bin/env python3
"""
添加用户删除相关字段的数据库迁移脚本
运行方法: python migrations/add_user_delete_fields.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from app import create_app

def add_user_delete_fields():
    """添加用户删除相关字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查字段是否已存在（SQLite语法）
            with db.engine.connect() as conn:
                result = conn.execute(db.text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                
                # 添加 is_deleted 字段
                if 'is_deleted' not in columns:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
                    print("✓ 添加 is_deleted 字段成功")
                else:
                    print("• is_deleted 字段已存在")
                
                # 添加 deleted_at 字段  
                if 'deleted_at' not in columns:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN deleted_at DATETIME NULL"))
                    print("✓ 添加 deleted_at 字段成功")
                else:
                    print("• deleted_at 字段已存在")
                
                conn.commit()
            
            # 提交事务
            db.session.commit()
            print("✓ 数据库迁移完成")
            
        except Exception as e:
            print(f"✗ 迁移失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_user_delete_fields()
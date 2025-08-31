#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为chantings表添加user_id字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.user import User
from models.chanting import Chanting

def upgrade():
    """添加user_id字段并设置默认值"""
    print("开始迁移：为chantings表添加user_id字段...")
    
    try:
        # 检查user_id字段是否已存在
        columns = [col.name for col in Chanting.__table__.columns]
        if 'user_id' in columns:
            print("user_id字段已存在，跳过迁移")
            return
        
        # 添加user_id字段
        with db.engine.connect() as conn:
            conn.execute("ALTER TABLE chantings ADD COLUMN user_id INT NULL")
            conn.execute("ALTER TABLE chantings ADD CONSTRAINT fk_chantings_user_id FOREIGN KEY (user_id) REFERENCES users (id)")
            
        print("user_id字段添加成功")
        
        # 为现有的自定义内容设置user_id
        # 这里我们假设所有非内置内容都是admin创建的
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            # 更新所有非内置内容的user_id为admin
            with db.engine.connect() as conn:
                conn.execute(
                    "UPDATE chantings SET user_id = %s WHERE is_built_in = 0 AND user_id IS NULL",
                    (admin_user.id,)
                )
            print(f"为现有自定义内容设置创建者为admin用户（ID: {admin_user.id}）")
        else:
            print("警告：未找到admin用户，现有自定义内容的user_id保持为NULL")
            
        print("迁移完成")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        raise

def downgrade():
    """删除user_id字段"""
    print("开始回滚：删除chantings表的user_id字段...")
    
    try:
        # 删除外键约束和字段
        with db.engine.connect() as conn:
            conn.execute("ALTER TABLE chantings DROP FOREIGN KEY fk_chantings_user_id")
            conn.execute("ALTER TABLE chantings DROP COLUMN user_id")
            
        print("回滚完成")
        
    except Exception as e:
        print(f"回滚失败: {e}")
        raise

if __name__ == '__main__':
    from app import create_app
    
    app = create_app('development')
    with app.app_context():
        upgrade()
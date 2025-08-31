#!/usr/bin/env python3
"""
修复DailyStats表中缺失的user_id字段
将遗留数据（user_id为NULL）根据ChantingRecord关联到正确的用户
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.daily_stats import DailyStats
from models.chanting_record import ChantingRecord
from sqlalchemy import and_

def fix_daily_stats_user_id():
    """修复DailyStats中缺失的user_id"""
    app = create_app()
    
    with app.app_context():
        print("开始修复DailyStats中缺失的user_id...")
        
        # 查找所有user_id为NULL的DailyStats记录
        orphaned_stats = DailyStats.query.filter(DailyStats.user_id.is_(None)).all()
        print(f"找到 {len(orphaned_stats)} 条需要修复的记录")
        
        fixed_count = 0
        unfixable_count = 0
        
        for stat in orphaned_stats:
            # 根据chanting_id查找对应的ChantingRecord
            # 假设每个chanting只有一个用户的记录，或者取第一个找到的
            record = ChantingRecord.query.filter_by(chanting_id=stat.chanting_id).first()
            
            if record and record.user_id:
                print(f"修复统计ID {stat.id}: chanting_id={stat.chanting_id}, 分配给用户 {record.user_id}")
                stat.user_id = record.user_id
                fixed_count += 1
            else:
                print(f"无法修复统计ID {stat.id}: 找不到对应的用户记录")
                unfixable_count += 1
        
        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"✅ 成功修复 {fixed_count} 条记录")
            except Exception as e:
                db.session.rollback()
                print(f"❌ 提交失败: {e}")
        else:
            print("没有需要修复的记录")
        
        if unfixable_count > 0:
            print(f"⚠️  有 {unfixable_count} 条记录无法自动修复，需要手动处理")
        
        print("修复完成！")

if __name__ == '__main__':
    fix_daily_stats_user_id()
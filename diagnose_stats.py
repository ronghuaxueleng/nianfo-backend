#!/usr/bin/env python3
"""
诊断修行记录统计数据问题
"""

import os
import sys
from datetime import date

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models.daily_stats import DailyStats
from models.chanting_record import ChantingRecord
from models.chanting import Chanting
from sqlalchemy import func

def diagnose_stats():
    """诊断统计数据问题"""
    app = create_app()
    
    with app.app_context():
        print("=== 修行记录统计数据诊断 ===\n")
        
        # 1. 查看所有修行记录
        records = ChantingRecord.query.all()
        print(f"总修行记录数: {len(records)}\n")
        
        for i, record in enumerate(records[:5]):  # 只看前5条
            print(f"--- 记录 {i+1} ---")
            print(f"ID: {record.id}")
            print(f"佛号ID: {record.chanting_id}")
            print(f"用户ID: {record.user_id}")
            
            # 获取对应的佛号信息
            chanting = Chanting.query.get(record.chanting_id)
            if chanting:
                print(f"佛号名称: {chanting.title}")
            else:
                print("佛号信息: 未找到")
            
            # 查看该记录对应的统计数据
            stats = DailyStats.query.filter_by(
                chanting_id=record.chanting_id,
                user_id=record.user_id
            ).all()
            
            print(f"对应统计记录数: {len(stats)}")
            if stats:
                total = sum(stat.count for stat in stats)
                print(f"总念诵次数: {total}")
                print("详细统计:")
                for stat in stats:
                    print(f"  {stat.date}: {stat.count} 次")
            else:
                print("无统计数据")
            
            # 查看今日统计
            today = date.today()
            today_stat = DailyStats.query.filter_by(
                chanting_id=record.chanting_id,
                user_id=record.user_id,
                date=today
            ).first()
            
            if today_stat:
                print(f"今日念诵: {today_stat.count} 次")
            else:
                print("今日念诵: 0 次")
            
            print()
        
        # 2. 查看所有DailyStats记录
        all_stats = DailyStats.query.all()
        print(f"=== 所有DailyStats记录 ({len(all_stats)}条) ===")
        
        # 按用户分组显示
        user_stats = {}
        for stat in all_stats:
            user_id = stat.user_id or "NULL"
            if user_id not in user_stats:
                user_stats[user_id] = []
            user_stats[user_id].append(stat)
        
        for user_id, stats in user_stats.items():
            print(f"\n用户 {user_id} 的统计:")
            total = sum(stat.count for stat in stats)
            print(f"  总记录数: {len(stats)}")
            print(f"  总念诵次数: {total}")
            
            # 显示前几条
            for stat in stats[:3]:
                chanting = Chanting.query.get(stat.chanting_id)
                chanting_name = chanting.title if chanting else f"ID:{stat.chanting_id}"
                print(f"  {stat.date} {chanting_name}: {stat.count} 次")
            
            if len(stats) > 3:
                print(f"  ... 还有 {len(stats)-3} 条记录")

if __name__ == '__main__':
    diagnose_stats()
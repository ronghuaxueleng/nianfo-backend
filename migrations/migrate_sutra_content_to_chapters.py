#!/usr/bin/env python3
"""
数据迁移脚本：将现有经文内容迁移到第一章
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from utils.datetime_utils import now
from app import create_app

def migrate_sutra_content_to_chapters():
    """将现有经文内容迁移到第一章"""
    app = create_app('development')
    
    with app.app_context():
        print("开始迁移经文内容到章节...")
        
        # 获取所有经文类型的数据
        sutras = Chanting.query.filter_by(type='sutra', is_deleted=False).all()
        
        migrated_count = 0
        skipped_count = 0
        
        for sutra in sutras:
            # 检查是否已经有章节
            existing_chapters = Chapter.query.filter_by(
                chanting_id=sutra.id,
                is_deleted=False
            ).count()
            
            if existing_chapters > 0:
                print(f"跳过 '{sutra.title}' - 已有 {existing_chapters} 个章节")
                skipped_count += 1
                continue
            
            # 检查是否有内容需要迁移
            if not sutra.content or not sutra.content.strip():
                print(f"跳过 '{sutra.title}' - 无内容")
                skipped_count += 1
                continue
            
            # 创建第一章
            chapter = Chapter(
                chanting_id=sutra.id,
                chapter_number=1,
                title=f"{sutra.title} - 第一章",
                content=sutra.content,
                pronunciation=sutra.pronunciation,
                created_at=now()
            )
            
            try:
                db.session.add(chapter)
                db.session.commit()
                print(f"✓ 迁移 '{sutra.title}' 内容到第一章")
                migrated_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"✗ 迁移 '{sutra.title}' 失败: {e}")
        
        print(f"\n迁移完成:")
        print(f"  成功迁移: {migrated_count} 部经文")
        print(f"  跳过: {skipped_count} 部经文")
        print(f"  总计: {len(sutras)} 部经文")
        
        if migrated_count > 0:
            print(f"\n注意: 经文原有内容已复制到第一章中，")
            print(f"      可考虑清空经文表的 content 和 pronunciation 字段以节省空间")

if __name__ == '__main__':
    migrate_sutra_content_to_chapters()
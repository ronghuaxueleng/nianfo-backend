#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地藏经内容导入工具
批量导入所有章节的完整内容和注音
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models.chapter import Chapter
from utils.datetime_utils import now
from data.dizang_jing_complete import DIZANG_JING_CHAPTERS

def update_chapter(chanting_id, chapter_num, title, content, pronunciation):
    """更新单个章节内容"""
    try:
        chapter = Chapter.query.filter_by(
            chanting_id=chanting_id, 
            chapter_number=chapter_num
        ).first()
        
        if chapter:
            chapter.title = title
            chapter.content = content
            chapter.pronunciation = pronunciation
            chapter.updated_at = now()
            db.session.commit()
            
            print(f"✅ 第{chapter_num}品 '{title}' 更新成功")
            print(f"   内容长度: {len(content)} 字符")
            print(f"   注音长度: {len(pronunciation)} 字符")
            return True
        else:
            print(f"❌ 第{chapter_num}品未找到")
            return False
    except Exception as e:
        print(f"❌ 第{chapter_num}品更新失败: {str(e)}")
        return False

def batch_import():
    """批量导入所有可用的章节"""
    print("开始批量导入地藏经内容...")
    print("=" * 60)
    
    app = create_app('development')
    with app.app_context():
        chanting_id = 37  # 地藏菩萨本愿经 ID
        success_count = 0
        total_count = len(DIZANG_JING_CHAPTERS)
        
        for chapter_num, chapter_data in DIZANG_JING_CHAPTERS.items():
            success = update_chapter(
                chanting_id=chanting_id,
                chapter_num=chapter_num,
                title=chapter_data['title'],
                content=chapter_data['content'],
                pronunciation=chapter_data['pronunciation']
            )
            if success:
                success_count += 1
            print("-" * 60)
        
        print(f"\n导入完成: {success_count}/{total_count} 章节成功导入")
        
        if success_count == total_count:
            print("🎉 所有章节导入成功！")
        else:
            print(f"⚠️  {total_count - success_count} 个章节导入失败")

def check_content_status():
    """检查内容状态"""
    print("检查地藏经章节内容状态...")
    print("=" * 60)
    
    app = create_app('development')
    with app.app_context():
        chanting_id = 37  # 地藏菩萨本愿经 ID
        
        chapters = Chapter.query.filter_by(chanting_id=chanting_id).order_by(Chapter.chapter_number).all()
        
        for chapter in chapters:
            status = "✅ 完整" if len(chapter.content) > 100 else "❌ 占位符"
            pronunciation_status = "✅ 有注音" if chapter.pronunciation else "❌ 无注音"
            
            print(f"第{chapter.chapter_number}品: {chapter.title}")
            print(f"  内容: {status} ({len(chapter.content)} 字符)")
            print(f"  注音: {pronunciation_status} ({len(chapter.pronunciation or '')} 字符)")
            print("-" * 60)

def main():
    """主菜单"""
    while True:
        print("\n地藏经内容导入工具")
        print("=" * 40)
        print("1. 检查当前内容状态")
        print("2. 批量导入可用内容")
        print("3. 退出")
        
        choice = input("\n请选择操作 (1-3): ").strip()
        
        if choice == '1':
            check_content_status()
        elif choice == '2':
            batch_import()
        elif choice == '3':
            print("退出程序")
            break
        else:
            print("无效选择，请重试")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
地藏经内容填充助手
提供便捷的方法来填充地藏经各品的内容
"""
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from utils.pinyin_utils import PinyinGenerator
from utils.datetime_utils import now

def get_dizang_jing():
    """获取地藏经记录"""
    return Chanting.query.filter_by(
        title="地藏菩萨本愿经",
        type="sutra", 
        is_deleted=False
    ).first()

def list_chapters():
    """列出所有章节及其当前状态"""
    dizang_jing = get_dizang_jing()
    if not dizang_jing:
        print("未找到地藏经记录")
        return
    
    chapters = Chapter.query.filter_by(
        chanting_id=dizang_jing.id,
        is_deleted=False
    ).order_by(Chapter.chapter_number).all()
    
    print(f"地藏菩萨本愿经 (ID: {dizang_jing.id}) 章节列表：")
    print("=" * 80)
    
    for chapter in chapters:
        content_status = "已填充" if len(chapter.content) > 100 else "待填充"
        pronunciation_status = "有注音" if chapter.pronunciation else "无注音"
        
        print(f"第{chapter.chapter_number:2d}品: {chapter.title}")
        print(f"        状态: {content_status} | {pronunciation_status}")
        print(f"        内容长度: {len(chapter.content)} 字符")
        print()

def update_chapter_content(chapter_number, new_content):
    """
    更新章节内容
    
    Args:
        chapter_number (int): 章节序号
        new_content (str): 新的内容
    """
    dizang_jing = get_dizang_jing()
    if not dizang_jing:
        print("未找到地藏经记录")
        return False
    
    chapter = Chapter.query.filter_by(
        chanting_id=dizang_jing.id,
        chapter_number=chapter_number,
        is_deleted=False
    ).first()
    
    if not chapter:
        print(f"未找到第{chapter_number}品")
        return False
    
    # 更新内容和注音
    chapter.content = new_content
    chapter.pronunciation = PinyinGenerator.generate_simple_pinyin(new_content)
    chapter.updated_at = now()
    
    db.session.commit()
    
    print(f"第{chapter_number}品 '{chapter.title}' 内容更新成功")
    print(f"内容长度: {len(new_content)} 字符")
    print("注音已自动生成")
    
    return True

def show_chapter_preview(chapter_number, lines=10):
    """显示章节内容预览"""
    dizang_jing = get_dizang_jing()
    if not dizang_jing:
        print("未找到地藏经记录")
        return
    
    chapter = Chapter.query.filter_by(
        chanting_id=dizang_jing.id,
        chapter_number=chapter_number,
        is_deleted=False
    ).first()
    
    if not chapter:
        print(f"未找到第{chapter_number}品")
        return
    
    print(f"第{chapter_number}品: {chapter.title}")
    print("=" * 60)
    
    content_lines = chapter.content.split('\n')
    preview_lines = content_lines[:lines]
    
    for line in preview_lines:
        print(line)
    
    if len(content_lines) > lines:
        print(f"\n... (还有 {len(content_lines) - lines} 行)")
    
    print(f"\n总长度: {len(chapter.content)} 字符")

def main():
    """主函数"""
    print("地藏经内容填充助手")
    print("=" * 40)
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        while True:
            print("\n请选择操作：")
            print("1. 查看章节列表")
            print("2. 预览章节内容")
            print("3. 更新章节内容")  
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == '1':
                list_chapters()
                
            elif choice == '2':
                try:
                    chapter_num = int(input("请输入品数 (1-13): "))
                    if 1 <= chapter_num <= 13:
                        lines = int(input("预览行数 (默认10): ") or "10")
                        show_chapter_preview(chapter_num, lines)
                    else:
                        print("品数应在1-13之间")
                except ValueError:
                    print("请输入有效数字")
                    
            elif choice == '3':
                try:
                    chapter_num = int(input("请输入品数 (1-13): "))
                    if 1 <= chapter_num <= 13:
                        print("请输入新内容（输入END结束）：")
                        content_lines = []
                        while True:
                            line = input()
                            if line.strip() == "END":
                                break
                            content_lines.append(line)
                        
                        new_content = '\n'.join(content_lines)
                        if new_content.strip():
                            update_chapter_content(chapter_num, new_content)
                        else:
                            print("内容不能为空")
                    else:
                        print("品数应在1-13之间")
                except ValueError:
                    print("请输入有效数字")
                    
            elif choice == '4':
                print("再见！")
                break
                
            else:
                print("无效选项，请重试")

if __name__ == "__main__":
    main()
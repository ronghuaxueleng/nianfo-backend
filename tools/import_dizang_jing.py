#!/usr/bin/env python3
"""
地藏经数据导入工具
用于批量导入地藏菩萨本愿经的章节内容
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

def create_dizang_jing():
    """创建地藏经主记录"""
    # 检查是否已存在
    existing = Chanting.query.filter_by(
        title="地藏菩萨本愿经",
        type="sutra",
        is_deleted=False
    ).first()
    
    if existing:
        print(f"地藏经已存在，ID: {existing.id}")
        return existing
    
    # 创建新的地藏经记录
    dizang_jing = Chanting(
        title="地藏菩萨本愿经",
        content="",  # 内容由章节管理
        pronunciation="",
        type="sutra",
        is_built_in=True,
        user_id=None,  # 系统内置
        created_at=now()
    )
    
    db.session.add(dizang_jing)
    db.session.commit()
    
    print(f"创建地藏经记录，ID: {dizang_jing.id}")
    return dizang_jing

def get_dizang_jing_chapters():
    """
    获取地藏经章节结构
    返回章节标题列表，内容需要从合法来源获取
    """
    return [
        "忉利天宫神通品第一",
        "分身集会品第二", 
        "观众生业缘品第三",
        "阎浮众生业感品第四",
        "地狱名号品第五",
        "如来赞叹品第六",
        "利益存亡品第七",
        "阎罗王众赞叹品第八",
        "称佛名号品第九",
        "校量布施功德缘品第十",
        "地神护法品第十一",
        "见闻利益品第十二",
        "嘱累人天品第十三"
    ]

def import_chapter(chanting_id, chapter_number, title, content):
    """
    导入单个章节
    
    Args:
        chanting_id: 经文ID
        chapter_number: 章节序号
        title: 章节标题
        content: 章节内容
    """
    # 检查是否已存在
    existing = Chapter.query.filter_by(
        chanting_id=chanting_id,
        chapter_number=chapter_number,
        is_deleted=False
    ).first()
    
    if existing:
        print(f"章节 {chapter_number} 已存在，跳过")
        return
    
    # 生成注音
    pronunciation = PinyinGenerator.generate_simple_pinyin(content) if content else ""
    
    # 创建章节
    chapter = Chapter(
        chanting_id=chanting_id,
        chapter_number=chapter_number,
        title=title,
        content=content,
        pronunciation=pronunciation,
        created_at=now()
    )
    
    db.session.add(chapter)
    db.session.commit()
    
    print(f"导入章节 {chapter_number}: {title}")

def main():
    """主函数"""
    print("开始导入地藏经数据...")
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            # 创建地藏经主记录
            dizang_jing = create_dizang_jing()
            
            # 获取章节标题
            chapter_titles = get_dizang_jing_chapters()
            
            print(f"准备导入 {len(chapter_titles)} 个章节...")
            print()
            print("注意：您需要从合法来源获取经文内容。")
            print("建议来源：")
            print("1. 佛教正信网站（如佛门网、佛教在线等）")
            print("2. 开放版权的佛教经典数据库")
            print("3. 寺院官方发布的电子版经文")
            print()
            
            # 为每个章节创建占位记录（内容为空）
            for i, title in enumerate(chapter_titles, 1):
                placeholder_content = f"【{title}】\n\n（此处应填入完整的章节内容）\n\n请从合法来源获取经文内容后填入。"
                import_chapter(dizang_jing.id, i, title, placeholder_content)
            
            print()
            print("地藏经框架导入完成！")
            print(f"经文ID: {dizang_jing.id}")
            print("下一步：请在后台管理系统中编辑各章节，填入完整内容。")
            
        except Exception as e:
            print(f"导入过程中出现错误: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main()
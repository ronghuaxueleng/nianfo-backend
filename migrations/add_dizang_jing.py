#!/usr/bin/env python3
"""
地藏经数据导入脚本
《地藏菩萨本愿经》共13品，此脚本用于导入完整经文和章节
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from utils.datetime_utils import now
from app import create_app

# 地藏经章节结构
DIZANG_JING_CHAPTERS = [
    {
        "chapter_number": 1,
        "title": "忉利天宫神通品第一",
        "content_placeholder": "如是我闻：一时佛在忉利天，为母说法...",
        "pronunciation_placeholder": "rú shì wǒ wén：yī shí fó zài dāo lì tiān，wéi mǔ shuō fǎ..."
    },
    {
        "chapter_number": 2,
        "title": "分身集会品第二",
        "content_placeholder": "尔时十方无量世界，不可说不可说一切诸佛...",
        "pronunciation_placeholder": "ěr shí shí fāng wú liàng shì jiè，bù kě shuō bù kě shuō yī qiē zhū fó..."
    },
    {
        "chapter_number": 3,
        "title": "观众生业缘品第三",
        "content_placeholder": "尔时佛母摩耶夫人，恭敬合掌问地藏菩萨言...",
        "pronunciation_placeholder": "ěr shí fó mǔ mó yé fū rén，gōng jìng hé zhǎng wèn dì cáng pú sà yán..."
    },
    {
        "chapter_number": 4,
        "title": "阎浮众生业感品第四",
        "content_placeholder": "尔时地藏菩萨摩诃萨白佛言：世尊，我承佛如来威神力故...",
        "pronunciation_placeholder": "ěr shí dì cáng pú sà mó hē sà bái fó yán：shì zun，wǒ chéng fó rú lái wēi shén lì gù..."
    },
    {
        "chapter_number": 5,
        "title": "地狱名号品第五",
        "content_placeholder": "尔时普贤菩萨摩诃萨白地藏菩萨言...",
        "pronunciation_placeholder": "ěr shí pǔ xián pú sà mó hē sà bái dì cáng pú sà yán..."
    },
    {
        "chapter_number": 6,
        "title": "如来赞叹品第六",
        "content_placeholder": "尔时世尊举身放大光明，遍照百千万亿恒河沙等诸佛世界...",
        "pronunciation_placeholder": "ěr shí shì zun jǔ shēn fàng dà guáng míng，biàn zhào bǎi qiān wàn yì héng hé shā děng zhū fó shì jiè..."
    },
    {
        "chapter_number": 7,
        "title": "利益存亡品第七",
        "content_placeholder": "尔时地藏菩萨摩诃萨白佛言：世尊，我观是阎浮众生...",
        "pronunciation_placeholder": "ěr shí dì cáng pú sà mó hē sà bái fó yán：shì zun，wǒ guān shì yán fú zhòng shēng..."
    },
    {
        "chapter_number": 8,
        "title": "阎罗王众赞叹品第八",
        "content_placeholder": "尔时铁围山内，有无量鬼王，与阎罗天子...",
        "pronunciation_placeholder": "ěr shí tiě wéi shān nèi，yǒu wú liàng guǐ wáng，yǔ yán luó tiān zǐ..."
    },
    {
        "chapter_number": 9,
        "title": "称佛名号品第九",
        "content_placeholder": "尔时地藏菩萨摩诃萨白佛言：世尊，我今为未来众生演利益事...",
        "pronunciation_placeholder": "ěr shí dì cáng pú sà mó hē sà bái fó yán：shì zun，wǒ jīn wéi wèi lái zhòng shēng yǎn lì yì shì..."
    },
    {
        "chapter_number": 10,
        "title": "校量布施功德缘品第十",
        "content_placeholder": "尔时地藏菩萨摩诃萨，承佛威神，从座而起...",
        "pronunciation_placeholder": "ěr shí dì cáng pú sà mó hē sà，chéng fó wēi shén，cóng zuò ér qǐ..."
    },
    {
        "chapter_number": 11,
        "title": "地神护法品第十一",
        "content_placeholder": "尔时坚牢地神白佛言：世尊，我从昔来瞻视顶礼...",
        "pronunciation_placeholder": "ěr shí jiān láo dì shén bái fó yán：shì zun，wǒ cóng xī lái zhān shì dǐng lǐ..."
    },
    {
        "chapter_number": 12,
        "title": "见闻利益品第十二",
        "content_placeholder": "尔时世尊从顶门上，放百千万亿大毫相光...",
        "pronunciation_placeholder": "ěr shí shì zun cóng dǐng mén shàng，fàng bǎi qiān wàn yì dà háo xiāng guāng..."
    },
    {
        "chapter_number": 13,
        "title": "嘱累人天品第十三",
        "content_placeholder": "尔时世尊举金色臂，又摩地藏菩萨摩诃萨顶...",
        "pronunciation_placeholder": "ěr shí shì zun jǔ jīn sè bì，yòu mó dì cáng pú sà mó hē sà dǐng..."
    }
]

def add_dizang_jing():
    """添加地藏经到数据库"""
    app = create_app('development')
    
    with app.app_context():
        print("开始导入《地藏菩萨本愿经》...")
        
        # 检查是否已存在
        existing = Chanting.query.filter_by(
            title="地藏菩萨本愿经", 
            type="sutra",
            is_deleted=False
        ).first()
        
        if existing:
            print(f"经文已存在 (ID: {existing.id})，是否要重新导入章节？")
            response = input("输入 'y' 继续，其他键退出: ")
            if response.lower() != 'y':
                return
            chanting = existing
        else:
            # 创建经文记录
            chanting = Chanting(
                title="地藏菩萨本愿经",
                content="",  # 内容在章节中管理
                pronunciation="",  # 注音在章节中管理
                type="sutra",
                is_built_in=True,  # 标记为内置经文
                user_id=None,  # 系统内置
                created_at=now()
            )
            
            db.session.add(chanting)
            db.session.commit()
            print(f"创建经文记录成功 (ID: {chanting.id})")
        
        # 删除现有章节（如果重新导入）
        if existing:
            existing_chapters = Chapter.query.filter_by(
                chanting_id=chanting.id,
                is_deleted=False
            ).all()
            for chapter in existing_chapters:
                chapter.soft_delete()
            db.session.commit()
            print(f"删除现有 {len(existing_chapters)} 个章节")
        
        # 导入章节
        created_count = 0
        
        for chapter_data in DIZANG_JING_CHAPTERS:
            chapter = Chapter(
                chanting_id=chanting.id,
                chapter_number=chapter_data["chapter_number"],
                title=chapter_data["title"],
                content=chapter_data["content_placeholder"],
                pronunciation=chapter_data["pronunciation_placeholder"],
                created_at=now()
            )
            
            db.session.add(chapter)
            created_count += 1
            print(f"  创建第{chapter_data['chapter_number']}品: {chapter_data['title']}")
        
        db.session.commit()
        
        print(f"\n导入完成:")
        print(f"  经文: 地藏菩萨本愿经")
        print(f"  章节: {created_count} 品")
        print(f"  状态: 成功")
        
        print(f"\n⚠️  重要提示:")
        print(f"  1. 当前章节内容为占位文本")
        print(f"  2. 请在后台管理界面中编辑每个章节，添加完整的经文内容")
        print(f"  3. 建议从权威佛教网站获取完整经文和注音")
        print(f"  4. 经文ID: {chanting.id}，可通过以下URL访问章节管理:")
        print(f"     http://localhost:5000/sutra/{chanting.id}/chapters")

def get_content_sources():
    """显示获取完整经文内容的建议来源"""
    print("\n📚 建议的经文来源:")
    print("1. 中国佛教协会官网")
    print("2. 佛光山全球资讯网")
    print("3. 法鼓山数位典藏")
    print("4. 佛学多媒体资料库")
    print("5. 大正藏数字版")
    print("\n🔊 注音来源建议:")
    print("1. 佛教念诵集")
    print("2. 佛经念诵音频对照")
    print("3. 佛学院标准读音")
    
    print("\n⚠️  注意事项:")
    print("- 请确保使用的文本来源合法")
    print("- 建议使用多个来源对比校正")
    print("- 注音应符合佛教读音传统")

if __name__ == '__main__':
    print("🙏 地藏菩萨本愿经导入工具")
    print("=" * 50)
    
    choice = input("请选择操作:\n1. 导入经文框架\n2. 查看内容来源建议\n请输入数字 (1或2): ")
    
    if choice == '1':
        add_dizang_jing()
    elif choice == '2':
        get_content_sources()
    else:
        print("输入无效，程序退出。")
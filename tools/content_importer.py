#!/usr/bin/env python3
"""
地藏经内容导入工具
用于批量导入从权威来源获取的完整经文内容和注音

使用方法:
1. 从权威佛教网站获取完整的地藏经内容
2. 按照本文件中的CHAPTER_CONTENTS模板格式填充内容
3. 运行此脚本自动导入到数据库

权威来源建议:
- 中华电子佛典协会 (CBETA): http://www.cbeta.org
- 佛光山全球资讯网
- 中国佛教协会官网
- 法鼓山数位典藏
- 灵隐寺官网
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from utils.datetime_utils import now
from app import create_app

# 地藏经完整内容模板
# 请从权威佛教网站获取完整内容后，替换以下占位内容
CHAPTER_CONTENTS = {
    1: {
        "title": "忉利天宫神通品第一",
        "content": """请在此处填入第一品的完整经文内容

使用步骤:
1. 访问权威佛教网站（如CBETA、佛光山等）
2. 复制第一品完整经文内容
3. 替换此占位文本
4. 保持原有的段落格式和标点符号

注意事项:
- 请确保内容来源合法
- 建议使用大正藏版本
- 保持传统标点符号格式""",
        
        "pronunciation": """请在此处填入第一品的完整汉语拼音注音

格式要求:
- 使用汉语拼音标注
- 与经文内容逐句对应
- 遵循佛教读音传统
- 特殊术语参考权威读音

示例格式:
rú shì wǒ wén：
yī shí fó zài dāo lì tiān，wéi mǔ shuō fǎ。
..."""
    },
    
    2: {
        "title": "分身集会品第二", 
        "content": "请填入第二品完整经文内容...",
        "pronunciation": "请填入第二品完整注音..."
    },
    
    3: {
        "title": "观众生业缘品第三",
        "content": "请填入第三品完整经文内容...",
        "pronunciation": "请填入第三品完整注音..."
    },
    
    4: {
        "title": "阎浮众生业感品第四",
        "content": "请填入第四品完整经文内容...",
        "pronunciation": "请填入第四品完整注音..."
    },
    
    5: {
        "title": "地狱名号品第五",
        "content": "请填入第五品完整经文内容...",
        "pronunciation": "请填入第五品完整注音..."
    },
    
    6: {
        "title": "如来赞叹品第六",
        "content": "请填入第六品完整经文内容...",
        "pronunciation": "请填入第六品完整注音..."
    },
    
    7: {
        "title": "利益存亡品第七",
        "content": "请填入第七品完整经文内容...",
        "pronunciation": "请填入第七品完整注音..."
    },
    
    8: {
        "title": "阎罗王众赞叹品第八",
        "content": "请填入第八品完整经文内容...",
        "pronunciation": "请填入第八品完整注音..."
    },
    
    9: {
        "title": "称佛名号品第九",
        "content": "请填入第九品完整经文内容...",
        "pronunciation": "请填入第九品完整注音..."
    },
    
    10: {
        "title": "校量布施功德缘品第十",
        "content": "请填入第十品完整经文内容...",
        "pronunciation": "请填入第十品完整注音..."
    },
    
    11: {
        "title": "地神护法品第十一",
        "content": "请填入第十一品完整经文内容...",
        "pronunciation": "请填入第十一品完整注音..."
    },
    
    12: {
        "title": "见闻利益品第十二",
        "content": "请填入第十二品完整经文内容...",
        "pronunciation": "请填入第十二品完整注音..."
    },
    
    13: {
        "title": "嘱累人天品第十三",
        "content": "请填入第十三品完整经文内容...",
        "pronunciation": "请填入第十三品完整注音..."
    }
}

def validate_content(chapter_num, data):
    """验证内容是否已填充（不是占位文本）"""
    content = data.get('content', '')
    pronunciation = data.get('pronunciation', '')
    
    # 检查是否还是占位文本
    placeholder_indicators = [
        "请填入", "请在此处填入", "占位", "placeholder",
        "使用步骤", "注意事项", "示例格式"
    ]
    
    for indicator in placeholder_indicators:
        if indicator in content or indicator in pronunciation:
            return False, f"第{chapter_num}品内容或注音仍为占位文本，请先填入完整内容"
    
    # 检查基本长度要求
    if len(content.strip()) < 100:
        return False, f"第{chapter_num}品内容过短，可能不是完整经文"
    
    if len(pronunciation.strip()) < 50:
        return False, f"第{chapter_num}品注音过短，可能不是完整注音"
    
    return True, "验证通过"

def import_single_chapter(chanting_id, chapter_num):
    """导入单个章节"""
    if chapter_num not in CHAPTER_CONTENTS:
        print(f"❌ 错误：第{chapter_num}品不存在")
        return False
    
    data = CHAPTER_CONTENTS[chapter_num]
    
    # 验证内容
    is_valid, message = validate_content(chapter_num, data)
    if not is_valid:
        print(f"❌ 验证失败：{message}")
        print(f"💡 请先编辑本文件，填入第{chapter_num}品的完整经文内容和注音")
        return False
    
    # 查找现有章节
    chapter = Chapter.query.filter_by(
        chanting_id=chanting_id,
        chapter_number=chapter_num,
        is_deleted=False
    ).first()
    
    if not chapter:
        print(f"❌ 错误：未找到第{chapter_num}品章节记录")
        return False
    
    # 更新内容
    chapter.title = data['title']
    chapter.content = data['content']
    chapter.pronunciation = data['pronunciation']
    chapter.updated_at = now()
    
    db.session.commit()
    print(f"✅ 成功更新第{chapter_num}品：{data['title']}")
    return True

def import_all_chapters(chanting_id):
    """导入所有章节"""
    print("开始批量导入所有章节...")
    
    success_count = 0
    failed_count = 0
    
    for chapter_num in range(1, 14):  # 1-13品
        print(f"\n处理第{chapter_num}品...")
        if import_single_chapter(chanting_id, chapter_num):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 导入结果统计:")
    print(f"  ✅ 成功: {success_count} 品")
    print(f"  ❌ 失败: {failed_count} 品")
    print(f"  📋 总计: {success_count + failed_count} 品")
    
    if success_count == 13:
        print("\n🎉 恭喜！地藏经所有章节内容导入成功！")
    elif success_count > 0:
        print(f"\n⚠️  部分章节导入成功，请检查失败的章节并补充内容")
    else:
        print(f"\n❌ 所有章节都未导入，请先填充经文内容")

def show_content_sources():
    """显示内容获取建议"""
    print("\n📚 权威经文来源推荐:")
    print("=" * 50)
    
    sources = [
        {
            "name": "中华电子佛典协会 (CBETA)",
            "url": "http://www.cbeta.org",
            "description": "最权威的电子佛典，含大正藏版本"
        },
        {
            "name": "佛光山全球资讯网", 
            "url": "官方网站搜索地藏经",
            "description": "标准化版本，校对精确"
        },
        {
            "name": "中国佛教协会官网",
            "url": "官方网站佛经专区",
            "description": "官方认可版本"
        },
        {
            "name": "法鼓山数位典藏",
            "url": "法鼓山官方网站",
            "description": "校对精确的数字版本"
        },
        {
            "name": "灵隐寺官网",
            "url": "https://www.lingyinsi.org",
            "description": "有PDF版本可下载"
        }
    ]
    
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   网址: {source['url']}")
        print(f"   说明: {source['description']}")
        print()
    
    print("🔊 注音获取建议:")
    print("- 佛教念诵集标准读音")
    print("- 各大佛学院权威发音")
    print("- 佛经念诵音频对照标注")
    print("- 权威法师念诵录音参考")
    
    print("\n⚠️  重要提示:")
    print("1. 请确保使用的文本来源合法合规")
    print("2. 建议使用多个权威来源对比校正")
    print("3. 注音应符合佛教传统读音")
    print("4. 保持原文的段落结构和标点符号")

def check_system_status():
    """检查系统状态"""
    app = create_app('development')
    
    with app.app_context():
        # 查找地藏经记录
        chanting = Chanting.query.filter_by(
            title="地藏菩萨本愿经",
            type="sutra", 
            is_deleted=False
        ).first()
        
        if not chanting:
            print("❌ 错误：未找到地藏菩萨本愿经记录")
            print("💡 请先运行 python migrations/add_dizang_jing.py 创建经文框架")
            return None
        
        # 统计章节状态
        chapters = Chapter.query.filter_by(
            chanting_id=chanting.id,
            is_deleted=False
        ).order_by(Chapter.chapter_number).all()
        
        print(f"📋 系统状态检查:")
        print(f"  经文ID: {chanting.id}")
        print(f"  经文标题: {chanting.title}")
        print(f"  章节总数: {len(chapters)}")
        
        if len(chapters) != 13:
            print(f"  ⚠️  警告：章节数量不正确，应为13品，实际为{len(chapters)}品")
        
        print(f"\n📝 章节状态:")
        filled_count = 0
        for chapter in chapters:
            # 简单检查是否为占位内容
            is_placeholder = any(indicator in chapter.content for indicator in 
                               ["如是我闻：一时佛在忉利天", "尔时十方无量世界", "占位", "待填充"])
            
            status = "🟡 占位文本" if is_placeholder else "✅ 已填充"
            if not is_placeholder:
                filled_count += 1
                
            print(f"  第{chapter.chapter_number:2d}品: {chapter.title} - {status}")
        
        print(f"\n📊 完成度统计:")
        print(f"  已填充: {filled_count} / 13 品")
        print(f"  完成度: {(filled_count/13)*100:.1f}%")
        
        return chanting.id

def main():
    """主函数"""
    print("🙏 地藏菩萨本愿经内容导入工具")
    print("=" * 60)
    
    # 检查系统状态
    chanting_id = check_system_status()
    if not chanting_id:
        return
    
    print("\n请选择操作:")
    print("1. 查看权威经文来源建议")
    print("2. 导入单个章节 (需要先填充内容)")
    print("3. 批量导入所有章节 (需要先填充所有内容)")
    print("4. 重新检查系统状态")
    print("5. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == '1':
            show_content_sources()
            
        elif choice == '2':
            try:
                chapter_num = int(input("请输入要导入的章节号 (1-13): "))
                if 1 <= chapter_num <= 13:
                    app = create_app('development')
                    with app.app_context():
                        import_single_chapter(chanting_id, chapter_num)
                else:
                    print("❌ 章节号必须在1-13之间")
            except ValueError:
                print("❌ 请输入有效的数字")
                
        elif choice == '3':
            confirm = input("⚠️  确定要批量导入所有章节吗？这会覆盖现有内容。(y/N): ")
            if confirm.lower() == 'y':
                app = create_app('development')
                with app.app_context():
                    import_all_chapters(chanting_id)
            else:
                print("操作已取消")
                
        elif choice == '4':
            check_system_status()
            
        elif choice == '5':
            print("程序退出。🙏")
            break
            
        else:
            print("❌ 无效选择，请输入 1-5")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
地藏经内容获取助手
帮助用户从合法来源获取地藏经内容
"""
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def show_legal_sources():
    """显示合法的内容获取来源"""
    print("=" * 60)
    print("地藏菩萨本愿经合法内容来源推荐")
    print("=" * 60)
    
    sources = [
        {
            "name": "佛门网",
            "url": "http://www.fomen123.com/",
            "description": "提供完整的电子版佛经，内容权威可靠"
        },
        {
            "name": "佛教在线",
            "url": "http://www.fjnet.com/",
            "description": "权威佛教资讯网站，有经典文献版块"
        },
        {
            "name": "CBETA中华电子佛典协会",
            "url": "http://www.cbeta.org/",
            "description": "学术级佛典数据库，提供标准化经文"
        },
        {
            "name": "学佛网",
            "url": "http://www.xuefo.net/",
            "description": "佛教学习网站，有经典诵读版块"
        },
        {
            "name": "弘善佛教网",
            "url": "http://www.liaotuo.org/",
            "description": "提供各种佛教经典的电子版本"
        }
    ]
    
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   网址: {source['url']}")
        print(f"   说明: {source['description']}")
        print()
    
    print("使用建议：")
    print("1. 优先选择CBETA等学术机构的版本")
    print("2. 对比多个来源确保内容准确性")
    print("3. 保持原文的段落和标点格式")
    print("4. 注意避免现代出版社的版权保护版本")

def show_chapter_templates():
    """显示章节内容模板格式"""
    print("=" * 60)
    print("章节内容格式模板")
    print("=" * 60)
    
    template = """地藏菩萨本愿经

【品名】第X品

【经文开始】
尔时...
（经文正文）
...佛说此经已。

【回向】
（可选，包含回向文）
"""
    
    print(template)
    print("格式说明：")
    print("1. 保持品名格式统一")
    print("2. 经文内容完整，包含开头和结尾")
    print("3. 适当的段落分行便于阅读")
    print("4. 保持传统标点符号使用")

def show_usage_steps():
    """显示具体使用步骤"""
    print("=" * 60)
    print("内容填充操作步骤")
    print("=" * 60)
    
    steps = [
        "1. 从合法来源复制经文内容",
        "2. 整理格式（保持段落分行）",
        "3. 运行填充工具: python tools/fill_dizang_content.py",
        "4. 选择选项3（更新章节内容）",
        "5. 输入品数（3-13）",
        "6. 粘贴经文内容",
        "7. 输入END结束",
        "8. 系统自动生成注音"
    ]
    
    for step in steps:
        print(step)
    
    print("\n或者使用后台管理系统：")
    print("1. 启动服务: python run.py")
    print("2. 访问后台管理页面")
    print("3. 进入经文管理 → 地藏菩萨本愿经 → 章节管理")
    print("4. 点击编辑按钮填入内容")

def main():
    """主函数"""
    print("地藏经内容获取助手")
    print("本工具帮助您从合法来源获取和填充地藏经内容")
    
    while True:
        print("\n" + "=" * 40)
        print("请选择查看内容：")
        print("1. 合法内容来源")
        print("2. 内容格式模板")
        print("3. 操作步骤说明")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            show_legal_sources()
        elif choice == '2':
            show_chapter_templates()
        elif choice == '3':
            show_usage_steps()
        elif choice == '4':
            print("感谢使用！建议从CBETA等权威来源获取经文内容。")
            break
        else:
            print("无效选项，请重试")

if __name__ == "__main__":
    main()
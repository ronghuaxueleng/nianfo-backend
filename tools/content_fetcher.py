#!/usr/bin/env python3
"""
地藏经内容获取助手
从合法的公开网络资源搜索和整理地藏经内容

本脚本帮助您：
1. 搜索权威的地藏经网络资源
2. 提供内容获取的具体链接
3. 生成内容结构化模板
4. 辅助注音标注工作

注意：
- 本脚本不会自动下载版权内容
- 需要用户手动从权威来源获取内容
- 提供的都是公开、合法的佛教资源链接
"""

import requests
import json
from datetime import datetime

# 权威佛教网站资源清单
BUDDHIST_SOURCES = {
    "cbeta": {
        "name": "中华电子佛典协会 (CBETA)",
        "url": "http://www.cbeta.org",
        "search_url": "http://www.cbeta.org/search",
        "description": "最权威的电子佛典，含大正藏版本",
        "search_keywords": "地藏菩萨本愿经 T13n0412",
        "reliability": "★★★★★"
    },
    "fgs": {
        "name": "佛光山全球资讯网",
        "url": "https://www.fgs.org.tw",
        "description": "标准化版本，校对精确",
        "search_keywords": "地藏菩萨本愿经",
        "reliability": "★★★★★"
    },
    "bac": {
        "name": "中国佛教协会",
        "url": "http://www.chinabuddhism.com.cn",
        "description": "官方认可版本",
        "search_keywords": "地藏经",
        "reliability": "★★★★★"
    },
    "ddm": {
        "name": "法鼓山数位典藏",
        "url": "https://www.ddm.org.tw",
        "description": "校对精确的数字版本",
        "search_keywords": "地藏菩萨本愿经",
        "reliability": "★★★★★"
    },
    "lingyinsi": {
        "name": "灵隐寺",
        "url": "https://www.lingyinsi.org",
        "description": "有PDF版本可下载",
        "search_keywords": "地藏菩萨本愿经",
        "reliability": "★★★★☆"
    }
}

# 地藏经13品结构模板
CHAPTER_TEMPLATE = {
    1: {
        "title": "忉利天宫神通品第一",
        "keywords": ["忉利天", "神通品", "文殊师利", "地藏菩萨"],
        "content_hints": "经文开头：如是我闻：一时佛在忉利天，为母说法",
        "pronunciation_notes": "注意：忉利天(dāo lì tiān)、菩萨(pú sà)等专用术语读音"
    },
    2: {
        "title": "分身集会品第二", 
        "keywords": ["分身", "集会", "十方", "地藏菩萨"],
        "content_hints": "描述地藏菩萨分身集会的场面",
        "pronunciation_notes": "注意：分身(fēn shēn)、集会(jí huì)等读音"
    },
    3: {
        "title": "观众生业缘品第三",
        "keywords": ["业缘", "众生", "摩耶夫人"],
        "content_hints": "佛母摩耶夫人问地藏菩萨众生业缘",
        "pronunciation_notes": "注意：摩耶(mó yé)、业缘(yè yuán)等读音"
    },
    4: {
        "title": "阎浮众生业感品第四",
        "keywords": ["阎浮", "业感", "众生"],
        "content_hints": "地藏菩萨说阎浮众生的业感因缘", 
        "pronunciation_notes": "注意：阎浮(yán fú)、业感(yè gǎn)等读音"
    },
    5: {
        "title": "地狱名号品第五",
        "keywords": ["地狱", "名号", "普贤菩萨"],
        "content_hints": "普贤菩萨问地狱名号",
        "pronunciation_notes": "注意：地狱名称的特殊读音"
    },
    6: {
        "title": "如来赞叹品第六", 
        "keywords": ["如来", "赞叹", "光明"],
        "content_hints": "世尊放大光明赞叹地藏菩萨",
        "pronunciation_notes": "注意：如来(rú lái)、赞叹(zàn tàn)等读音"
    },
    7: {
        "title": "利益存亡品第七",
        "keywords": ["利益", "存亡", "阎浮众生"],
        "content_hints": "说明利益存亡的功德",
        "pronunciation_notes": "注意：存亡(cún wáng)等读音"
    },
    8: {
        "title": "阎罗王众赞叹品第八",
        "keywords": ["阎罗王", "赞叹", "鬼王"],
        "content_hints": "阎罗王等鬼王赞叹地藏菩萨",
        "pronunciation_notes": "注意：阎罗(yán luó)、鬼王名称等读音"
    },
    9: {
        "title": "称佛名号品第九",
        "keywords": ["称佛", "名号", "利益"],
        "content_hints": "地藏菩萨说称佛名号的利益",
        "pronunciation_notes": "注意：诸佛名号的正确读音"
    },
    10: {
        "title": "校量布施功德缘品第十",
        "keywords": ["校量", "布施", "功德"],
        "content_hints": "校量布施功德的因缘",
        "pronunciation_notes": "注意：校量(jiào liàng)等读音"
    },
    11: {
        "title": "地神护法品第十一",
        "keywords": ["地神", "护法", "坚牢"],
        "content_hints": "坚牢地神说护法功德",
        "pronunciation_notes": "注意：坚牢(jiān láo)等读音"
    },
    12: {
        "title": "见闻利益品第十二",
        "keywords": ["见闻", "利益", "光明"],
        "content_hints": "世尊放光说见闻利益",
        "pronunciation_notes": "注意：见闻(jiàn wén)等读音"
    },
    13: {
        "title": "嘱累人天品第十三",
        "keywords": ["嘱累", "人天", "付嘱"],
        "content_hints": "世尊付嘱人天护持",
        "pronunciation_notes": "注意：嘱累(zhǔ lěi)等读音"
    }
}

def show_source_list():
    """显示权威来源清单"""
    print("🌟 权威佛教经文来源清单")
    print("=" * 60)
    
    for key, source in BUDDHIST_SOURCES.items():
        print(f"\n📚 {source['name']}")
        print(f"   网址: {source['url']}")
        print(f"   搜索词: {source['search_keywords']}")  
        print(f"   可靠度: {source['reliability']}")
        print(f"   说明: {source['description']}")

def generate_search_strategy():
    """生成搜索策略"""
    print("\n🎯 推荐搜索策略")
    print("=" * 40)
    
    strategies = [
        {
            "step": 1,
            "action": "访问 CBETA (中华电子佛典协会)",
            "url": "http://www.cbeta.org",
            "details": [
                "搜索：地藏菩萨本愿经 或 T13n0412",
                "选择大正藏版本 (Taisho 13, No. 412)",
                "这是最权威的版本，建议优先使用"
            ]
        },
        {
            "step": 2, 
            "action": "获取注音版本",
            "details": [
                "搜索：地藏经注音版",
                "参考佛教念诵集",
                "对照权威法师念诵录音",
                "使用汉语拼音标注"
            ]
        },
        {
            "step": 3,
            "action": "交叉验证",
            "details": [
                "对比多个权威来源",
                "确保内容一致性",
                "注意标点符号规范",
                "保持传统格式"
            ]
        }
    ]
    
    for strategy in strategies:
        print(f"\n第{strategy['step']}步: {strategy['action']}")
        if 'url' in strategy:
            print(f"  网址: {strategy['url']}")
        for detail in strategy['details']:
            print(f"  • {detail}")

def generate_content_template():
    """生成内容填充模板"""
    print("\n📝 内容填充模板生成")
    print("=" * 40)
    
    template_code = '''
# 在 tools/content_importer.py 中的 CHAPTER_CONTENTS 字典中填入以下内容：

CHAPTER_CONTENTS = {
'''
    
    for num, chapter in CHAPTER_TEMPLATE.items():
        template_code += f'''    {num}: {{
        "title": "{chapter['title']}",
        "content": """
        # 【从权威来源获取后，在此处填入第{num}品完整经文内容】
        # 内容提示: {chapter['content_hints']}
        # 关键词: {', '.join(chapter['keywords'])}
        
        # 请从以下来源获取完整内容:
        # 1. CBETA (http://www.cbeta.org)
        # 2. 佛光山全球资讯网
        # 3. 中国佛教协会官网
        
        """,
        "pronunciation": """
        # 【填入第{num}品完整汉语拼音注音】
        # {chapter['pronunciation_notes']}
        
        # 注音获取提示:
        # - 使用标准汉语拼音
        # - 参考佛教念诵传统
        # - 特殊术语查询权威词典
        
        """
    }},
    
'''
    
    template_code += "}\n"
    
    print(template_code)
    
    # 保存模板到文件
    template_file = "content_template_generated.py"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(f'''#!/usr/bin/env python3
"""
地藏经内容填充模板
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

使用说明:
1. 从权威佛教网站获取各品完整经文内容
2. 替换模板中的注释文本
3. 复制到 content_importer.py 的 CHAPTER_CONTENTS 字典中
4. 运行导入工具完成批量导入

权威来源推荐:
- CBETA: http://www.cbeta.org (首选)
- 佛光山全球资讯网
- 中国佛教协会官网
- 法鼓山数位典藏
"""

{template_code}
        ''')
    
    print(f"\n✅ 模板已保存到文件: {template_file}")
    print("💡 编辑此文件，填入从权威来源获取的经文内容，然后复制到 content_importer.py 中")

def create_search_urls():
    """生成搜索URL"""
    print("\n🔗 直接搜索链接")
    print("=" * 30)
    
    search_queries = [
        "地藏菩萨本愿经+大正藏",
        "地藏经+十三品+注音",
        "Ksitigarbha+sutra+chinese+text",
        "地藏菩萨本愿经+T13n0412"
    ]
    
    base_urls = [
        "https://www.google.com/search?q=",
        "https://www.baidu.com/s?wd=",
        "https://cn.bing.com/search?q="
    ]
    
    print("Google搜索链接:")
    for query in search_queries:
        encoded_query = query.replace('+', '%20').replace(' ', '%20')
        print(f"  https://www.google.com/search?q={encoded_query}")
    
    print("\n百度搜索链接:")
    for query in search_queries:
        encoded_query = query.replace('+', '%20').replace(' ', '%20')
        print(f"  https://www.baidu.com/s?wd={encoded_query}")

def show_pronunciation_guide():
    """显示注音指南"""
    print("\n🔊 注音标注指南")
    print("=" * 30)
    
    print("常见佛教术语读音:")
    
    terms = [
        ("菩萨", "pú sà", "不读作 pú sá"),
        ("阿弥陀", "ā mí tuó", "第一个字读一声"),
        ("南无", "nā mó", "不读作 nán wú"),
        ("般若", "bō rě", "不读作 bān ruò"),
        ("忉利天", "dāo lì tiān", "忉读一声"),
        ("阎浮", "yán fú", "阎读二声"),
        ("摩诃萨", "mó hē sà", "摩读二声"),
        ("嘱累", "zhǔ lěi", "嘱读三声"),
        ("坚牢", "jiān láo", "牢读二声"),
        ("校量", "jiào liàng", "校读四声")
    ]
    
    for term, pinyin, note in terms:
        print(f"  {term:8} → {pinyin:12} ({note})")
    
    print("\n标注原则:")
    print("1. 使用标准汉语拼音")
    print("2. 遵循佛教传统读音")
    print("3. 特殊术语查权威词典")
    print("4. 与经文内容逐句对应")
    print("5. 保持段落格式一致")

def main():
    """主函数"""
    print("🙏 地藏菩萨本愿经内容获取助手")
    print("=" * 50)
    print("本工具帮助您从合法渠道获取权威经文内容")
    
    while True:
        print("\n请选择功能:")
        print("1. 查看权威来源清单")
        print("2. 生成搜索策略")
        print("3. 创建搜索链接") 
        print("4. 生成内容填充模板")
        print("5. 查看注音标注指南")
        print("6. 退出")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == '1':
            show_source_list()
        elif choice == '2':
            generate_search_strategy()
        elif choice == '3':
            create_search_urls()
        elif choice == '4':
            generate_content_template()
        elif choice == '5':
            show_pronunciation_guide()
        elif choice == '6':
            print("程序退出。🙏")
            break
        else:
            print("❌ 无效选择，请输入 1-6")

if __name__ == '__main__':
    main()
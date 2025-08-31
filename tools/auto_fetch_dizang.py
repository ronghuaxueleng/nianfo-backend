#!/usr/bin/env python3
"""
地藏经内容自动抓取脚本
从合法来源自动获取并填充地藏经各品内容
"""
import sys
import os
import time
import re
import requests
from bs4 import BeautifulSoup

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from utils.pinyin_utils import PinyinGenerator
from utils.datetime_utils import now

# 代理配置
PROXY_CONFIG = {
    'http': 'http://192.168.10.11:1080',
    'https': 'http://192.168.10.11:1080'
}

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# 地藏经各品的抓取配置
CHAPTER_SOURCES = {
    3: {
        'title': '观众生业缘品第三',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3818.html',
            'http://www.xuefo.net/nr/article54/544603.html',
            'https://www.budaedu.org/jing/dizang/dzpsbyjing03.php'
        ]
    },
    4: {
        'title': '阎浮众生业感品第四',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3819.html',
            'http://www.xuefo.net/nr/article54/544604.html'
        ]
    },
    5: {
        'title': '地狱名号品第五',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3820.html',
            'http://www.xuefo.net/nr/article54/544605.html'
        ]
    },
    6: {
        'title': '如来赞叹品第六',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3821.html',
            'http://www.xuefo.net/nr/article54/544606.html'
        ]
    },
    7: {
        'title': '利益存亡品第七',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3822.html',
            'http://www.xuefo.net/nr/article54/544607.html'
        ]
    },
    8: {
        'title': '阎罗王众赞叹品第八',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3823.html',
            'http://www.xuefo.net/nr/article54/544608.html'
        ]
    },
    9: {
        'title': '称佛名号品第九',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3824.html',
            'http://www.xuefo.net/nr/article54/544609.html'
        ]
    },
    10: {
        'title': '校量布施功德缘品第十',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3825.html',
            'http://www.xuefo.net/nr/article54/544610.html'
        ]
    },
    11: {
        'title': '地神护法品第十一',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3826.html',
            'http://www.xuefo.net/nr/article54/544611.html'
        ]
    },
    12: {
        'title': '见闻利益品第十二',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3827.html',
            'http://www.xuefo.net/nr/article54/544612.html'
        ]
    },
    13: {
        'title': '嘱累人天品第十三',
        'urls': [
            'http://www.fomen123.com/fo/jing/dizangjing/3828.html',
            'http://www.xuefo.net/nr/article54/544613.html'
        ]
    }
}

def fetch_content(url, use_proxy=True):
    """
    从指定URL获取网页内容
    
    Args:
        url (str): 目标URL
        use_proxy (bool): 是否使用代理
    
    Returns:
        str: 网页HTML内容
    """
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        proxies = PROXY_CONFIG if use_proxy else None
        
        print(f"正在请求: {url}")
        response = session.get(url, proxies=proxies, timeout=30, verify=False)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            print(f"✓ 请求成功: {url}")
            return response.text
        else:
            print(f"✗ 请求失败: {url}, 状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ 请求异常: {url}, 错误: {str(e)}")
        return None

def parse_content(html, url):
    """
    解析HTML提取经文内容
    
    Args:
        html (str): HTML内容
        url (str): 来源URL
        
    Returns:
        str: 提取的经文文本
    """
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 根据不同网站的结构提取内容
        content = None
        
        if 'fomen123.com' in url:
            # 佛门网的内容结构
            content_div = soup.find('div', class_='content') or soup.find('div', class_='article-content')
            if content_div:
                content = content_div.get_text(strip=True)
        
        elif 'xuefo.net' in url:
            # 学佛网的内容结构
            content_div = soup.find('div', class_='content') or soup.find('div', id='content')
            if content_div:
                content = content_div.get_text(strip=True)
        
        elif 'budaedu.org' in url:
            # 其他网站的通用提取
            content_div = soup.find('div', class_='content') or soup.find('article')
            if content_div:
                content = content_div.get_text(strip=True)
        
        # 通用提取方法
        if not content:
            # 尝试提取主要内容区域
            for selector in ['#content', '.content', '.article', '.post', 'main', '.main']:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break
        
        # 如果还没找到，提取body中的文本
        if not content:
            body = soup.find('body')
            if body:
                content = body.get_text(strip=True)
        
        if content:
            # 清理文本
            content = clean_text(content)
            print(f"✓ 内容提取成功，长度: {len(content)} 字符")
            return content
        else:
            print(f"✗ 内容提取失败: {url}")
            return None
            
    except Exception as e:
        print(f"✗ 解析异常: {url}, 错误: {str(e)}")
        return None

def clean_text(text):
    """
    清理提取的文本内容
    
    Args:
        text (str): 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 恢复段落分隔
    text = re.sub(r'([。！？])\s+', r'\1\n\n', text)
    
    # 移除网站相关的无关内容
    unwanted_patterns = [
        r'.*?版权所有.*?',
        r'.*?转载请注明.*?',
        r'.*?免责声明.*?',
        r'.*?联系我们.*?',
        r'.*?首页.*?',
        r'.*?导航.*?',
        r'.*?菜单.*?',
        r'分享到.*?',
        r'上一篇.*?下一篇',
        r'相关阅读',
        r'热门推荐'
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 确保以品名开头
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    return '\n'.join(cleaned_lines)

def get_chapter_content(chapter_num):
    """
    获取指定品的内容
    
    Args:
        chapter_num (int): 品数
        
    Returns:
        str: 经文内容
    """
    if chapter_num not in CHAPTER_SOURCES:
        print(f"第{chapter_num}品配置不存在")
        return None
    
    chapter_info = CHAPTER_SOURCES[chapter_num]
    print(f"\n开始获取第{chapter_num}品: {chapter_info['title']}")
    
    # 尝试从多个源获取内容
    for i, url in enumerate(chapter_info['urls']):
        print(f"尝试源 {i+1}: {url}")
        
        # 先尝试使用代理
        html = fetch_content(url, use_proxy=True)
        if not html:
            # 如果代理失败，尝试直连
            print("代理请求失败，尝试直连...")
            time.sleep(2)
            html = fetch_content(url, use_proxy=False)
        
        if html:
            content = parse_content(html, url)
            if content and len(content) > 500:  # 确保内容足够长
                print(f"✓ 第{chapter_num}品内容获取成功")
                return content
        
        # 请求间隔
        time.sleep(3)
    
    print(f"✗ 第{chapter_num}品内容获取失败")
    return None

def update_chapter_in_db(chapter_num, content):
    """
    更新数据库中的章节内容
    
    Args:
        chapter_num (int): 品数
        content (str): 经文内容
    """
    app = create_app()
    with app.app_context():
        try:
            # 获取地藏经记录
            dizang_jing = Chanting.query.filter_by(
                title="地藏菩萨本愿经",
                type="sutra",
                is_deleted=False
            ).first()
            
            if not dizang_jing:
                print("未找到地藏经记录")
                return False
            
            # 获取章节记录
            chapter = Chapter.query.filter_by(
                chanting_id=dizang_jing.id,
                chapter_number=chapter_num,
                is_deleted=False
            ).first()
            
            if not chapter:
                print(f"未找到第{chapter_num}品记录")
                return False
            
            # 更新内容和注音
            chapter.content = content
            chapter.pronunciation = PinyinGenerator.generate_simple_pinyin(content)
            chapter.updated_at = now()
            
            db.session.commit()
            
            print(f"✓ 第{chapter_num}品数据库更新成功")
            print(f"  内容长度: {len(content)} 字符")
            print(f"  注音已自动生成")
            return True
            
        except Exception as e:
            print(f"✗ 第{chapter_num}品数据库更新失败: {str(e)}")
            db.session.rollback()
            return False

def main():
    """主函数"""
    print("地藏经内容自动抓取脚本")
    print("=" * 50)
    print("代理配置:", PROXY_CONFIG['http'])
    print("=" * 50)
    
    # 获取需要填充的品目
    chapters_to_fetch = list(range(3, 14))  # 第3-13品
    
    success_count = 0
    
    for chapter_num in chapters_to_fetch:
        try:
            print(f"\n{'='*20} 第{chapter_num}品 {'='*20}")
            
            # 获取内容
            content = get_chapter_content(chapter_num)
            
            if content:
                # 更新数据库
                if update_chapter_in_db(chapter_num, content):
                    success_count += 1
                    print(f"✓ 第{chapter_num}品处理完成")
                else:
                    print(f"✗ 第{chapter_num}品数据库更新失败")
            else:
                print(f"✗ 第{chapter_num}品内容获取失败")
            
            # 处理间隔
            time.sleep(5)
            
        except KeyboardInterrupt:
            print(f"\n用户中断，已处理 {success_count} 品")
            break
        except Exception as e:
            print(f"✗ 第{chapter_num}品处理异常: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"抓取完成！成功处理 {success_count}/{len(chapters_to_fetch)} 品")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
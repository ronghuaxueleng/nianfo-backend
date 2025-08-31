#!/usr/bin/env python3
"""
地藏经内容优化抓取脚本
使用192.168.10.11:1080代理，优化错误处理和重试机制
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
}

# 简化的抓取源配置
SIMPLE_SOURCES = {
    3: {
        'title': '观众生业缘品第三',
        'url': 'https://www.xuefo.net/nr/article54/544603.html'
    },
    4: {
        'title': '阎浮众生业感品第四',
        'url': 'https://www.xuefo.net/nr/article54/544604.html'
    },
    5: {
        'title': '地狱名号品第五',
        'url': 'https://www.xuefo.net/nr/article54/544605.html'
    },
    6: {
        'title': '如来赞叹品第六',
        'url': 'https://www.xuefo.net/nr/article54/544606.html'
    },
    7: {
        'title': '利益存亡品第七',
        'url': 'https://www.xuefo.net/nr/article54/544607.html'
    },
    8: {
        'title': '阎罗王众赞叹品第八',
        'url': 'https://www.xuefo.net/nr/article54/544608.html'
    },
    9: {
        'title': '称佛名号品第九',
        'url': 'https://www.xuefo.net/nr/article54/544609.html'
    },
    10: {
        'title': '校量布施功德缘品第十',
        'url': 'https://www.xuefo.net/nr/article54/544610.html'
    },
    11: {
        'title': '地神护法品第十一',
        'url': 'https://www.xuefo.net/nr/article54/544611.html'
    },
    12: {
        'title': '见闻利益品第十二',
        'url': 'https://www.xuefo.net/nr/article54/544612.html'
    },
    13: {
        'title': '嘱累人天品第十三',
        'url': 'https://www.xuefo.net/nr/article54/544613.html'
    }
}

def fetch_with_retry(url, max_retries=3):
    """
    带重试机制的请求函数
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for attempt in range(max_retries):
        try:
            print(f"  尝试 {attempt + 1}/{max_retries}: {url}")
            
            response = session.get(
                url, 
                proxies=PROXY_CONFIG,
                timeout=20,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                response.encoding = 'utf-8'
                print(f"  ✓ 请求成功: {len(response.text)} 字符")
                return response.text
            else:
                print(f"  ✗ HTTP错误: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ✗ 超时错误")
        except requests.exceptions.ConnectionError:
            print(f"  ✗ 连接错误")
        except Exception as e:
            print(f"  ✗ 其他错误: {str(e)}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 5
            print(f"  等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    return None

def extract_content(html, chapter_num):
    """
    提取经文内容
    """
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # 查找内容
        content_text = None
        
        # 多种选择器尝试
        selectors = [
            '.content',
            '#content', 
            '.article-content',
            '.post-content',
            '.entry-content',
            'article',
            '.main-content',
            'main'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                content_text = element.get_text(separator='\n', strip=True)
                if len(content_text) > 500:  # 内容足够长
                    break
        
        # 如果还没找到，使用body
        if not content_text or len(content_text) < 500:
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator='\n', strip=True)
        
        if content_text:
            # 清理文本
            cleaned = clean_content(content_text, chapter_num)
            print(f"  ✓ 内容提取成功: {len(cleaned)} 字符")
            return cleaned
        
    except Exception as e:
        print(f"  ✗ 解析错误: {str(e)}")
    
    return None

def clean_content(text, chapter_num):
    """
    清理提取的内容
    """
    if not text:
        return ""
    
    # 按行处理
    lines = text.split('\n')
    cleaned_lines = []
    
    # 查找经文开始位置
    content_started = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过无关内容
        skip_patterns = [
            r'.*?版权.*?',
            r'.*?转载.*?',
            r'.*?声明.*?',
            r'.*?联系.*?',
            r'.*?首页.*?',
            r'.*?导航.*?',
            r'.*?分享.*?',
            r'.*?推荐.*?',
            r'.*?相关.*?',
            r'.*?热门.*?',
            r'.*?点击.*?',
            r'.*?阅读.*?次',
            r'上一篇.*?下一篇',
            r'发表时间.*?',
            r'来源.*?',
            r'作者.*?'
        ]
        
        should_skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                should_skip = True
                break
        
        if should_skip:
            continue
        
        # 检查是否是品名开始
        title_patterns = [
            f'.*?第{chapter_num}品.*?',
            f'.*?品第{chapter_num}.*?',
            '.*?品.*?'
        ]
        
        for pattern in title_patterns:
            if re.search(pattern, line):
                content_started = True
                break
        
        # 检查经文特征词
        if not content_started:
            sutra_keywords = ['尔时', '佛言', '菩萨', '世尊', '如是我闻']
            for keyword in sutra_keywords:
                if keyword in line:
                    content_started = True
                    break
        
        if content_started:
            cleaned_lines.append(line)
    
    # 合并文本
    result = '\n'.join(cleaned_lines)
    
    # 最终清理
    result = re.sub(r'\n{3,}', '\n\n', result)  # 合并多个换行
    result = result.strip()
    
    return result

def update_database(chapter_num, content):
    """
    更新数据库
    """
    app = create_app()
    with app.app_context():
        try:
            # 获取地藏经
            dizang = Chanting.query.filter_by(
                title="地藏菩萨本愿经",
                type="sutra",
                is_deleted=False
            ).first()
            
            if not dizang:
                print("  ✗ 未找到地藏经记录")
                return False
            
            # 获取章节
            chapter = Chapter.query.filter_by(
                chanting_id=dizang.id,
                chapter_number=chapter_num,
                is_deleted=False
            ).first()
            
            if not chapter:
                print(f"  ✗ 未找到第{chapter_num}品记录")
                return False
            
            # 更新内容
            chapter.content = content
            chapter.pronunciation = PinyinGenerator.generate_simple_pinyin(content)
            chapter.updated_at = now()
            
            db.session.commit()
            print(f"  ✓ 数据库更新成功")
            return True
            
        except Exception as e:
            print(f"  ✗ 数据库更新失败: {str(e)}")
            db.session.rollback()
            return False

def process_chapter(chapter_num):
    """
    处理单个品
    """
    if chapter_num not in SIMPLE_SOURCES:
        print(f"第{chapter_num}品：配置不存在")
        return False
    
    source = SIMPLE_SOURCES[chapter_num]
    print(f"第{chapter_num}品：{source['title']}")
    
    # 获取内容
    html = fetch_with_retry(source['url'])
    if not html:
        print(f"  ✗ 获取失败")
        return False
    
    # 提取内容
    content = extract_content(html, chapter_num)
    if not content:
        print(f"  ✗ 提取失败")
        return False
    
    if len(content) < 200:
        print(f"  ✗ 内容太短: {len(content)} 字符")
        return False
    
    # 更新数据库
    return update_database(chapter_num, content)

def main():
    """
    主函数
    """
    print("地藏经内容抓取 - 优化版本")
    print("代理:", PROXY_CONFIG['http'])
    print("=" * 50)
    
    success_count = 0
    failed_chapters = []
    
    for chapter_num in range(3, 14):
        print(f"\n{'='*10} 处理第{chapter_num}品 {'='*10}")
        
        try:
            if process_chapter(chapter_num):
                success_count += 1
                print(f"✓ 第{chapter_num}品处理成功")
            else:
                failed_chapters.append(chapter_num)
                print(f"✗ 第{chapter_num}品处理失败")
        
        except KeyboardInterrupt:
            print(f"\n用户中断！已成功处理 {success_count} 品")
            break
        except Exception as e:
            print(f"✗ 第{chapter_num}品异常: {str(e)}")
            failed_chapters.append(chapter_num)
        
        # 处理间隔
        time.sleep(3)
    
    print(f"\n{'='*50}")
    print(f"处理完成！")
    print(f"成功: {success_count}/11 品")
    if failed_chapters:
        print(f"失败: {failed_chapters}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
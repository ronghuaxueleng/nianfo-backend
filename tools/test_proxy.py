#!/usr/bin/env python3
"""
测试代理连接
"""
import requests
import time

# 代理配置
PROXY_CONFIG = {
    'http': 'http://192.168.10.11:1080',
    'https': 'http://192.168.10.11:1080'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def test_proxy():
    """测试代理连接"""
    test_urls = [
        'http://httpbin.org/ip',
        'https://www.baidu.com',
        'http://www.fomen123.com'
    ]
    
    for url in test_urls:
        try:
            print(f"测试 {url}...")
            response = requests.get(
                url, 
                proxies=PROXY_CONFIG, 
                headers=HEADERS, 
                timeout=10,
                verify=False
            )
            print(f"✓ 成功: {response.status_code}")
            if 'httpbin' in url:
                print(f"  IP信息: {response.text[:200]}")
        except Exception as e:
            print(f"✗ 失败: {str(e)}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_proxy()
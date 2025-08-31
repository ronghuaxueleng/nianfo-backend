#!/usr/bin/env python3
"""
地藏经快速设置脚本
一键启动后台管理系统进行内容填充
"""
import sys
import os
import subprocess
import webbrowser
import time

def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    try:
        import flask
        import pypinyin
        print("✓ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_backend_server():
    """启动后台服务器"""
    print("启动后台服务器...")
    
    # 检查端口是否被占用
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('0.0.0.0', 5566))
    sock.close()
    
    if result == 0:
        print("端口5566已被占用，请先关闭其他服务或修改端口")
        return False
    
    try:
        # 启动Flask应用
        subprocess.Popen([sys.executable, 'run.py'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("✓ 后台服务器已启动 (http://localhost:5566)")
        return True
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        return False

def open_management_page():
    """打开后台管理页面"""
    print("等待服务器启动...")
    time.sleep(3)
    
    try:
        # 打开浏览器到后台管理页面
        management_url = "http://localhost:5566/sutra/37/chapters"
        webbrowser.open(management_url)
        print(f"✓ 已打开管理页面: {management_url}")
        return True
    except Exception as e:
        print(f"✗ 打开页面失败: {e}")
        print("请手动访问: http://localhost:5566/sutra/37/chapters")
        return False

def show_instructions():
    """显示操作说明"""
    print("\n" + "=" * 60)
    print("地藏经内容填充操作指南")
    print("=" * 60)
    
    instructions = [
        "1. 后台服务已启动，管理页面已打开",
        "2. 在页面中点击需要编辑的品（第3-13品）",
        "3. 从合法来源（如CBETA）复制经文内容",
        "4. 在编辑页面的“内容”字段中粘贴",
        "5. 注音字段可留空，系统会自动生成",
        "6. 点击保存完成该品的填充",
        "7. 重复以上步骤完成所有品的内容",
        "",
        "推荐内容来源：",
        "- CBETA中华电子佛典协会: http://www.cbeta.org/",
        "- 佛门网: http://www.fomen123.com/",
        "",
        "按 Ctrl+C 停止后台服务"
    ]
    
    for instruction in instructions:
        print(instruction)
    
    print("=" * 60)

def main():
    """主函数"""
    print("地藏经快速设置工具")
    print("自动启动后台管理系统进行内容填充")
    print()
    
    # 检查当前目录
    if not os.path.exists('run.py'):
        print("错误：请在backend目录下运行此脚本")
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 启动后台服务
    if not start_backend_server():
        return
    
    # 打开管理页面
    open_management_page()
    
    # 显示操作说明
    show_instructions()
    
    try:
        # 保持脚本运行
        print("\n服务器运行中... (按 Ctrl+C 停止)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n正在停止服务器...")
        print("服务已停止")

if __name__ == "__main__":
    main()
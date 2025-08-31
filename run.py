#!/usr/bin/env python3
"""
修行记录后台管理系统启动脚本
"""

import os
import sys

from app import create_app


def print_config_info(app):
    """打印配置信息"""
    print("📋 当前配置信息:")
    print(f"   环境: {app.config.get('ENV', 'unknown')}")
    print(f"   调试模式: {app.config.get('DEBUG', False)}")
    print(f"   数据库: {_mask_db_url(app.config.get('SQLALCHEMY_DATABASE_URI', ''))}")
    print(f"   连接池: {'已启用' if app.config.get('SQLALCHEMY_ENGINE_OPTIONS') else '未启用'}")
    print(f"   CORS: {app.config.get('CORS_ORIGINS', [])}")

def _mask_db_url(url):
    """隐藏数据库URL中的密码"""
    if url and '://' in url:
        parts = url.split('://')
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            if '@' in rest:
                auth_part, host_part = rest.split('@', 1)
                if ':' in auth_part:
                    user, _ = auth_part.split(':', 1)
                    return f"{protocol}://{user}:***@{host_part}"
    return url

def main():
    """主函数"""
    try:
        # 设置环境
        config_name = os.environ.get('FLASK_ENV', 'development')
        
        # 创建应用
        app = create_app(config_name)
        
        # 初始化数据库
        with app.app_context():
            from database import db
            from models import AdminUser, DedicationTemplate, SyncConfig
            
            # 创建表
            db.create_all()
            print("数据库表创建完成")
            
            # 创建默认管理员账户
            if not AdminUser.query.filter_by(username='admin').first():
                admin = AdminUser(
                    username='admin',
                    email='admin@xiuxing.com'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("创建默认管理员账户: admin / admin123")
            
            # 创建内置回向文模板
            DedicationTemplate.create_built_in_templates()
            print("内置回向文模板初始化完成")
            
            # 初始化同步配置
            SyncConfig.init_default_configs()
            print("同步配置初始化完成")
        
        # 打印配置信息
        print_config_info(app)
        
        # 启动应用
        host = app.config.get('HOST', '0.0.0.0')
        port = app.config.get('PORT', 5566)
        debug = app.config.get('DEBUG', False)
        
        print(f"\n🙏 修行记录后台管理系统")
        print(f"🔗 访问地址: http://localhost:{port}")
        print(f"👤 管理员: admin / admin123")
        print(f"📱 API接口: http://localhost:{port}/api")
        print(f"💊 健康检查: http://localhost:{port}/system/health")
        print(f"📊 连接池监控: http://localhost:{port}/system/db-pool")
        print(f"\n南无阿弥陀佛 🙏\n")
        
        app.run(host=host, port=port, debug=debug)
    
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
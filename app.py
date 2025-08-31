from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from database import db
import os

# 初始化扩展
login_manager = LoginManager()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # 加载配置
    from config import get_config
    config_instance = get_config(config_name)
    
    # 将配置实例的属性应用到Flask应用
    for key, value in config_instance.__dict__.items():
        if key.isupper() or key in ['HOST', 'PORT', 'DEBUG', 'ENV']:
            app.config[key] = value
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 配置CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # 初始化数据库监控
    from utils.db_monitor import init_db_monitoring
    init_db_monitoring(app)
    
    # 导入所有模型确保它们被注册到SQLAlchemy
    from models import User, AdminUser, Chanting, Dedication, ChantingRecord, DailyStats, DedicationTemplate, SyncRecord, SyncConfig
    
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.chanting import chanting_bp
    from routes.buddha_nam import buddha_nam_bp
    from routes.sutra import sutra_bp
    from routes.dedication import dedication_bp
    from routes.records import records_bp
    from routes.stats import stats_bp
    from routes.api import api_bp
    from routes.system import system_bp
    from routes.sync import sync_bp
    from routes.users import users_bp
    from routes.sync_management import sync_management_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(chanting_bp, url_prefix='/chanting')
    app.register_blueprint(buddha_nam_bp, url_prefix='/buddha-nam')
    app.register_blueprint(sutra_bp, url_prefix='/sutra')
    app.register_blueprint(dedication_bp, url_prefix='/dedication')
    app.register_blueprint(records_bp, url_prefix='/records')
    app.register_blueprint(stats_bp, url_prefix='/stats')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(sync_bp, url_prefix='/sync')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(sync_management_bp)
    
    # 全局模板变量
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    # 添加模板过滤器
    @app.template_filter('tojsonpretty')
    def to_json_pretty(value):
        try:
            import json
            if isinstance(value, str):
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            else:
                return json.dumps(value, indent=2, ensure_ascii=False)
        except:
            return str(value)
    
    # 错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        # 如果是API请求，返回JSON格式错误
        if request.path.startswith('/api/') or request.path.startswith('/sync/'):
            return {
                'error': 'Not Found',
                'message': 'The requested resource was not found on this server.',
                'status_code': 404,
                'path': request.path
            }, 404
        # 其他请求返回HTML页面
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        # 如果是API请求，返回JSON格式错误
        if request.path.startswith('/api/') or request.path.startswith('/sync/'):
            return {
                'error': 'Internal Server Error',
                'message': 'An internal server error occurred.',
                'status_code': 500,
                'path': request.path
            }, 500
        # 其他请求返回HTML页面
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员账户
        from models.user import AdminUser
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(
                username='admin',
                email='admin@xiuxing.com'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("创建默认管理员账户: admin / admin123")
        
        # 创建内置数据
        from models.chanting import Chanting
        from models.dedication_template import DedicationTemplate
        Chanting.create_built_in_chantings()
        DedicationTemplate.create_built_in_templates()
        print("初始化内置数据完成")
    
    app.run(debug=True, host='0.0.0.0', port=5566)
import os
import logging
from datetime import timedelta
from utils.config_loader import config_loader

# 配置日志
def setup_logging():
    """设置日志配置"""
    log_config = config_loader.get_logging_config()
    
    # 创建logs目录
    log_file = log_config.get('file', 'logs/app.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

class Config:
    """基础配置类"""
    
    def __init__(self):
        # 设置日志
        setup_logging()
        
        # 应用配置
        app_config = config_loader.get_app_config()
        self.SECRET_KEY = os.environ.get('SECRET_KEY') or app_config.get('secret_key', 'dev-secret-key')
        
        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or config_loader.build_database_url()
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = config_loader.get_engine_options()
        
        # JWT配置
        jwt_config = config_loader.get_jwt_config()
        self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or jwt_config.get('secret_key', 'jwt-secret-key')
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=jwt_config.get('access_token_expires_days', 30))
        
        # 会话配置
        self.PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
        
        # 文件上传配置
        upload_config = config_loader.get_upload_config()
        self.MAX_CONTENT_LENGTH = upload_config.get('max_file_size', 16 * 1024 * 1024)
        self.UPLOAD_FOLDER = upload_config.get('upload_folder', 'uploads')
        
        # CORS配置
        cors_config = config_loader.get_cors_config()
        self.CORS_ORIGINS = cors_config.get('origins', ['*'])
        
        # 分页配置
        self.POSTS_PER_PAGE = 20
        
        # 应用运行配置
        self.HOST = app_config.get('host', '0.0.0.0')
        self.PORT = app_config.get('port', 5566)
        self.DEBUG = app_config.get('debug', False)
        
        # 开发模式配置
        dev_config = config_loader.get_development_config()
        if dev_config.get('enabled', False):
            self.DEBUG = True
            self.ENV = 'development'
        else:
            self.ENV = 'production'
    
    def to_dict(self):
        """转换为字典格式，用于调试"""
        return {
            'SECRET_KEY': '***' if self.SECRET_KEY else None,
            'SQLALCHEMY_DATABASE_URI': self._mask_database_url(self.SQLALCHEMY_DATABASE_URI),
            'SQLALCHEMY_ENGINE_OPTIONS': self.SQLALCHEMY_ENGINE_OPTIONS,
            'JWT_SECRET_KEY': '***' if self.JWT_SECRET_KEY else None,
            'HOST': self.HOST,
            'PORT': self.PORT,
            'DEBUG': self.DEBUG,
            'ENV': self.ENV,
            'MAX_CONTENT_LENGTH': self.MAX_CONTENT_LENGTH,
            'UPLOAD_FOLDER': self.UPLOAD_FOLDER,
            'CORS_ORIGINS': self.CORS_ORIGINS
        }
    
    def _mask_database_url(self, url):
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

class DevelopmentConfig(Config):
    """开发环境配置"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.ENV = 'development'
        
        # 开发环境特定配置
        dev_config = config_loader.get_development_config()
        if dev_config.get('enabled', True):
            # 强制开启调试模式
            self.DEBUG = True
            
            # 如果配置的是SQLite，移除连接池配置
            db_config = config_loader.get_database_config()
            if db_config.get('type') == 'sqlite':
                self.SQLALCHEMY_ENGINE_OPTIONS = {}

class ProductionConfig(Config):
    """生产环境配置"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.ENV = 'production'
        
class TestingConfig(Config):
    """测试环境配置"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = True
        self.ENV = 'testing'
        
        # 测试环境使用内存数据库
        self.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        self.SQLALCHEMY_ENGINE_OPTIONS = {}

def get_config(config_name=None):
    """获取配置实例"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    return config_class()

# 向后兼容
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
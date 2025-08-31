import json
import base64
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """配置文件加载器"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = config_path
        self._config = None
        self._decoded = False  # 标记是否已经解码过
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config = self._get_default_config()
                self.save_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
        
        # 重置解码标记
        self._decoded = False
        return self._config
    
    def save_default_config(self):
        """保存默认配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"默认配置文件已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存默认配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "database": {
                "type": "sqlite",
                "sqlite": {
                    "path": "data/xiuxing.db"
                },
                "mysql": {
                    "host": "localhost",
                    "port": "3306",
                    "user": "root",
                    "password": "password",
                    "password_encoded": False,
                    "database": "xiuxing_db",
                    "charset": "utf8mb4"
                },
                "pool": {
                    "pool_size": 10,
                    "max_overflow": 20,
                    "pool_timeout": 30,
                    "pool_recycle": 3600,
                    "pool_pre_ping": True
                }
            },
            "app": {
                "host": "0.0.0.0",
                "port": 5566,
                "debug": True,
                "secret_key": "dev-secret-key-change-in-production"
            },
            "development": {
                "enabled": True,
                "auto_reload": True,
                "watch_directories": ["models", "routes", "templates", "static", "utils"],
                "ignore_patterns": ["*.pyc", "*.log", "*.tmp", "__pycache__/*", "logs/*", "data/*"]
            },
            "upload": {
                "max_file_size": 16777216,  # 16MB
                "allowed_extensions": ["txt", "json", "csv"],
                "upload_folder": "uploads"
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log"
            },
            "jwt": {
                "secret_key": "jwt-secret-key-change-in-production",
                "access_token_expires_days": 30
            },
            "cors": {
                "origins": ["*"]
            }
        }
    
    def _decode_base64(self, encoded_str: str) -> str:
        """Base64解码"""
        try:
            # 清理输入字符串
            encoded_str = str(encoded_str).strip()
            
            # 添加必要的填充
            missing_padding = len(encoded_str) % 4
            if missing_padding:
                encoded_str += '=' * (4 - missing_padding)
            
            # Base64解码
            decoded_bytes = base64.b64decode(encoded_str)
            decoded = decoded_bytes.decode('utf-8')
            
            # 只移除首尾空白字符，保留所有有效字符包括@符号
            decoded = decoded.strip()
            
            logger.debug(f"Base64解码成功: {encoded_str[:10]}... -> {decoded}")
            return decoded
            
        except Exception as e:
            logger.error(f"Base64解码失败 [{encoded_str[:20]}]: {e}")
            return encoded_str
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        db_config = self._config.get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'mysql' and not self._decoded:
            mysql_config = db_config.get('mysql', {})
            
            # 检查是否启用了Base64编码
            is_encoded = mysql_config.get('password_encoded', False)
            
            if is_encoded:
                logger.info("开始解码Base64配置...")
                
                # 只有当password_encoded为True时才解码所有字段
                # 解码密码
                if 'password' in mysql_config:
                    original = mysql_config['password']
                    decoded = self._decode_base64(original)
                    mysql_config['password'] = decoded
                    logger.debug(f"密码解码完成")
                
                # 解码其他字段
                for field in ['host', 'user', 'database']:
                    if field in mysql_config:
                        original_value = mysql_config[field]
                        decoded = self._decode_base64(str(original_value))
                        mysql_config[field] = decoded
                        logger.debug(f"{field}解码: {original_value} -> {decoded}")
                
                # 端口解码
                if 'port' in mysql_config:
                    original_port = mysql_config['port']
                    try:
                        port_decoded = self._decode_base64(str(original_port))
                        mysql_config['port'] = int(port_decoded)
                        logger.debug(f"端口解码: {original_port} -> {port_decoded}")
                    except:
                        # 如果解码失败，尝试直接转换为int
                        try:
                            mysql_config['port'] = int(original_port)
                        except:
                            mysql_config['port'] = 3306  # 默认端口
                
                # 标记已解码
                self._decoded = True
                logger.info("Base64配置解码完成")
                
            else:
                # 如果password_encoded为False，确保端口是int类型
                if 'port' in mysql_config:
                    try:
                        mysql_config['port'] = int(mysql_config['port'])
                    except:
                        mysql_config['port'] = 3306
        
        return db_config
    
    def get_app_config(self) -> Dict[str, Any]:
        """获取应用配置"""
        return self._config.get('app', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """获取开发配置"""
        return self._config.get('development', {})
    
    def get_upload_config(self) -> Dict[str, Any]:
        """获取上传配置"""
        return self._config.get('upload', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._config.get('logging', {})
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """获取JWT配置"""
        return self._config.get('jwt', {})
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置"""
        return self._config.get('cors', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def build_database_url(self) -> str:
        """构建数据库连接URL"""
        db_config = self.get_database_config()
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            sqlite_config = db_config.get('sqlite', {})
            db_path = sqlite_config.get('path', 'data/xiuxing.db')
            
            # 确保目录存在
            dir_path = os.path.dirname(db_path)
            if dir_path:  # 只有当有目录时才创建
                os.makedirs(dir_path, exist_ok=True)
            
            return f'sqlite:///{db_path}'
        
        elif db_type == 'mysql':
            mysql_config = db_config.get('mysql', {})
            host = str(mysql_config.get('host', 'localhost')).strip()
            port = mysql_config.get('port', 3306)
            user = str(mysql_config.get('user', 'root')).strip()
            password = str(mysql_config.get('password', '')).strip()
            database = str(mysql_config.get('database', 'xiuxing_db')).strip()
            charset = mysql_config.get('charset', 'utf8mb4')
            
            # URL编码特殊字符（只编码用户名和密码）
            from urllib.parse import quote_plus
            encoded_user = quote_plus(user)
            encoded_password = quote_plus(password)
            
            return f'mysql+pymysql://{encoded_user}:{encoded_password}@{host}:{port}/{database}?charset={charset}'
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def get_engine_options(self) -> Dict[str, Any]:
        """获取数据库引擎选项"""
        db_config = self.get_database_config()
        db_type = db_config.get('type', 'sqlite')
        pool_config = db_config.get('pool', {})
        
        if db_type == 'sqlite':
            # SQLite不支持连接池
            return {}
        
        elif db_type == 'mysql':
            return {
                'pool_size': pool_config.get('pool_size', 10),
                'max_overflow': pool_config.get('max_overflow', 20),
                'pool_timeout': pool_config.get('pool_timeout', 30),
                'pool_recycle': pool_config.get('pool_recycle', 3600),
                'pool_pre_ping': pool_config.get('pool_pre_ping', True),
                'pool_reset_on_return': 'commit',
                'connect_args': {
                    'charset': db_config.get('mysql', {}).get('charset', 'utf8mb4'),
                    'autocommit': True,
                    'connect_timeout': 60,
                    'read_timeout': 30,
                    'write_timeout': 30,
                }
            }
        
        return {}

# 全局配置实例
config_loader = ConfigLoader()
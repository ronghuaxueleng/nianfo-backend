from datetime import datetime
from database import db

class SyncConfig(db.Model):
    """同步配置模型 - 控制数据同步的规则和权限"""
    __tablename__ = 'sync_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)  # 配置键
    config_value = db.Column(db.Text, nullable=False)  # 配置值（JSON格式）
    description = db.Column(db.String(255), nullable=True)  # 配置说明
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_config(key, default=None):
        """获取配置值"""
        config = SyncConfig.query.filter_by(config_key=key, is_active=True).first()
        if config:
            import json
            try:
                return json.loads(config.config_value)
            except:
                return config.config_value
        return default
    
    @staticmethod
    def set_config(key, value, description=None):
        """设置配置值"""
        import json
        config = SyncConfig.query.filter_by(config_key=key).first()
        
        # 如果是字典或列表，转换为JSON字符串
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        if config:
            config.config_value = value_str
            config.updated_at = datetime.utcnow()
            if description:
                config.description = description
        else:
            config = SyncConfig(
                config_key=key,
                config_value=value_str,
                description=description
            )
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def init_default_configs():
        """初始化默认配置"""
        default_configs = [
            {
                'key': 'app_data_overwrite_policy',
                'value': {
                    'users': True,  # App数据可以覆盖后端用户数据
                    'chantings': False,  # App数据不能覆盖后端佛号经文数据（内置保护）
                    'dedication_templates': False,  # App数据不能覆盖后端回向模板数据
                    'chanting_records': True,  # App数据可以覆盖后端修行记录
                    'daily_stats': True,  # App数据可以覆盖后端统计数据
                    'dedications': True  # App数据可以覆盖后端回向记录
                },
                'description': 'App端数据是否可以覆盖后端数据的策略配置'
            },
            {
                'key': 'sync_allowed_data_types',
                'value': ['users', 'chantings', 'dedication_templates', 'chanting_records', 'daily_stats', 'dedications'],
                'description': '允许同步的数据类型列表'
            },
            {
                'key': 'sync_batch_size',
                'value': 100,
                'description': '批量同步的数据条数限制'
            },
            {
                'key': 'sync_rate_limit',
                'value': {
                    'max_requests_per_hour': 60,
                    'max_requests_per_day': 500
                },
                'description': '同步接口的频率限制'
            },
            {
                'key': 'first_sync_auto_create_user',
                'value': True,
                'description': '首次同步时是否自动创建用户'
            },
            {
                'key': 'built_in_content_protection',
                'value': {
                    'strict_mode': True,  # 严格模式：app完全不能修改内置内容
                    'protected_fields': ['title', 'content', 'pronunciation', 'type', 'is_built_in'],
                    'admin_only_operations': ['create_built_in', 'update_built_in', 'delete_built_in'],
                    'allow_user_content_only': True  # 只允许用户创建非内置内容
                },
                'description': '内置内容保护策略，确保app无法修改删除内置佛号经文和模板'
            }
        ]
        
        for config_data in default_configs:
            existing = SyncConfig.query.filter_by(config_key=config_data['key']).first()
            if not existing:
                SyncConfig.set_config(
                    config_data['key'], 
                    config_data['value'], 
                    config_data['description']
                )
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from utils.db_monitor import DatabaseMonitor
from utils.config_loader import config_loader
from database import db
import psutil
import os
from datetime import datetime

system_bp = Blueprint('system', __name__)

@system_bp.route('/health')
def health_check():
    """系统健康检查"""
    db_health = DatabaseMonitor.check_health()
    pool_status = DatabaseMonitor.get_pool_status()
    
    return jsonify({
        'status': 'healthy' if db_health else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': {
            'connected': db_health,
            'pool': pool_status
        },
        'system': {
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(),
            'disk_usage': psutil.disk_usage('/').percent
        }
    })

@system_bp.route('/db-pool')
@login_required
def db_pool_status():
    """数据库连接池状态（需要登录）"""
    pool_status = DatabaseMonitor.get_pool_status()
    
    if pool_status is None:
        return jsonify({'error': '无法获取连接池状态'}), 500
    
    return jsonify({
        'pool_status': pool_status,
        'engine_info': {
            'name': db.engine.name,
            'driver': db.engine.driver,
            'url': str(db.engine.url).replace(db.engine.url.password or '', '***')
        },
        'timestamp': datetime.utcnow().isoformat()
    })

@system_bp.route('/db-pool/reset', methods=['POST'])
@login_required
def reset_db_pool():
    """重置数据库连接池（需要登录）"""
    try:
        DatabaseMonitor.cleanup_connections()
        return jsonify({
            'status': 'success',
            'message': '连接池已重置',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'重置连接池失败: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@system_bp.route('/config')
@login_required
def get_config_info():
    """获取配置信息（需要登录）"""
    try:
        # 获取数据库配置（隐藏敏感信息）
        db_config = config_loader.get_database_config()
        if 'mysql' in db_config and 'password' in db_config['mysql']:
            db_config['mysql']['password'] = '***'
        
        config_info = {
            'database': db_config,
            'app': config_loader.get_app_config(),
            'development': config_loader.get_development_config(),
            'upload': config_loader.get_upload_config(),
            'logging': config_loader.get_logging_config(),
            'jwt': {
                **config_loader.get_jwt_config(),
                'secret_key': '***'  # 隐藏JWT密钥
            },
            'cors': config_loader.get_cors_config(),
            'flask_config': {
                'ENV': current_app.config.get('ENV'),
                'DEBUG': current_app.config.get('DEBUG'),
                'HOST': current_app.config.get('HOST'),
                'PORT': current_app.config.get('PORT'),
                'MAX_CONTENT_LENGTH': current_app.config.get('MAX_CONTENT_LENGTH'),
                'UPLOAD_FOLDER': current_app.config.get('UPLOAD_FOLDER')
            }
        }
        
        return jsonify({
            'status': 'success',
            'config': config_info,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取配置信息失败: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@system_bp.route('/config/reload', methods=['POST'])
@login_required
def reload_config():
    """重新加载配置文件（需要登录）"""
    try:
        config_loader.load_config()
        return jsonify({
            'status': 'success',
            'message': '配置文件已重新加载',
            'timestamp': datetime.utcnow().isoformat(),
            'note': '某些配置需要重启应用才能生效'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'重新加载配置失败: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500
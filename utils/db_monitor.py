from sqlalchemy import text
from database import db
import logging

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """数据库连接池监控和健康检查"""
    
    @staticmethod
    def check_health():
        """检查数据库连接健康状态"""
        try:
            # 简单查询测试连接
            result = db.session.execute(text('SELECT 1'))
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
    
    @staticmethod
    def get_pool_status():
        """获取连接池状态信息"""
        try:
            engine = db.engine
            pool = engine.pool
            
            # 构建基本状态信息
            status = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow()
            }
            
            # 尝试获取invalid状态，如果方法不存在则跳过
            try:
                status['invalid'] = pool.invalid()
            except AttributeError:
                # 较新版本的SQLAlchemy可能没有invalid()方法
                status['invalid'] = 'N/A'
            
            return status
        except Exception as e:
            logger.error(f"获取连接池状态失败: {e}")
            return None
    
    @staticmethod
    def log_pool_status():
        """记录连接池状态到日志"""
        status = DatabaseMonitor.get_pool_status()
        if status:
            logger.info(f"连接池状态: {status}")
        
    @staticmethod
    def cleanup_connections():
        """清理无效连接"""
        try:
            db.engine.dispose()
            logger.info("连接池已重置")
        except Exception as e:
            logger.error(f"清理连接池失败: {e}")

def init_db_monitoring(app):
    """初始化数据库监控"""
    
    @app.before_request
    def before_request():
        """请求前检查数据库连接"""
        if not DatabaseMonitor.check_health():
            logger.warning("数据库连接异常，尝试重新连接")
            DatabaseMonitor.cleanup_connections()
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        try:
            db.session.remove()
        except Exception as e:
            logger.error(f"清理session失败: {e}")
        return response
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """应用上下文结束时清理session"""
        try:
            db.session.remove()
        except Exception as e:
            logger.error(f"teardown session失败: {e}")
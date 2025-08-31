"""
日期时间工具函数
统一处理应用中的时间相关操作
"""
from datetime import datetime, timedelta

def now():
    """获取当前本地时间"""
    return datetime.now()

def utc_now():
    """获取当前UTC时间（保持原有接口兼容性）"""
    return datetime.utcnow()

def to_local_time(utc_datetime):
    """将UTC时间转换为本地时间（简单的+8小时处理）"""
    if utc_datetime is None:
        return None
    
    # 简单的时区转换：UTC+8 (中国标准时间)
    return utc_datetime + timedelta(hours=8)

def to_utc_time(local_datetime):
    """将本地时间转换为UTC时间（简单的-8小时处理）"""
    if local_datetime is None:
        return None
        
    # 简单的时区转换：本地时间-8小时 = UTC
    return local_datetime - timedelta(hours=8)
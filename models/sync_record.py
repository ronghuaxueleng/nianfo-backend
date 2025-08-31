from datetime import datetime
from database import db

class SyncRecord(db.Model):
    """同步记录模型 - 记录用户的同步历史"""
    __tablename__ = 'sync_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.String(100), nullable=False)  # 设备标识
    sync_type = db.Column(db.Enum('full', 'incremental'), nullable=False, default='incremental')  # 同步类型：全量/增量
    sync_direction = db.Column(db.Enum('upload', 'download', 'bidirectional'), nullable=False)  # 同步方向
    sync_status = db.Column(db.Enum('success', 'failed', 'partial'), nullable=False, default='success')  # 同步状态
    sync_data_types = db.Column(db.Text)  # JSON格式，记录同步的数据类型
    error_message = db.Column(db.Text, nullable=True)  # 错误信息
    sync_started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 同步开始时间
    sync_completed_at = db.Column(db.DateTime, nullable=True)  # 同步完成时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联用户
    user = db.relationship('User', backref=db.backref('sync_records', lazy=True))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'sync_type': self.sync_type,
            'sync_direction': self.sync_direction,
            'sync_status': self.sync_status,
            'sync_data_types': self.sync_data_types,
            'error_message': self.error_message,
            'sync_started_at': self.sync_started_at.isoformat() if self.sync_started_at else None,
            'sync_completed_at': self.sync_completed_at.isoformat() if self.sync_completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_first_sync(self):
        """判断是否为首次同步"""
        previous_sync = SyncRecord.query.filter(
            SyncRecord.user_id == self.user_id,
            SyncRecord.device_id == self.device_id,
            SyncRecord.id < self.id,
            SyncRecord.sync_status == 'success'
        ).first()
        return previous_sync is None
    
    @staticmethod
    def get_last_sync_time(user_id, device_id=None):
        """获取最后同步时间"""
        query = SyncRecord.query.filter(
            SyncRecord.user_id == user_id,
            SyncRecord.sync_status == 'success'
        )
        if device_id:
            query = query.filter(SyncRecord.device_id == device_id)
        
        last_sync = query.order_by(SyncRecord.sync_completed_at.desc()).first()
        return last_sync.sync_completed_at if last_sync else None
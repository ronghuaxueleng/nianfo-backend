from datetime import datetime
from database import db

class Dedication(db.Model):
    """回向文模型 - 对应Flutter应用的Dedication"""
    __tablename__ = 'dedications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    chanting_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)  # 可选，如果需要用户关联
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'chanting_id': self.chanting_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
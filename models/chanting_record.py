from datetime import datetime
from database import db

class ChantingRecord(db.Model):
    """修行记录模型 - 对应Flutter应用的ChantingRecord"""
    __tablename__ = 'chanting_records'
    
    id = db.Column(db.Integer, primary_key=True)
    chanting_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # 可选，如果需要用户关联
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'chanting_id': self.chanting_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_chanting(self):
        """包含佛号经文详情的字典格式"""
        from models.chanting import Chanting
        data = self.to_dict()
        if self.chanting_id:
            chanting = Chanting.query.get(self.chanting_id)
            if chanting:
                data['chanting'] = chanting.to_dict()
        return data
    
    def to_dict_with_user_and_chanting(self):
        """包含用户和佛号经文详情的字典格式"""
        from models.chanting import Chanting
        from models.user import User
        data = self.to_dict()
        if self.chanting_id:
            chanting = Chanting.query.get(self.chanting_id)
            if chanting:
                data['chanting'] = chanting.to_dict()
        if self.user_id:
            user = User.query.get(self.user_id)
            if user:
                data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'avatar_type': user.avatar_type
                }
        return data
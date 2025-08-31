from datetime import datetime
from database import db

class Chapter(db.Model):
    """经文章节模型"""
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    chanting_id = db.Column(db.Integer, nullable=False)  # 所属经文ID
    chapter_number = db.Column(db.Integer, nullable=False)  # 章节序号
    title = db.Column(db.String(200), nullable=False)  # 章节标题
    content = db.Column(db.Text, nullable=False)  # 章节内容
    pronunciation = db.Column(db.Text, nullable=True)  # 注音
    is_deleted = db.Column(db.Boolean, default=False)  # 逻辑删除
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'chanting_id': self.chanting_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'content': self.content,
            'pronunciation': self.pronunciation,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active(cls):
        """获取未删除的记录"""
        return cls.query.filter_by(is_deleted=False)
    
    @classmethod
    def get_by_chanting(cls, chanting_id):
        """获取某个经文的所有章节"""
        return cls.get_active().filter_by(chanting_id=chanting_id).order_by(cls.chapter_number)
    
    def soft_delete(self):
        """逻辑删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict_with_chanting(self):
        """包含经文详情的字典格式"""
        from models.chanting import Chanting
        data = self.to_dict()
        if self.chanting_id:
            chanting = Chanting.query.get(self.chanting_id)
            if chanting:
                data['chanting'] = chanting.to_dict()
        return data
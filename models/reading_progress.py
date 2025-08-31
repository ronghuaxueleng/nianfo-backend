from datetime import datetime
from database import db

class ReadingProgress(db.Model):
    """阅读进度模型"""
    __tablename__ = 'reading_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # 用户ID
    chanting_id = db.Column(db.Integer, nullable=False)  # 经文ID
    chapter_id = db.Column(db.Integer, nullable=True)  # 章节ID，空表示整部经文
    is_completed = db.Column(db.Boolean, default=False)  # 是否完成
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)  # 最后阅读时间
    reading_position = db.Column(db.Integer, default=0)  # 阅读位置（如字符位置）
    notes = db.Column(db.Text, nullable=True)  # 阅读笔记
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建唯一约束：每个用户对每个章节只能有一条进度记录
    __table_args__ = (
        db.UniqueConstraint('user_id', 'chanting_id', 'chapter_id', name='unique_user_progress'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chanting_id': self.chanting_id,
            'chapter_id': self.chapter_id,
            'is_completed': self.is_completed,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
            'reading_position': self.reading_position,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_details(self):
        """包含经文和章节详情的字典格式"""
        from models.chanting import Chanting
        from models.chapter import Chapter
        from models.user import User
        
        data = self.to_dict()
        
        # 添加经文信息
        if self.chanting_id:
            chanting = Chanting.query.get(self.chanting_id)
            if chanting:
                data['chanting'] = chanting.to_dict()
        
        # 添加章节信息
        if self.chapter_id:
            chapter = Chapter.query.get(self.chapter_id)
            if chapter:
                data['chapter'] = chapter.to_dict()
        
        # 添加用户信息
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
    
    @classmethod
    def get_user_progress(cls, user_id, chanting_id=None):
        """获取用户的阅读进度"""
        query = cls.query.filter_by(user_id=user_id)
        if chanting_id:
            query = query.filter_by(chanting_id=chanting_id)
        return query.order_by(cls.last_read_at.desc())
    
    @classmethod
    def get_or_create_progress(cls, user_id, chanting_id, chapter_id=None):
        """获取或创建进度记录"""
        progress = cls.query.filter_by(
            user_id=user_id,
            chanting_id=chanting_id,
            chapter_id=chapter_id
        ).first()
        
        if not progress:
            progress = cls(
                user_id=user_id,
                chanting_id=chanting_id,
                chapter_id=chapter_id
            )
            db.session.add(progress)
            db.session.commit()
        
        return progress
    
    def update_progress(self, is_completed=None, reading_position=None, notes=None):
        """更新阅读进度"""
        if is_completed is not None:
            self.is_completed = is_completed
        if reading_position is not None:
            self.reading_position = reading_position
        if notes is not None:
            self.notes = notes
        
        self.last_read_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_chanting_progress_summary(self, user_id, chanting_id):
        """获取某部经文的整体进度摘要"""
        from models.chapter import Chapter
        
        # 获取经文的所有章节
        chapters = Chapter.get_by_chanting(chanting_id).all()
        total_chapters = len(chapters)
        
        if total_chapters == 0:
            return {'total_chapters': 0, 'completed_chapters': 0, 'progress_percentage': 0}
        
        # 获取已完成的章节数
        completed_count = self.query.filter_by(
            user_id=user_id,
            chanting_id=chanting_id,
            is_completed=True
        ).filter(self.chapter_id.isnot(None)).count()
        
        progress_percentage = (completed_count / total_chapters) * 100
        
        return {
            'total_chapters': total_chapters,
            'completed_chapters': completed_count,
            'progress_percentage': round(progress_percentage, 2)
        }
from datetime import datetime, date
from database import db

class DailyStats(db.Model):
    """每日统计模型 - 对应Flutter应用的DailyStats"""
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    chanting_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # 可选，如果需要用户关联
    count = db.Column(db.Integer, default=0, nullable=False)  # 念诵次数
    date = db.Column(db.Date, default=date.today, nullable=False)  # 统计日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建复合唯一索引，确保每个用户每天每个佛号经文只有一条统计记录
    __table_args__ = (
        db.UniqueConstraint('chanting_id', 'user_id', 'date', name='unique_daily_stats'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'chanting_id': self.chanting_id,
            'user_id': self.user_id,
            'count': self.count,
            'date': self.date.isoformat() if self.date else None,
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
    
    @classmethod
    def get_or_create_today(cls, chanting_id, user_id=None):
        """获取或创建今日统计记录"""
        today = date.today()
        stats = cls.query.filter_by(
            chanting_id=chanting_id,
            user_id=user_id,
            date=today
        ).first()
        
        if not stats:
            stats = cls(
                chanting_id=chanting_id,
                user_id=user_id,
                date=today,
                count=0
            )
            db.session.add(stats)
            db.session.commit()
        
        return stats
    
    @classmethod
    def increment_count(cls, chanting_id, user_id=None, increment=1):
        """增加念诵次数"""
        stats = cls.get_or_create_today(chanting_id, user_id)
        stats.count += increment
        stats.updated_at = datetime.utcnow()
        db.session.commit()
        return stats
    
    @classmethod
    def set_count(cls, chanting_id, count, user_id=None):
        """设置念诵次数"""
        stats = cls.get_or_create_today(chanting_id, user_id)
        stats.count = count
        stats.updated_at = datetime.utcnow()
        db.session.commit()
        return stats
    
    @classmethod
    def get_date_range_stats(cls, start_date, end_date, user_id=None):
        """获取日期范围内的统计"""
        query = cls.query.filter(
            cls.date >= start_date,
            cls.date <= end_date
        )
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.all()
    
    @classmethod
    def get_monthly_stats(cls, year, month, user_id=None):
        """获取月度统计"""
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        return cls.get_date_range_stats(start_date, end_date, user_id)
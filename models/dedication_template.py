from datetime import datetime
from database import db

class DedicationTemplate(db.Model):
    """回向文模板模型 - 对应Flutter应用的DedicationTemplate"""
    __tablename__ = 'dedication_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_built_in = db.Column(db.Boolean, default=False)  # 是否为内置模板
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_built_in': self.is_built_in,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_built_in_templates():
        """创建内置回向文模板"""
        built_in_templates = [
            {
                'title': '回向万界众生',
                'content': '愿以此功德，回向万界众生\n愿众生离苦得乐，究竟解脱',
                'is_built_in': True
            },
            {
                'title': '回向父母',
                'content': '愿以此功德，回向父母师长\n愿他们身体健康，福慧增长',
                'is_built_in': True
            },
            {
                'title': '回向冤亲债主',
                'content': '愿以此功德，回向冤亲债主\n愿他们离苦得乐，往生净土',
                'is_built_in': True
            },
            {
                'title': '回向自己',
                'content': '愿以此功德，回向给自己\n愿消除业障，增长智慧，早日成佛',
                'is_built_in': True
            }
        ]
        
        for template_data in built_in_templates:
            existing = DedicationTemplate.query.filter_by(
                title=template_data['title'], 
                is_built_in=True
            ).first()
            if not existing:
                template = DedicationTemplate(**template_data)
                db.session.add(template)
        
        db.session.commit()
from datetime import datetime
from database import db

class Chanting(db.Model):
    """佛号经文模型 - 对应Flutter应用的Chanting"""
    __tablename__ = 'chantings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    pronunciation = db.Column(db.Text, nullable=True)  # 注音
    type = db.Column(db.Enum('buddha', 'sutra'), nullable=False)  # 佛号或经文
    is_built_in = db.Column(db.Boolean, default=False)  # 是否为内置
    is_deleted = db.Column(db.Boolean, default=False)  # 逻辑删除
    user_id = db.Column(db.Integer, nullable=True)  # 创建者ID，内置内容为空
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'pronunciation': self.pronunciation,
            'type': self.type,
            'is_built_in': self.is_built_in,
            'is_deleted': self.is_deleted,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active(cls):
        """获取未删除的记录"""
        return cls.query.filter_by(is_deleted=False)
    
    @classmethod
    def get_by_type(cls, chanting_type):
        """按类型获取记录"""
        return cls.get_active().filter_by(type=chanting_type)
    
    def soft_delete(self):
        """逻辑删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_built_in_chantings():
        """创建内置佛号经文"""
        built_in_data = [
            {
                'title': '地藏菩萨本愿经（节选）',
                'content': '''南无本师释迦牟尼佛！
南无大愿地藏王菩萨！

尔时世尊举身放大光明，遍照百千万亿恒河沙等诸佛世界。出大音声，普告诸佛世界一切诸菩萨摩诃萨，及天龙八部、人非人等：听吾今日称扬赞叹地藏菩萨摩诃萨，于十方世界，现大不可思议威神慈悲之力，救护一切罪苦众生。

地藏！地藏！汝之神力不可思议，汝之慈悲不可思议，汝之智慧不可思议，汝之辩才不可思议！正使十方诸佛，赞叹宣说汝之不思议事，千万劫中，不能得尽。''',
                'pronunciation': '''nán wú běn shī shì jiā móu ní fó ！
nán wú dà yuàn dì zàng wáng pú sà ！

ěr shí shì zūn jǔ shēn fàng dà guāng míng ， biàn zhào bǎi qiān wàn yì héng hé shā děng zhū fó shì jiè 。 chū dà yīn shēng ， pǔ gào zhū fó shì jiè yī qiè zhū pú sà mó hē sà ， jí tiān lóng bā bù 、 rén fēi rén děng ： tīng wú jīn rì chēng yáng zàn tàn dì zàng pú sà mó hē sà ， yú shí fāng shì jiè ， xiàn dà bù kě sī yì wēi shén cí bēi zhī lì ， jiù hù yī qiè zuì kǔ zhòng shēng 。

dì zàng ！ dì zàng ！ rǔ zhī shén lì bù kě sī yì ， rǔ zhī cí bēi bù kě sī yì ， rǔ zhī zhì huì bù kě sī yì ， rǔ zhī biàn cái bù kě sī yì ！ zhèng shǐ shí fāng zhū fó ， zàn tàn xuān shuō rǔ zhī bù sī yì shì ， qiān wàn jié zhōng ， bù néng dé jìn 。''',
                'type': 'sutra',
                'is_built_in': True
            },
            {
                'title': '文殊菩萨心咒',
                'content': '嗡啊喇巴札那谛',
                'pronunciation': 'ōng ā rā bā zhā nà dì',
                'type': 'sutra',
                'is_built_in': True
            },
            {
                'title': '南无阿弥陀佛',
                'content': '南无阿弥陀佛',
                'pronunciation': 'nán wú ā mí tuó fó',
                'type': 'buddha',
                'is_built_in': True
            },
            {
                'title': '南无观世音菩萨',
                'content': '南无观世音菩萨',
                'pronunciation': 'nán wú guān shì yīn pú sà',
                'type': 'buddha',
                'is_built_in': True
            },
            {
                'title': '南无地藏王菩萨',
                'content': '南无地藏王菩萨',
                'pronunciation': 'nán wú dì zàng wáng pú sà',
                'type': 'buddha',
                'is_built_in': True
            }
        ]
        
        for data in built_in_data:
            existing = Chanting.query.filter_by(title=data['title'], is_built_in=True).first()
            if not existing:
                chanting = Chanting(**data)
                db.session.add(chanting)
        
        db.session.commit()
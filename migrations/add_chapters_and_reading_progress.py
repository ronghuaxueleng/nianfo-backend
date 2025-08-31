#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加章节表和阅读进度表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.chapter import Chapter
from models.reading_progress import ReadingProgress
from models.chanting import Chanting

def upgrade():
    """创建章节表和阅读进度表"""
    print("开始迁移：创建章节表和阅读进度表...")
    
    try:
        # 创建表格
        db.create_all()
        print("表格创建完成")
        
        # 为现有的经文创建示例章节
        create_sample_chapters()
        
        print("迁移完成")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        raise

def create_sample_chapters():
    """为现有经文创建示例章节"""
    print("为现有经文创建示例章节...")
    
    # 查找地藏菩萨本愿经，为其创建章节
    dizang_sutra = Chanting.query.filter_by(title='地藏菩萨本愿经（节选）', is_built_in=True).first()
    if dizang_sutra:
        print(f"为 {dizang_sutra.title} 创建章节...")
        
        chapters_data = [
            {
                'chapter_number': 1,
                'title': '序分',
                'content': '''南无本师释迦牟尼佛！
南无大愿地藏王菩萨！

尔时世尊举身放大光明，遍照百千万亿恒河沙等诸佛世界。出大音声，普告诸佛世界一切诸菩萨摩诃萨，及天龙八部、人非人等：听吾今日称扬赞叹地藏菩萨摩诃萨，于十方世界，现大不可思议威神慈悲之力，救护一切罪苦众生。''',
                'pronunciation': '''nán wú běn shī shì jiā móu ní fó ！
nán wú dà yuàn dì zàng wáng pú sà ！

ěr shí shì zūn jǔ shēn fàng dà guāng míng ， biàn zhào bǎi qiān wàn yì héng hé shā děng zhū fó shì jiè 。 chū dà yīn shēng ， pǔ gào zhū fó shì jiè yī qiè zhū pú sà mó hē sà ， jí tiān lóng bā bù 、 rén fēi rén děng ： tīng wú jīn rì chēng yáng zàn tàn dì zàng pú sà mó hē sà ， yú shí fāng shì jiè ， xiàn dà bù kě sī yì wēi shén cí bēi zhī lì ， jiù hù yī qiè zuì kǔ zhòng shēng 。'''
            },
            {
                'chapter_number': 2,
                'title': '赞叹地藏菩萨',
                'content': '''地藏！地藏！汝之神力不可思议，汝之慈悲不可思议，汝之智慧不可思议，汝之辩才不可思议！正使十方诸佛，赞叹宣说汝之不思议事，千万劫中，不能得尽。''',
                'pronunciation': '''dì zàng ！ dì zàng ！ rǔ zhī shén lì bù kě sī yì ， rǔ zhī cí bēi bù kě sī yì ， rǔ zhī zhì huì bù kě sī yì ， rǔ zhī biàn cái bù kě sī yì ！ zhèng shǐ shí fāng zhū fó ， zàn tàn xuān shuō rǔ zhī bù sī yì shì ， qiān wàn jié zhōng ， bù néng dé jìn 。'''
            }
        ]
        
        for chapter_data in chapters_data:
            existing_chapter = Chapter.query.filter_by(
                chanting_id=dizang_sutra.id,
                chapter_number=chapter_data['chapter_number']
            ).first()
            
            if not existing_chapter:
                chapter = Chapter(
                    chanting_id=dizang_sutra.id,
                    **chapter_data
                )
                db.session.add(chapter)
        
        # 更新原经文，标记其有章节
        if not hasattr(dizang_sutra, 'has_chapters'):
            # 这里我们可以通过content字段来标记，或者后续添加has_chapters字段
            pass
    
    # 为心咒类经文创建章节（如果需要的话）
    # 心咒通常比较短，可以不分章节
    
    db.session.commit()
    print("示例章节创建完成")

def downgrade():
    """删除章节表和阅读进度表"""
    print("开始回滚：删除章节表和阅读进度表...")
    
    try:
        # 删除表格
        ReadingProgress.__table__.drop(db.engine)
        Chapter.__table__.drop(db.engine)
        
        print("回滚完成")
        
    except Exception as e:
        print(f"回滚失败: {e}")
        raise

if __name__ == '__main__':
    from app import create_app
    
    app = create_app('development')
    with app.app_context():
        upgrade()
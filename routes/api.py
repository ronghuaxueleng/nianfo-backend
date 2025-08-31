from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import datetime, date
from database import db
from models.user import User
from models.chanting import Chanting
from models.dedication import Dedication
from models.chanting_record import ChantingRecord
from models.daily_stats import DailyStats
from models.dedication_template import DedicationTemplate
from models.chapter import Chapter
from models.reading_progress import ReadingProgress

api_bp = Blueprint('api', __name__)

# ================== 认证相关 ==================

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': '用户名或密码错误'}), 401

@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """API用户注册"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')
    avatar = data.get('avatar')
    avatar_type = data.get('avatar_type', 'emoji')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    user = User(
        username=username,
        nickname=nickname,
        avatar=avatar,
        avatar_type=avatar_type,
        created_at=datetime.utcnow()
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 201

@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户资料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify(user.to_dict())

@api_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户资料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'avatar_type' in data:
        user.avatar_type = data['avatar_type']
    
    db.session.commit()
    return jsonify(user.to_dict())

# ================== 佛号经文相关 ==================

@api_bp.route('/chantings', methods=['GET'])
@jwt_required()
def get_chantings():
    """获取佛号经文列表"""
    chanting_type = request.args.get('type')  # buddha 或 sutra
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Chanting.get_active()
    
    if chanting_type:
        query = query.filter_by(type=chanting_type)
    
    chantings = query.order_by(Chanting.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'chantings': [c.to_dict() for c in chantings.items],
        'total': chantings.total,
        'page': page,
        'per_page': per_page,
        'pages': chantings.pages
    })

@api_bp.route('/chantings/<int:chanting_id>', methods=['GET'])
@jwt_required()
def get_chanting(chanting_id):
    """获取单个佛号经文详情"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    return jsonify(chanting.to_dict())

@api_bp.route('/chantings', methods=['POST'])
@jwt_required()
def create_chanting():
    """创建佛号经文"""
    data = request.get_json()
    
    required_fields = ['title', 'content', 'type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field}不能为空'}), 400
    
    if data['type'] not in ['buddha', 'sutra']:
        return jsonify({'error': 'type必须是buddha或sutra'}), 400
    
    # 检查用户权限：admin用户添加的标记为内置，普通用户添加的标记为自定义
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    is_built_in = user.username == 'admin' if user else False
    
    chanting = Chanting(
        title=data['title'],
        content=data['content'],
        pronunciation=data.get('pronunciation'),
        type=data['type'],
        is_built_in=is_built_in,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(chanting)
    db.session.commit()
    
    return jsonify(chanting.to_dict()), 201

@api_bp.route('/chantings/<int:chanting_id>', methods=['PUT'])
@jwt_required()
def update_chanting(chanting_id):
    """更新佛号经文"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        chanting.title = data['title']
    if 'content' in data:
        chanting.content = data['content']
    if 'pronunciation' in data:
        chanting.pronunciation = data['pronunciation']
    if 'type' in data and data['type'] in ['buddha', 'sutra']:
        chanting.type = data['type']
    
    chanting.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(chanting.to_dict())

@api_bp.route('/chantings/<int:chanting_id>', methods=['DELETE'])
@jwt_required()
def delete_chanting(chanting_id):
    """删除佛号经文（逻辑删除）"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    chanting.soft_delete()
    return jsonify({'message': '删除成功'})

# ================== 回向文相关 ==================

@api_bp.route('/dedications', methods=['GET'])
@jwt_required()
def get_dedications():
    """获取回向文列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    dedications = Dedication.query.filter_by(user_id=user_id).order_by(
        Dedication.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'dedications': [d.to_dict() for d in dedications.items],
        'total': dedications.total,
        'page': page,
        'per_page': per_page,
        'pages': dedications.pages
    })

@api_bp.route('/dedications', methods=['POST'])
@jwt_required()
def create_dedication():
    """创建回向文"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['title', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field}不能为空'}), 400
    
    dedication = Dedication(
        title=data['title'],
        content=data['content'],
        chanting_id=data.get('chanting_id'),
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(dedication)
    db.session.commit()
    
    return jsonify(dedication.to_dict()), 201

@api_bp.route('/dedications/<int:dedication_id>', methods=['PUT'])
@jwt_required()
def update_dedication(dedication_id):
    """更新回向文"""
    user_id = get_jwt_identity()
    dedication = Dedication.query.filter_by(id=dedication_id, user_id=user_id).first()
    if not dedication:
        return jsonify({'error': '回向文不存在'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        dedication.title = data['title']
    if 'content' in data:
        dedication.content = data['content']
    if 'chanting_id' in data:
        dedication.chanting_id = data['chanting_id']
    
    dedication.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(dedication.to_dict())

@api_bp.route('/dedications/<int:dedication_id>', methods=['DELETE'])
@jwt_required()
def delete_dedication(dedication_id):
    """删除回向文"""
    user_id = get_jwt_identity()
    dedication = Dedication.query.filter_by(id=dedication_id, user_id=user_id).first()
    if not dedication:
        return jsonify({'error': '回向文不存在'}), 404
    
    db.session.delete(dedication)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

# ================== 回向文模板相关 ==================

@api_bp.route('/dedication-templates', methods=['GET'])
def get_dedication_templates():
    """获取回向文模板列表"""
    templates = DedicationTemplate.query.order_by(
        DedicationTemplate.is_built_in.desc(),
        DedicationTemplate.created_at.desc()
    ).all()
    
    return jsonify([t.to_dict() for t in templates])

@api_bp.route('/dedication-templates', methods=['POST'])
def create_dedication_template():
    """创建回向文模板（后台管理用）"""
    data = request.get_json()
    
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    template = DedicationTemplate(
        title=data['title'],
        content=data['content'],
        is_built_in=data.get('is_built_in', True)  # 管理员创建的默认为内置
    )
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify(template.to_dict()), 201

@api_bp.route('/dedication-templates/<int:template_id>', methods=['GET'])
def get_dedication_template(template_id):
    """获取单个回向文模板"""
    template = DedicationTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())

@api_bp.route('/dedication-templates/<int:template_id>', methods=['PUT'])
def update_dedication_template(template_id):
    """更新回向文模板（管理员可修改所有模板）"""
    template = DedicationTemplate.query.get_or_404(template_id)
    
    data = request.get_json()
    
    if 'title' in data:
        template.title = data['title']
    if 'content' in data:
        template.content = data['content']
    
    template.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(template.to_dict())

@api_bp.route('/dedication-templates/<int:template_id>', methods=['DELETE'])
def delete_dedication_template(template_id):
    """删除回向文模板（管理员可删除所有模板）"""
    template = DedicationTemplate.query.get_or_404(template_id)
    
    db.session.delete(template)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

# ================== 修行记录相关 ==================

@api_bp.route('/chanting-records', methods=['GET'])
@jwt_required()
def get_chanting_records():
    """获取修行记录列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_user_id = request.args.get('user_id', type=int)
    chanting_id = request.args.get('chanting_id', type=int)
    
    # 构建查询
    query = ChantingRecord.query
    
    # 如果指定了用户筛选，使用筛选条件，否则只显示当前用户的记录
    if filter_user_id:
        query = query.filter(ChantingRecord.user_id == filter_user_id)
    else:
        query = query.filter(ChantingRecord.user_id == current_user_id)
    
    if chanting_id:
        query = query.filter(ChantingRecord.chanting_id == chanting_id)
    
    records = query.order_by(ChantingRecord.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'records': [r.to_dict_with_user_and_chanting() for r in records.items],
        'total': records.total,
        'page': page,
        'per_page': per_page,
        'pages': records.pages
    })

@api_bp.route('/chanting-records', methods=['POST'])
@jwt_required()
def create_chanting_record():
    """创建修行记录"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('chanting_id'):
        return jsonify({'error': 'chanting_id不能为空'}), 400
    
    # 验证佛号经文是否存在
    chanting = Chanting.query.filter_by(id=data['chanting_id'], is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    record = ChantingRecord(
        chanting_id=data['chanting_id'],
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify(record.to_dict_with_chanting()), 201

@api_bp.route('/chanting-records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_chanting_record(record_id):
    """获取单个修行记录详情"""
    user_id = get_jwt_identity()
    record = ChantingRecord.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({'error': '修行记录不存在'}), 404
    
    return jsonify(record.to_dict_with_chanting())

# Alternative shorter route alias
@api_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_record_alias(record_id):
    """获取单个修行记录详情（短路由别名）"""
    return get_chanting_record(record_id)

@api_bp.route('/chanting-records/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_chanting_record(record_id):
    """删除修行记录"""
    user_id = get_jwt_identity()
    record = ChantingRecord.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({'error': '修行记录不存在'}), 404
    
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

# ================== 每日统计相关 ==================

@api_bp.route('/daily-stats', methods=['GET'])
@jwt_required()
def get_daily_stats():
    """获取每日统计"""
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    chanting_id = request.args.get('chanting_id', type=int)
    
    query = DailyStats.query.filter_by(user_id=user_id)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(DailyStats.date >= start_date)
        except ValueError:
            return jsonify({'error': '开始日期格式错误，应为YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(DailyStats.date <= end_date)
        except ValueError:
            return jsonify({'error': '结束日期格式错误，应为YYYY-MM-DD'}), 400
    
    if chanting_id:
        query = query.filter_by(chanting_id=chanting_id)
    
    stats = query.order_by(DailyStats.date.desc()).all()
    
    return jsonify([s.to_dict_with_chanting() for s in stats])

@api_bp.route('/daily-stats', methods=['POST'])
@jwt_required()
def update_daily_stats():
    """更新每日统计"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['chanting_id', 'count']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}不能为空'}), 400
    
    chanting_id = data['chanting_id']
    count = data['count']
    target_date = data.get('date')
    
    if target_date:
        try:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误，应为YYYY-MM-DD'}), 400
    else:
        target_date = date.today()
    
    # 验证佛号经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    # 获取或创建统计记录
    stats = DailyStats.query.filter_by(
        chanting_id=chanting_id,
        user_id=user_id,
        date=target_date
    ).first()
    
    if stats:
        stats.count = count
        stats.updated_at = datetime.utcnow()
    else:
        stats = DailyStats(
            chanting_id=chanting_id,
            user_id=user_id,
            count=count,
            date=target_date,
            created_at=datetime.utcnow()
        )
        db.session.add(stats)
    
    db.session.commit()
    
    return jsonify(stats.to_dict_with_chanting())

@api_bp.route('/daily-stats/increment', methods=['POST'])
@jwt_required()
def increment_daily_stats():
    """增加今日念诵次数"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('chanting_id'):
        return jsonify({'error': 'chanting_id不能为空'}), 400
    
    chanting_id = data['chanting_id']
    increment = data.get('increment', 1)
    
    # 验证佛号经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '佛号经文不存在'}), 404
    
    stats = DailyStats.increment_count(chanting_id, user_id, increment)
    
    return jsonify(stats.to_dict_with_chanting())

# ================== 数据同步相关 ==================

@api_bp.route('/sync/last-updated', methods=['GET'])
@jwt_required()
def get_last_updated():
    """获取各数据表的最后更新时间"""
    user_id = get_jwt_identity()
    
    # 获取各表的最后更新时间
    last_chanting = db.session.query(db.func.max(Chanting.updated_at)).scalar()
    last_dedication = db.session.query(db.func.max(Dedication.updated_at)).filter_by(user_id=user_id).scalar()
    last_record = db.session.query(db.func.max(ChantingRecord.updated_at)).filter_by(user_id=user_id).scalar()
    last_stats = db.session.query(db.func.max(DailyStats.updated_at)).filter_by(user_id=user_id).scalar()
    last_template = db.session.query(db.func.max(DedicationTemplate.updated_at)).scalar()
    
    return jsonify({
        'chantings': last_chanting.isoformat() if last_chanting else None,
        'dedications': last_dedication.isoformat() if last_dedication else None,
        'chanting_records': last_record.isoformat() if last_record else None,
        'daily_stats': last_stats.isoformat() if last_stats else None,
        'dedication_templates': last_template.isoformat() if last_template else None
    })

# ================== 经文章节相关 ==================

@api_bp.route('/chantings/<int:chanting_id>/chapters', methods=['GET'])
@jwt_required()
def get_chapters(chanting_id):
    """获取经文的章节列表"""
    # 验证经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '经文不存在'}), 404
    
    chapters = Chapter.get_by_chanting(chanting_id).all()
    
    return jsonify({
        'chanting_id': chanting_id,
        'chapters': [chapter.to_dict() for chapter in chapters],
        'total_chapters': len(chapters)
    })

@api_bp.route('/chantings/<int:chanting_id>/chapters', methods=['POST'])
@jwt_required()
def create_chapter(chanting_id):
    """创建经文章节"""
    # 验证经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '经文不存在'}), 404
    
    data = request.get_json()
    
    required_fields = ['chapter_number', 'title', 'content']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field}不能为空'}), 400
    
    # 检查章节序号是否重复
    existing_chapter = Chapter.query.filter_by(
        chanting_id=chanting_id,
        chapter_number=data['chapter_number'],
        is_deleted=False
    ).first()
    
    if existing_chapter:
        return jsonify({'error': '章节序号已存在'}), 400
    
    chapter = Chapter(
        chanting_id=chanting_id,
        chapter_number=data['chapter_number'],
        title=data['title'],
        content=data['content'],
        pronunciation=data.get('pronunciation'),
        created_at=datetime.utcnow()
    )
    
    db.session.add(chapter)
    db.session.commit()
    
    return jsonify(chapter.to_dict()), 201

@api_bp.route('/chapters/<int:chapter_id>', methods=['GET'])
@jwt_required()
def get_chapter(chapter_id):
    """获取单个章节详情"""
    chapter = Chapter.query.filter_by(id=chapter_id, is_deleted=False).first()
    if not chapter:
        return jsonify({'error': '章节不存在'}), 404
    
    return jsonify(chapter.to_dict_with_chanting())

@api_bp.route('/chapters/<int:chapter_id>', methods=['PUT'])
@jwt_required()
def update_chapter(chapter_id):
    """更新章节"""
    chapter = Chapter.query.filter_by(id=chapter_id, is_deleted=False).first()
    if not chapter:
        return jsonify({'error': '章节不存在'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        chapter.title = data['title']
    if 'content' in data:
        chapter.content = data['content']
    if 'pronunciation' in data:
        chapter.pronunciation = data['pronunciation']
    if 'chapter_number' in data:
        # 检查新的章节序号是否重复
        existing_chapter = Chapter.query.filter(
            Chapter.chanting_id == chapter.chanting_id,
            Chapter.chapter_number == data['chapter_number'],
            Chapter.id != chapter_id,
            Chapter.is_deleted == False
        ).first()
        
        if existing_chapter:
            return jsonify({'error': '章节序号已存在'}), 400
        
        chapter.chapter_number = data['chapter_number']
    
    chapter.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(chapter.to_dict())

@api_bp.route('/chapters/<int:chapter_id>', methods=['DELETE'])
@jwt_required()
def delete_chapter(chapter_id):
    """删除章节（逻辑删除）"""
    chapter = Chapter.query.filter_by(id=chapter_id, is_deleted=False).first()
    if not chapter:
        return jsonify({'error': '章节不存在'}), 404
    
    chapter.soft_delete()
    return jsonify({'message': '删除成功'})

# ================== 阅读进度相关 ==================

@api_bp.route('/reading-progress', methods=['GET'])
@jwt_required()
def get_reading_progress():
    """获取用户的阅读进度"""
    user_id = get_jwt_identity()
    chanting_id = request.args.get('chanting_id', type=int)
    chapter_id = request.args.get('chapter_id', type=int)
    
    query = ReadingProgress.get_user_progress(user_id, chanting_id)
    
    if chapter_id:
        query = query.filter_by(chapter_id=chapter_id)
    
    progress_list = query.all()
    
    return jsonify([progress.to_dict_with_details() for progress in progress_list])

@api_bp.route('/reading-progress', methods=['POST'])
@jwt_required()
def update_reading_progress():
    """更新阅读进度"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('chanting_id'):
        return jsonify({'error': 'chanting_id不能为空'}), 400
    
    chanting_id = data['chanting_id']
    chapter_id = data.get('chapter_id')
    
    # 验证经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '经文不存在'}), 404
    
    # 如果指定了章节，验证章节是否存在
    if chapter_id:
        chapter = Chapter.query.filter_by(id=chapter_id, is_deleted=False).first()
        if not chapter:
            return jsonify({'error': '章节不存在'}), 404
        
        if chapter.chanting_id != chanting_id:
            return jsonify({'error': '章节不属于指定的经文'}), 400
    
    # 获取或创建进度记录
    progress = ReadingProgress.get_or_create_progress(user_id, chanting_id, chapter_id)
    
    # 更新进度
    progress.update_progress(
        is_completed=data.get('is_completed'),
        reading_position=data.get('reading_position'),
        notes=data.get('notes')
    )
    
    return jsonify(progress.to_dict_with_details())

@api_bp.route('/reading-progress/summary/<int:chanting_id>', methods=['GET'])
@jwt_required()
def get_reading_progress_summary(chanting_id):
    """获取经文的整体阅读进度摘要"""
    user_id = get_jwt_identity()
    
    # 验证经文是否存在
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first()
    if not chanting:
        return jsonify({'error': '经文不存在'}), 404
    
    # 创建一个临时的ReadingProgress实例来调用方法
    temp_progress = ReadingProgress()
    summary = temp_progress.get_chanting_progress_summary(user_id, chanting_id)
    
    return jsonify({
        'chanting_id': chanting_id,
        'chanting_title': chanting.title,
        **summary
    })

@api_bp.route('/reading-progress/<int:progress_id>', methods=['DELETE'])
@jwt_required()
def delete_reading_progress(progress_id):
    """删除阅读进度记录"""
    user_id = get_jwt_identity()
    progress = ReadingProgress.query.filter_by(id=progress_id, user_id=user_id).first()
    if not progress:
        return jsonify({'error': '阅读进度记录不存在'}), 404
    
    db.session.delete(progress)
    db.session.commit()
    
    return jsonify({'message': '删除成功'})
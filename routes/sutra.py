from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from database import db
from models.chanting import Chanting
from models.chapter import Chapter
from models.user import User
from utils.datetime_utils import now
from utils.pinyin_utils import PinyinGenerator

sutra_bp = Blueprint('sutra', __name__)

@sutra_bp.route('/')
@login_required
def index():
    """经文管理页面"""
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '')
    search = request.args.get('search', '')
    user_filter = request.args.get('user', '')
    
    # 只查询经文类型
    query = Chanting.get_active().filter(Chanting.type == 'sutra')
    
    # 来源筛选
    if source == 'builtin':
        query = query.filter(Chanting.is_built_in == True)
    elif source == 'custom':
        query = query.filter(Chanting.is_built_in == False)
    
    # 用户筛选
    if user_filter:
        if user_filter == 'system':
            # 系统内置内容（无创建者）
            query = query.filter(Chanting.user_id.is_(None))
        else:
            # 按用户名筛选
            query = query.filter(User.username == user_filter)
    
    # 搜索筛选
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Chanting.title.contains(search),
                Chanting.content.contains(search)
            )
        )
    
    sutras = query.order_by(Chanting.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 获取所有有经文的用户列表用于筛选
    user_ids = db.session.query(Chanting.user_id).filter(
        Chanting.is_deleted == False,
        Chanting.type == 'sutra',
        Chanting.user_id.isnot(None)
    ).distinct().all()
    user_ids = [uid[0] for uid in user_ids]
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    
    return render_template('sutra/index.html', 
                         chantings=sutras, 
                         current_source=source,
                         current_search=search,
                         current_user_filter=user_filter,
                         users=users)

@sutra_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建经文"""
    if request.method == 'POST':
        title = request.form.get('title')
        
        if not title:
            flash('经文名称是必填项', 'error')
            return render_template('sutra/create.html')
        
        # admin用户添加的标记为内置，普通用户添加的标记为自定义
        from flask_login import current_user
        is_built_in = current_user.username == 'admin'
        
        # 如果是管理员（AdminUser），设置为系统内置，不关联具体用户
        # 如果是普通用户，则关联到对应的users表用户
        if current_user.username == 'admin' and hasattr(current_user, 'email'):
            # 这是AdminUser，设置为系统内置
            user_id = None
        else:
            # 这是普通User
            user_id = current_user.id
        
        sutra = Chanting(
            title=title,
            content='',  # 内容为空，由章节管理
            pronunciation='',  # 注音为空，由章节管理
            type='sutra',  # 固定为经文类型
            is_built_in=is_built_in,
            user_id=user_id,
            created_at=now()
        )
        
        db.session.add(sutra)
        db.session.commit()
        
        flash('经文创建成功，请添加章节内容', 'success')
        return redirect(url_for('sutra.chapters', chanting_id=sutra.id))
    
    return render_template('sutra/create.html')

@sutra_bp.route('/<int:chanting_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(chanting_id):
    """编辑经文"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'  # 确保只能编辑经文
    ).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        
        if not title:
            flash('经文名称是必填项', 'error')
            return render_template('sutra/edit.html', chanting=chanting)
        
        chanting.title = title
        chanting.updated_at = now()
        
        db.session.commit()
        
        flash('经文更新成功', 'success')
        return redirect(url_for('sutra.index'))
    
    return render_template('sutra/edit.html', chanting=chanting)

@sutra_bp.route('/<int:chanting_id>/delete', methods=['POST'])
@login_required
def delete(chanting_id):
    """删除经文"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'  # 确保只能删除经文
    ).first_or_404()
    
    chanting.soft_delete()
    flash('经文删除成功', 'success')
    
    return redirect(url_for('sutra.index'))

@sutra_bp.route('/<int:chanting_id>/detail')
@login_required
def detail(chanting_id):
    """获取经文详情（后台管理用）"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'  # 确保只能查看经文
    ).first_or_404()
    return jsonify(chanting.to_dict())

@sutra_bp.route('/<int:chanting_id>/api-delete', methods=['POST'])
@login_required
def api_delete(chanting_id):
    """删除经文（API接口，后台管理用）"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'  # 确保只能删除经文
    ).first_or_404()
    
    chanting.soft_delete()
    db.session.commit()
    
    return jsonify({'message': '删除成功'})

@sutra_bp.route('/<int:chanting_id>/chapters-info')
@login_required
def chapters_info(chanting_id):
    """获取经文章节信息（用于后台管理界面）"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    chapters = Chapter.query.filter_by(
        chanting_id=chanting_id,
        is_deleted=False
    ).order_by(Chapter.chapter_number).all()
    
    return jsonify({
        'chanting_id': chanting_id,
        'chapters': [chapter.to_dict() for chapter in chapters],
        'total_chapters': len(chapters)
    })

# ================== 章节管理相关 ==================

@sutra_bp.route('/<int:chanting_id>/chapters')
@login_required
def chapters(chanting_id):
    """经文章节管理页面"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    
    chapters = Chapter.query.filter_by(
        chanting_id=chanting_id,
        is_deleted=False
    ).order_by(Chapter.chapter_number).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('sutra/chapters.html', 
                         chanting=chanting,
                         chapters=chapters)

@sutra_bp.route('/<int:chanting_id>/chapters/create', methods=['GET', 'POST'])
@login_required
def create_chapter(chanting_id):
    """创建经文章节"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    if request.method == 'POST':
        chapter_number = request.form.get('chapter_number', type=int)
        title = request.form.get('title')
        content = request.form.get('content')
        pronunciation = request.form.get('pronunciation', '').strip()
        
        if not all([chapter_number, title, content]):
            flash('章节序号、标题和内容都是必填项', 'error')
            return render_template('sutra/create_chapter.html', chanting=chanting)
        
        # 如果用户没有输入注音，自动生成
        if not pronunciation:
            pronunciation = PinyinGenerator.generate_simple_pinyin(content)
        
        # 检查章节序号是否重复
        existing_chapter = Chapter.query.filter_by(
            chanting_id=chanting_id,
            chapter_number=chapter_number,
            is_deleted=False
        ).first()
        
        if existing_chapter:
            flash('章节序号已存在', 'error')
            return render_template('sutra/create_chapter.html', chanting=chanting)
        
        chapter = Chapter(
            chanting_id=chanting_id,
            chapter_number=chapter_number,
            title=title,
            content=content,
            pronunciation=pronunciation,
            created_at=now()
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        flash('章节创建成功', 'success')
        return redirect(url_for('sutra.chapters', chanting_id=chanting_id))
    
    # 获取下一个章节序号
    last_chapter = Chapter.query.filter_by(
        chanting_id=chanting_id,
        is_deleted=False
    ).order_by(Chapter.chapter_number.desc()).first()
    
    next_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1
    
    return render_template('sutra/create_chapter.html', 
                         chanting=chanting,
                         next_chapter_number=next_chapter_number)

@sutra_bp.route('/<int:chanting_id>/chapters/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chapter(chanting_id, chapter_id):
    """编辑经文章节"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    # 确保章节存在且属于该经文
    chapter = Chapter.query.filter_by(
        id=chapter_id,
        chanting_id=chanting_id,
        is_deleted=False
    ).first_or_404()
    
    if request.method == 'POST':
        chapter_number = request.form.get('chapter_number', type=int)
        title = request.form.get('title')
        content = request.form.get('content')
        pronunciation = request.form.get('pronunciation', '').strip()
        
        if not all([chapter_number, title, content]):
            flash('章节序号、标题和内容都是必填项', 'error')
            return render_template('sutra/edit_chapter.html', chanting=chanting, chapter=chapter)
        
        # 如果用户没有输入注音，自动生成
        if not pronunciation:
            pronunciation = PinyinGenerator.generate_simple_pinyin(content)
        
        # 检查章节序号是否重复（排除当前章节）
        existing_chapter = Chapter.query.filter(
            Chapter.chanting_id == chanting_id,
            Chapter.chapter_number == chapter_number,
            Chapter.id != chapter_id,
            Chapter.is_deleted == False
        ).first()
        
        if existing_chapter:
            flash('章节序号已存在', 'error')
            return render_template('sutra/edit_chapter.html', chanting=chanting, chapter=chapter)
        
        chapter.chapter_number = chapter_number
        chapter.title = title
        chapter.content = content
        chapter.pronunciation = pronunciation
        chapter.updated_at = now()
        
        db.session.commit()
        
        flash('章节更新成功', 'success')
        return redirect(url_for('sutra.chapters', chanting_id=chanting_id))
    
    return render_template('sutra/edit_chapter.html', chanting=chanting, chapter=chapter)

@sutra_bp.route('/<int:chanting_id>/chapters/<int:chapter_id>/detail')
@login_required
def chapter_detail(chanting_id, chapter_id):
    """获取单个章节详情"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    # 确保章节存在且属于该经文
    chapter = Chapter.query.filter_by(
        id=chapter_id,
        chanting_id=chanting_id,
        is_deleted=False
    ).first_or_404()
    
    return jsonify(chapter.to_dict())

@sutra_bp.route('/<int:chanting_id>/chapters/<int:chapter_id>/delete', methods=['POST'])
@login_required
def delete_chapter(chanting_id, chapter_id):
    """删除经文章节"""
    # 确保经文存在且为经文类型
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='sutra'
    ).first_or_404()
    
    # 确保章节存在且属于该经文
    chapter = Chapter.query.filter_by(
        id=chapter_id,
        chanting_id=chanting_id,
        is_deleted=False
    ).first_or_404()
    
    chapter.soft_delete()
    flash('章节删除成功', 'success')
    
    return redirect(url_for('sutra.chapters', chanting_id=chanting_id))
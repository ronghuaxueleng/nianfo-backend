from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from database import db
from models.chanting import Chanting
from models.user import User
from utils.datetime_utils import now
from utils.pinyin_utils import PinyinGenerator

buddha_nam_bp = Blueprint('buddha_nam', __name__)

@buddha_nam_bp.route('/')
@login_required
def index():
    """佛号管理页面"""
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '')
    search = request.args.get('search', '')
    user_filter = request.args.get('user', '')
    
    # 只查询佛号类型
    query = Chanting.get_active().filter(Chanting.type == 'buddha')
    
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
    
    buddha_nams = query.order_by(Chanting.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 获取所有有佛号的用户列表用于筛选
    user_ids = db.session.query(Chanting.user_id).filter(
        Chanting.is_deleted == False,
        Chanting.type == 'buddha',
        Chanting.user_id.isnot(None)
    ).distinct().all()
    user_ids = [uid[0] for uid in user_ids]
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    
    return render_template('buddha_nam/index.html', 
                         chantings=buddha_nams, 
                         current_source=source,
                         current_search=search,
                         current_user_filter=user_filter,
                         users=users)

@buddha_nam_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建佛号"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        pronunciation = request.form.get('pronunciation', '').strip()
        
        if not all([title, content]):
            flash('标题和内容都是必填项', 'error')
            return render_template('buddha_nam/create.html')
        
        # 如果用户没有输入注音，自动生成
        if not pronunciation:
            pronunciation = PinyinGenerator.generate_simple_pinyin(content)
        
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
        
        buddha_nam = Chanting(
            title=title,
            content=content,
            pronunciation=pronunciation,
            type='buddha',  # 固定为佛号类型
            is_built_in=is_built_in,
            user_id=user_id,
            created_at=now()
        )
        
        db.session.add(buddha_nam)
        db.session.commit()
        
        flash('佛号创建成功', 'success')
        return redirect(url_for('buddha_nam.index'))
    
    return render_template('buddha_nam/create.html')

@buddha_nam_bp.route('/<int:chanting_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(chanting_id):
    """编辑佛号"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='buddha'  # 确保只能编辑佛号
    ).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        pronunciation = request.form.get('pronunciation', '').strip()
        
        # 如果用户没有输入注音，自动生成
        if not pronunciation:
            pronunciation = PinyinGenerator.generate_simple_pinyin(content)
        
        chanting.title = title
        chanting.content = content
        chanting.pronunciation = pronunciation
        chanting.updated_at = now()
        
        db.session.commit()
        
        flash('佛号更新成功', 'success')
        return redirect(url_for('buddha_nam.index'))
    
    return render_template('buddha_nam/edit.html', chanting=chanting)

@buddha_nam_bp.route('/<int:chanting_id>/delete', methods=['POST'])
@login_required
def delete(chanting_id):
    """删除佛号"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='buddha'  # 确保只能删除佛号
    ).first_or_404()
    
    chanting.soft_delete()
    flash('佛号删除成功', 'success')
    
    return redirect(url_for('buddha_nam.index'))

@buddha_nam_bp.route('/<int:chanting_id>/detail')
@login_required
def detail(chanting_id):
    """获取佛号详情（后台管理用）"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='buddha'  # 确保只能查看佛号
    ).first_or_404()
    return jsonify(chanting.to_dict())

@buddha_nam_bp.route('/<int:chanting_id>/api-delete', methods=['POST'])
@login_required
def api_delete(chanting_id):
    """删除佛号（API接口，后台管理用）"""
    chanting = Chanting.query.filter_by(
        id=chanting_id, 
        is_deleted=False,
        type='buddha'  # 确保只能删除佛号
    ).first_or_404()
    
    chanting.soft_delete()
    db.session.commit()
    
    return jsonify({'message': '删除成功'})
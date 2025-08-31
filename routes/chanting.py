from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from database import db
from models.chanting import Chanting
from models.user import User
from utils.datetime_utils import now

chanting_bp = Blueprint('chanting', __name__)

@chanting_bp.route('/')
@login_required
def index():
    """佛号经文管理页面"""
    page = request.args.get('page', 1, type=int)
    chanting_type = request.args.get('type', '')
    source = request.args.get('source', '')
    search = request.args.get('search', '')
    user_filter = request.args.get('user', '')
    
    query = Chanting.get_active()
    
    # 类型筛选
    if chanting_type:
        query = query.filter(Chanting.type == chanting_type)
    
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
    
    chantings = query.order_by(Chanting.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 获取所有有佛号经文的用户列表用于筛选
    user_ids = db.session.query(Chanting.user_id).filter(
        Chanting.is_deleted == False,
        Chanting.user_id.isnot(None)
    ).distinct().all()
    user_ids = [uid[0] for uid in user_ids]
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    
    return render_template('chanting/index.html', 
                         chantings=chantings, 
                         current_type=chanting_type,
                         current_source=source,
                         current_search=search,
                         current_user_filter=user_filter,
                         users=users)

@chanting_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建佛号经文"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        pronunciation = request.form.get('pronunciation')
        chanting_type = request.form.get('type')
        
        if not all([title, content, chanting_type]):
            flash('标题、内容和类型都是必填项', 'error')
            return render_template('chanting/create.html')
        
        if chanting_type not in ['buddha', 'sutra']:
            flash('类型必须是佛号或经文', 'error')
            return render_template('chanting/create.html')
        
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
        
        chanting = Chanting(
            title=title,
            content=content,
            pronunciation=pronunciation,
            type=chanting_type,
            is_built_in=is_built_in,
            user_id=user_id,
            created_at=now()
        )
        
        db.session.add(chanting)
        db.session.commit()
        
        flash('佛号经文创建成功', 'success')
        return redirect(url_for('chanting.index'))
    
    return render_template('chanting/create.html')

@chanting_bp.route('/<int:chanting_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(chanting_id):
    """编辑佛号经文"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first_or_404()
    
    if request.method == 'POST':
        chanting.title = request.form.get('title')
        chanting.content = request.form.get('content')
        chanting.pronunciation = request.form.get('pronunciation')
        chanting_type = request.form.get('type')
        
        if chanting_type in ['buddha', 'sutra']:
            chanting.type = chanting_type
        
        chanting.updated_at = now()
        db.session.commit()
        
        flash('佛号经文更新成功', 'success')
        return redirect(url_for('chanting.index'))
    
    return render_template('chanting/edit.html', chanting=chanting)

@chanting_bp.route('/<int:chanting_id>/delete', methods=['POST'])
@login_required
def delete(chanting_id):
    """删除佛号经文"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first_or_404()
    
    chanting.soft_delete()
    flash('佛号经文删除成功', 'success')
    
    return redirect(url_for('chanting.index'))

@chanting_bp.route('/<int:chanting_id>/detail')
@login_required
def detail(chanting_id):
    """获取佛号经文详情（后台管理用）"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first_or_404()
    return jsonify(chanting.to_dict())

@chanting_bp.route('/<int:chanting_id>/api-delete', methods=['POST'])
@login_required
def api_delete(chanting_id):
    """删除佛号经文（API接口，后台管理用）"""
    chanting = Chanting.query.filter_by(id=chanting_id, is_deleted=False).first_or_404()
    
    chanting.soft_delete()
    db.session.commit()
    
    return jsonify({'message': '删除成功'})
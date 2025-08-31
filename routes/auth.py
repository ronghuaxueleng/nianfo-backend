from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from database import db
from models.user import AdminUser

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('auth/login.html')
        
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            flash(f'欢迎回来，{admin.username}！', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """管理员登出"""
    logout_user()
    flash('已成功退出', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """个人中心"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人信息"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证用户名不能为空
        if not username:
            flash('用户名不能为空', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 验证邮箱不能为空
        if not email:
            flash('邮箱不能为空', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 检查用户名是否已被其他用户使用
        existing_user = AdminUser.query.filter(
            AdminUser.username == username,
            AdminUser.id != current_user.id
        ).first()
        if existing_user:
            flash('用户名已被使用', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 检查邮箱是否已被其他用户使用
        existing_email = AdminUser.query.filter(
            AdminUser.email == email,
            AdminUser.id != current_user.id
        ).first()
        if existing_email:
            flash('邮箱已被使用', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 更新基本信息
        current_user.username = username
        current_user.email = email
        
        # 如果要修改密码
        if new_password:
            # 验证当前密码
            if not current_password or not current_user.check_password(current_password):
                flash('当前密码错误', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            # 验证新密码
            if len(new_password) < 6:
                flash('新密码至少需要6位字符', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            # 验证密码确认
            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'error')
                return render_template('auth/edit_profile.html', user=current_user)
            
            # 更新密码
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('个人信息更新成功', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请重试', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)
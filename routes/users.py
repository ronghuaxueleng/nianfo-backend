from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models.user import User
from datetime import datetime
import logging
from utils.crypto_utils import CryptoUtils

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
def index():
    """用户列表页面"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        # 构建查询 - 显示users表中所有未删除的用户
        query = User.query.filter_by(is_deleted=False)
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.nickname.contains(search)
                )
            )
        
        # 分页查询
        users = query.order_by(User.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 统计信息 - 统计users表中所有未删除的用户
        total_users = User.query.filter_by(is_deleted=False).count()
        active_users = User.query.filter(
            User.created_at >= datetime.now().replace(day=1),
            User.is_deleted == False
        ).count()
        
        return render_template('users/index.html', 
                             users=users, 
                             search=search,
                             total_users=total_users,
                             active_users=active_users)
    
    except Exception as e:
        logging.error(f"获取用户列表失败: {str(e)}")
        flash('获取用户列表失败', 'error')
        return redirect(url_for('main.dashboard'))

@users_bp.route('/<int:user_id>')
@login_required
def detail(user_id):
    """用户详情页面"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 获取用户相关统计
        from models.chanting_record import ChantingRecord
        from models.daily_stats import DailyStats
        from models.dedication import Dedication
        
        # 修行记录数（根据用户ID查询）
        record_count = ChantingRecord.query.filter_by(user_id=user_id).count()
        
        # 总念诵次数（根据用户ID查询每日统计的总和）
        total_count = db.session.query(db.func.sum(DailyStats.count)).filter_by(user_id=user_id).scalar() or 0
        
        # 回向数量（根据用户ID查询）
        dedication_count = Dedication.query.filter_by(user_id=user_id).count()
        
        # 最近活动（根据用户ID查询）
        recent_stats = DailyStats.query.filter_by(user_id=user_id).order_by(
            DailyStats.updated_at.desc()
        ).limit(10).all()
        
        return render_template('users/detail.html', 
                             user=user,
                             record_count=record_count,
                             total_count=total_count,
                             dedication_count=dedication_count,
                             recent_stats=recent_stats)
    
    except Exception as e:
        logging.error(f"获取用户详情失败: {str(e)}")
        flash('获取用户详情失败', 'error')
        return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    """编辑用户"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            # 更新用户信息
            user.nickname = request.form.get('nickname', user.nickname)
            
            # 处理头像类型：空字符串转为None（默认头像）
            avatar_type = request.form.get('avatar_type', user.avatar_type)
            user.avatar_type = avatar_type if avatar_type else None
            
            # 处理头像内容
            avatar = request.form.get('avatar', user.avatar)
            user.avatar = avatar if avatar else None
            
            # 如果提供了新密码
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password:
                # 验证密码确认
                if new_password != confirm_password:
                    flash('两次输入的密码不一致', 'error')
                    return render_template('users/edit.html', user=user)
                
                # 验证密码长度
                if len(new_password) < 6:
                    flash('新密码至少需要6位字符', 'error')
                    return render_template('users/edit.html', user=user)
                
                # 使用与app相同的哈希方法加密密码
                user.password = CryptoUtils.hash_password(new_password)
            
            db.session.commit()
            flash('用户信息更新成功', 'success')
            return redirect(url_for('users.detail', user_id=user.id))
        
        return render_template('users/edit.html', user=user)
    
    except Exception as e:
        logging.error(f"编辑用户失败: {str(e)}")
        flash('编辑用户失败', 'error')
        return redirect(url_for('users.index'))

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete(user_id):
    """删除用户"""
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        # 软删除：标记为已删除而不是真正删除
        # 或者你可以选择真正删除：db.session.delete(user)
        user.is_deleted = True  # 需要在User模型中添加这个字段
        user.deleted_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'用户 {username} 已删除', 'success')
        
    except Exception as e:
        logging.error(f"删除用户失败: {str(e)}")
        flash('删除用户失败', 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/export')
@login_required
def export():
    """导出用户数据"""
    try:
        users = User.query.filter_by(is_deleted=False).all()
        
        # 构建CSV数据
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题
        writer.writerow(['ID', '用户名', '昵称', '头像类型', '创建时间'])
        
        # 写入数据
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.nickname or '',
                user.avatar_type or '',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
            ])
        
        # 生成响应
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    except Exception as e:
        logging.error(f"导出用户数据失败: {str(e)}")
        flash('导出用户数据失败', 'error')
        return redirect(url_for('users.index'))

@users_bp.route('/stats')
@login_required
def stats():
    """用户统计页面"""
    try:
        # 总用户数 - 统计users表中所有未删除用户
        total_users = User.query.filter_by(is_deleted=False).count()
        
        # 本月新增用户
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new = User.query.filter(
            User.created_at >= current_month,
            User.is_deleted == False
        ).count()
        
        # 今日新增用户
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_new = User.query.filter(
            User.created_at >= today,
            User.is_deleted == False
        ).count()
        
        # 用户注册趋势（最近7天） - 统计users表中所有用户
        from datetime import timedelta
        trends = []
        for i in range(7):
            date = today - timedelta(days=i)
            next_date = date + timedelta(days=1)
            count = User.query.filter(
                User.created_at >= date,
                User.created_at < next_date,
                User.is_deleted == False
            ).count()
            trends.append({
                'date': date.strftime('%m-%d'),
                'count': count
            })
        trends.reverse()
        
        # 头像类型分布 - 统计users表中所有用户
        avatar_types = db.session.query(
            User.avatar_type,
            db.func.count(User.id).label('count')
        ).filter_by(is_deleted=False).group_by(User.avatar_type).all()
        
        return render_template('users/stats.html',
                             total_users=total_users,
                             monthly_new=monthly_new,
                             daily_new=daily_new,
                             trends=trends,
                             avatar_types=avatar_types,
                             now=datetime.now())
    
    except Exception as e:
        logging.error(f"获取用户统计失败: {str(e)}")
        flash('获取用户统计失败', 'error')
        return redirect(url_for('main.dashboard'))
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from database import db
from models.chanting_record import ChantingRecord
from models.chanting import Chanting
from models.daily_stats import DailyStats
from models.user import User
from datetime import datetime, date, timedelta
from sqlalchemy import func

records_bp = Blueprint('records', __name__)

@records_bp.route('/')
@login_required
def index():
    """修行记录管理页面"""
    # 获取筛选参数
    chanting_id = request.args.get('chanting_id', type=int)
    user_id = request.args.get('user_id', type=int)
    filter_date = request.args.get('date')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询
    query = ChantingRecord.query
    
    if chanting_id:
        query = query.filter(ChantingRecord.chanting_id == chanting_id)
    
    if user_id:
        query = query.filter(ChantingRecord.user_id == user_id)
    
    # 日期筛选
    if filter_date:
        try:
            # 解析日期
            filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            # 筛选当天的记录（根据updated_at字段）
            start_datetime = datetime.combine(filter_date_obj, datetime.min.time())
            end_datetime = datetime.combine(filter_date_obj, datetime.max.time())
            query = query.filter(
                ChantingRecord.updated_at >= start_datetime,
                ChantingRecord.updated_at <= end_datetime
            )
        except ValueError:
            # 日期格式错误，忽略筛选
            pass
    
    # 获取记录并添加统计信息
    records = query.order_by(ChantingRecord.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 将记录转换为包含关联数据的字典列表
    today = date.today()
    enhanced_records = []
    for record in records.items:
        # 获取包含关联数据的记录字典
        record_dict = record.to_dict_with_user_and_chanting()
        
        # 今日念诵次数
        today_stat = DailyStats.query.filter_by(
            chanting_id=record.chanting_id,
            date=today
        ).first()
        record_dict['today_count'] = today_stat.count if today_stat else 0
        
        # 总念诵次数
        total_count = db.session.query(func.sum(DailyStats.count)).filter_by(
            chanting_id=record.chanting_id
        ).scalar()
        record_dict['total_count'] = total_count or 0
        
        enhanced_records.append(record_dict)
    
    # 替换原始的 records.items 为处理后的数据
    records.items = enhanced_records
    
    # 获取可用的佛号经文列表
    available_chantings = Chanting.query.filter_by(is_deleted=False).order_by(Chanting.title).all()
    
    # 获取所有应用用户列表（只包括未删除的普通用户）
    available_users = User.query.filter_by(is_deleted=False).order_by(User.username).all()
    
    return render_template('records/index.html',
                         records=records.items,
                         pagination=records,
                         available_chantings=available_chantings,
                         available_users=available_users,
                         selected_chanting_id=chanting_id,
                         selected_user_id=user_id,
                         selected_date=filter_date)

@records_bp.route('/<int:record_id>')
@login_required
def get_record(record_id):
    """获取单个修行记录详情（Web版本）"""
    record = ChantingRecord.query.filter_by(id=record_id).first()
    if not record:
        return jsonify({'error': '修行记录不存在'}), 404
    
    # 获取今日统计
    today = date.today()
    today_stat = DailyStats.query.filter_by(
        chanting_id=record.chanting_id,
        date=today
    ).first()
    
    # 获取总统计
    total_count = db.session.query(func.sum(DailyStats.count)).filter_by(
        chanting_id=record.chanting_id
    ).scalar()
    
    # 获取修行天数
    practice_days = db.session.query(func.count(DailyStats.id)).filter(
        DailyStats.chanting_id == record.chanting_id,
        DailyStats.count > 0
    ).scalar()
    
    data = record.to_dict_with_user_and_chanting()
    data['today_count'] = today_stat.count if today_stat else 0
    data['total_count'] = total_count or 0
    data['practice_days'] = practice_days or 0
    
    return jsonify(data)

@records_bp.route('/<int:record_id>/stats')
@login_required
def get_record_stats(record_id):
    """获取修行记录的详细统计信息"""
    record = ChantingRecord.query.filter_by(id=record_id).first()
    if not record:
        return jsonify({'error': '修行记录不存在'}), 404
    
    # 获取该佛号经文的所有统计数据
    stats_query = DailyStats.query.filter_by(chanting_id=record.chanting_id).order_by(DailyStats.date.desc())
    all_stats = stats_query.all()
    
    # 基本统计
    today = date.today()
    total_count = sum(stat.count for stat in all_stats)
    total_days = len([stat for stat in all_stats if stat.count > 0])
    today_count = next((stat.count for stat in all_stats if stat.date == today), 0)
    
    # 最近7天统计
    week_ago = today - timedelta(days=6)
    recent_stats = [stat for stat in all_stats if stat.date >= week_ago]
    week_total = sum(stat.count for stat in recent_stats)
    
    # 最近30天统计
    month_ago = today - timedelta(days=29)
    month_stats = [stat for stat in all_stats if stat.date >= month_ago]
    month_total = sum(stat.count for stat in month_stats)
    
    # 最高单日记录
    max_daily = max((stat.count for stat in all_stats), default=0)
    max_daily_date = next((stat.date.strftime('%Y-%m-%d') for stat in all_stats if stat.count == max_daily), None) if max_daily > 0 else None
    
    # 连续修行天数（当前连续）
    consecutive_days = 0
    check_date = today
    while True:
        day_stat = next((stat for stat in all_stats if stat.date == check_date), None)
        if day_stat and day_stat.count > 0:
            consecutive_days += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # 最长连续修行天数
    max_consecutive = 0
    current_consecutive = 0
    
    # 按日期排序统计数据
    sorted_stats = sorted(all_stats, key=lambda x: x.date)
    for i, stat in enumerate(sorted_stats):
        if stat.count > 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    # 平均每日念诵次数
    avg_daily = round(total_count / total_days, 1) if total_days > 0 else 0
    
    # 最近7天数据用于图表
    chart_data = []
    for i in range(6, -1, -1):
        check_date = today - timedelta(days=i)
        day_stat = next((stat for stat in all_stats if stat.date == check_date), None)
        chart_data.append({
            'date': check_date.strftime('%Y-%m-%d'),
            'date_short': check_date.strftime('%m-%d'),
            'count': day_stat.count if day_stat else 0
        })
    
    # Get chanting details
    from models.chanting import Chanting
    chanting = Chanting.query.get(record.chanting_id)
    chanting_data = chanting.to_dict() if chanting else None
    
    # Get user details if available
    user_data = None
    if record.user_id:
        from models.user import User
        user = User.query.get(record.user_id)
        if user:
            user_data = {
                'id': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'avatar': user.avatar,
                'avatar_type': user.avatar_type
            }
    
    return jsonify({
        'record_id': record_id,
        'chanting': chanting_data,
        'user': user_data,
        'stats': {
            'today_count': today_count,
            'total_count': total_count,
            'total_days': total_days,
            'week_total': week_total,
            'month_total': month_total,
            'max_daily': max_daily,
            'max_daily_date': max_daily_date,
            'consecutive_days': consecutive_days,
            'max_consecutive': max_consecutive,
            'avg_daily': avg_daily,
            'chart_data': chart_data
        }
    })
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from database import db
from models.chanting import Chanting
from models.chanting_record import ChantingRecord
from models.dedication import Dedication
from models.daily_stats import DailyStats
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/')
@login_required
def index():
    """统计报表页面"""
    selected_date = request.args.get('date')
    if selected_date:
        try:
            target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()
    
    # 基础统计
    total_chantings = Chanting.query.filter_by(is_deleted=False).count()
    total_records = ChantingRecord.query.count()
    total_dedications = Dedication.query.count()
    
    # 今日总念诵次数
    today_total_count = db.session.query(func.sum(DailyStats.count)).filter_by(
        date=target_date
    ).scalar() or 0
    
    # 热门修行项目 (按总念诵次数排序)
    top_practices = db.session.query(
        Chanting.id,
        Chanting.title,
        Chanting.type,
        func.sum(DailyStats.count).label('total_count')
    ).join(DailyStats, Chanting.id == DailyStats.chanting_id).filter(
        Chanting.is_deleted == False
    ).group_by(
        Chanting.id, Chanting.title, Chanting.type
    ).order_by(
        desc('total_count')
    ).limit(10).all()
    
    # 指定日期的详细统计
    daily_stats_query = db.session.query(
        DailyStats,
        Chanting
    ).join(Chanting, DailyStats.chanting_id == Chanting.id).filter(
        DailyStats.date == target_date,
        Chanting.is_deleted == False
    ).order_by(desc(DailyStats.count))
    
    daily_stats = []
    for stat, chanting in daily_stats_query:
        # 计算修行天数
        practice_days = DailyStats.query.filter(
            DailyStats.chanting_id == chanting.id,
            DailyStats.count > 0
        ).count()
        
        # 计算累计念诵
        total_count = db.session.query(func.sum(DailyStats.count)).filter_by(
            chanting_id=chanting.id
        ).scalar() or 0
        
        daily_stats.append({
            'chanting': chanting,
            'today_count': stat.count,
            'total_count': total_count,
            'practice_days': practice_days,
            'last_updated': stat.updated_at
        })
    
    return render_template('stats/index.html',
                         total_chantings=total_chantings,
                         total_records=total_records,
                         total_dedications=total_dedications,
                         today_total_count=today_total_count,
                         top_practices=top_practices,
                         daily_stats=daily_stats,
                         selected_date=selected_date,
                         today=target_date.strftime('%Y-%m-%d'))

@stats_bp.route('/chart')
@login_required
def chart_data():
    """获取图表数据"""
    days = request.args.get('days', 30, type=int)
    
    # 计算日期范围
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # 获取每日统计数据
    daily_totals = db.session.query(
        DailyStats.date,
        func.sum(DailyStats.count).label('total_count')
    ).filter(
        DailyStats.date >= start_date,
        DailyStats.date <= end_date
    ).group_by(DailyStats.date).order_by(DailyStats.date).all()
    
    # 创建日期标签和数据
    labels = []
    values = []
    
    # 填充所有日期，没有数据的日期设为0
    current_date = start_date
    daily_dict = {stat.date: stat.total_count for stat in daily_totals}
    
    while current_date <= end_date:
        labels.append(current_date.strftime('%m-%d'))
        values.append(daily_dict.get(current_date, 0))
        current_date += timedelta(days=1)
    
    return jsonify({
        'labels': labels,
        'values': values
    })
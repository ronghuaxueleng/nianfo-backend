from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from database import db
from models.sync_record import SyncRecord
from models.sync_config import SyncConfig
from models.user import User
from sqlalchemy import desc, func
import json
import csv
import io

sync_management_bp = Blueprint('sync_management', __name__, url_prefix='/sync-management')

# 添加模板函数
@sync_management_bp.app_template_global()
def get_config_value(config_key, default=''):
    """获取配置值"""
    config = SyncConfig.query.filter_by(config_key=config_key, is_active=True).first()
    return config.config_value if config else default

@sync_management_bp.app_template_global()
def get_config_policy(config_key, policy_key):
    """获取策略配置中的特定值"""
    config = SyncConfig.query.filter_by(config_key=config_key, is_active=True).first()
    if config:
        try:
            policy = json.loads(config.config_value)
            return policy.get(policy_key, False)
        except:
            return False
    return False

@sync_management_bp.app_template_global()
def get_config_protection(config_key, protection_key):
    """获取保护策略配置中的特定值"""
    config = SyncConfig.query.filter_by(config_key=config_key, is_active=True).first()
    if config:
        try:
            protection = json.loads(config.config_value)
            return protection.get(protection_key, False)
        except:
            return False
    return False

@sync_management_bp.app_template_global()
def get_config_rate_limit(config_key, limit_key):
    """获取频率限制配置中的特定值"""
    config = SyncConfig.query.filter_by(config_key=config_key, is_active=True).first()
    if config:
        try:
            rate_limit = json.loads(config.config_value)
            return rate_limit.get(limit_key, 100)
        except:
            return 100
    return 100

@sync_management_bp.route('/records')
@login_required
def sync_records():
    """同步记录管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 限制每页最大数量，防止性能问题
    if per_page > 100:
        per_page = 100
    
    # 获取查询参数
    user_id = request.args.get('user_id', type=int)
    device_id = request.args.get('device_id')
    sync_status = request.args.get('sync_status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # 构建查询
    query = db.session.query(SyncRecord, User).join(
        User, SyncRecord.user_id == User.id
    ).order_by(desc(SyncRecord.sync_started_at))
    
    # 应用过滤条件
    if user_id:
        query = query.filter(SyncRecord.user_id == user_id)
    if device_id:
        query = query.filter(SyncRecord.device_id.contains(device_id))
    if sync_status:
        query = query.filter(SyncRecord.sync_status == sync_status)
    if date_from:
        query = query.filter(SyncRecord.sync_started_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(SyncRecord.sync_started_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
    
    # 分页
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 获取用户列表用于筛选
    users = User.query.filter_by(is_deleted=False).all()
    
    # 如果是导出请求
    if request.args.get('export') == 'csv':
        return export_sync_records_csv(query)
    
    # 如果是AJAX请求，只返回表格部分
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('sync_management/records_table.html',
                             records=pagination.items,
                             pagination=pagination,
                             filters={
                                 'user_id': user_id,
                                 'device_id': device_id,
                                 'sync_status': sync_status,
                                 'date_from': date_from,
                                 'date_to': date_to,
                                 'per_page': per_page
                             })
    
    # 获取统计信息
    stats = get_sync_stats()
    
    return render_template('sync_management/records.html',
                         records=pagination.items,
                         pagination=pagination,
                         users=users,
                         stats=stats,
                         filters={
                             'user_id': user_id,
                             'device_id': device_id,
                             'sync_status': sync_status,
                             'date_from': date_from,
                             'date_to': date_to,
                             'per_page': per_page
                         })

@sync_management_bp.route('/configs')
@login_required
def sync_configs():
    """同步配置管理页面"""
    configs = SyncConfig.query.order_by(SyncConfig.created_at.desc()).all()
    
    # 将JSON字符串解析为字典以便在模板中显示
    parsed_configs = []
    for config in configs:
        try:
            parsed_value = json.loads(config.config_value)
        except:
            parsed_value = config.config_value
        
        parsed_configs.append({
            'id': config.id,
            'config_key': config.config_key,
            'config_value': config.config_value,
            'parsed_value': parsed_value,
            'description': config.description,
            'is_active': config.is_active,
            'created_at': config.created_at,
            'updated_at': config.updated_at
        })
    
    return render_template('sync_management/configs.html', configs=parsed_configs)

@sync_management_bp.route('/configs/edit/<int:config_id>', methods=['GET', 'POST'])
@login_required
def edit_config(config_id):
    """编辑同步配置"""
    config = SyncConfig.query.get_or_404(config_id)
    
    if request.method == 'POST':
        try:
            new_value = request.form.get('config_value', '').strip()
            description = request.form.get('description', '').strip()
            is_active = request.form.get('is_active') == '1'
            
            # 验证JSON格式
            if new_value.startswith('{') or new_value.startswith('['):
                json.loads(new_value)  # 验证JSON格式
            
            config.config_value = new_value
            config.description = description or config.description
            config.is_active = is_active
            config.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('配置更新成功', 'success')
            return redirect(url_for('sync_management.sync_configs'))
            
        except json.JSONDecodeError:
            flash('JSON格式无效，请检查配置值格式', 'error')
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'error')
            db.session.rollback()
    
    # 解析当前值用于编辑
    try:
        parsed_value = json.loads(config.config_value)
        if isinstance(parsed_value, dict):
            formatted_value = json.dumps(parsed_value, indent=2, ensure_ascii=False)
        else:
            formatted_value = config.config_value
    except:
        formatted_value = config.config_value
    
    return render_template('sync_management/edit_config.html', 
                         config=config, 
                         formatted_value=formatted_value)

@sync_management_bp.route('/configs/toggle/<int:config_id>', methods=['POST'])
@login_required
def toggle_config(config_id):
    """切换配置启用状态"""
    config = SyncConfig.query.get_or_404(config_id)
    config.is_active = not config.is_active
    config.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        status = '启用' if config.is_active else '禁用'
        flash(f'配置已{status}', 'success')
    except Exception as e:
        flash(f'操作失败: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('sync_management.sync_configs'))

@sync_management_bp.route('/api/records/<int:record_id>/delete', methods=['DELETE'])
@login_required
def delete_sync_record(record_id):
    """删除同步记录"""
    try:
        record = SyncRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '同步记录已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/records/batch-delete', methods=['DELETE'])
@login_required
def batch_delete_sync_records():
    """批量删除同步记录"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({
                'success': False,
                'message': '请选择要删除的记录'
            }), 400
        
        # 验证所有ID都是整数
        try:
            record_ids = [int(id) for id in record_ids]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': '无效的记录ID'
            }), 400
        
        # 查找并删除记录
        records = SyncRecord.query.filter(SyncRecord.id.in_(record_ids)).all()
        if not records:
            return jsonify({
                'success': False,
                'message': '未找到要删除的记录'
            }), 404
        
        deleted_count = len(records)
        for record in records:
            db.session.delete(record)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已成功删除 {deleted_count} 条记录'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/config/save', methods=['POST'])
@login_required
def save_config():
    """保存单个配置"""
    try:
        data = request.get_json()
        config_key = data.get('config_key')
        config_value = data.get('config_value')
        
        if not config_key:
            return jsonify({
                'success': False,
                'message': '配置键不能为空'
            }), 400
        
        # 查找或创建配置
        config = SyncConfig.query.filter_by(config_key=config_key).first()
        if config:
            config.config_value = config_value
            config.updated_at = datetime.utcnow()
        else:
            config = SyncConfig(
                config_key=config_key,
                config_value=config_value,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/config/save-batch', methods=['POST'])
@login_required
def save_batch_configs():
    """批量保存配置"""
    try:
        data = request.get_json()
        configs = data.get('configs', {})
        
        if not configs:
            return jsonify({
                'success': False,
                'message': '没有要保存的配置'
            }), 400
        
        saved_count = 0
        for config_key, config_value in configs.items():
            # 查找或创建配置
            config = SyncConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = str(config_value)
                config.updated_at = datetime.utcnow()
            else:
                config = SyncConfig(
                    config_key=config_key,
                    config_value=str(config_value),
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(config)
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已保存 {saved_count} 个配置'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量保存失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/config/reset-defaults', methods=['POST'])
@login_required
def reset_defaults():
    """恢复默认配置"""
    try:
        # 删除所有现有配置
        SyncConfig.query.delete()
        
        # 创建默认配置
        default_configs = [
            {
                'config_key': 'sync_enabled',
                'config_value': 'true',
                'description': '启用同步功能'
            },
            {
                'config_key': 'first_sync_auto_create_user',
                'config_value': 'true',
                'description': '首次同步自动创建用户'
            },
            {
                'config_key': 'sync_allowed_data_types',
                'config_value': '["users", "chanting_records", "daily_stats", "dedications"]',
                'description': '允许同步的数据类型'
            },
            {
                'config_key': 'app_data_overwrite_policy',
                'config_value': '{"users": true, "chanting_records": true, "daily_stats": true, "dedications": true, "chantings": false, "dedication_templates": false}',
                'description': 'App数据覆盖策略'
            },
            {
                'config_key': 'built_in_content_protection',
                'config_value': '{"strict_mode": true, "protected_fields": ["title", "content", "pronunciation", "type", "is_built_in"], "admin_only_operations": ["create_built_in", "update_built_in", "delete_built_in"], "allow_user_content_only": true}',
                'description': '内置内容保护策略'
            },
            {
                'config_key': 'sync_rate_limit',
                'config_value': '{"max_requests_per_hour": 60, "max_requests_per_day": 500}',
                'description': '同步频率限制'
            }
        ]
        
        for config_data in default_configs:
            config = SyncConfig(
                config_key=config_data['config_key'],
                config_value=config_data['config_value'],
                description=config_data['description'],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '已恢复默认配置'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'恢复默认配置失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/records/create-test-data', methods=['POST'])
@login_required
def create_test_sync_records():
    """创建测试同步记录"""
    import random
    from datetime import datetime, timedelta
    import uuid
    
    try:
        # 获取所有用户
        users = User.query.filter_by(is_deleted=False).all()
        if not users:
            return jsonify({
                'success': False,
                'message': '没有找到用户，请先创建用户'
            }), 400
        
        # 创建20条测试记录
        test_records = []
        sync_types = ['full', 'incremental']
        sync_directions = ['upload', 'download', 'bidirectional']
        sync_statuses = ['success', 'failed', 'partial']
        data_types_options = [
            'users,chanting_records,daily_stats',
            'chantings,dedication_templates',
            'dedications,chanting_records',
            'users,chantings,dedications',
            'daily_stats,chanting_records'
        ]
        
        for i in range(20):
            user = random.choice(users)
            
            # 随机生成时间（最近30天内）
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            start_time = datetime.utcnow() - timedelta(
                days=days_ago, 
                hours=hours_ago, 
                minutes=minutes_ago
            )
            
            sync_status = random.choice(sync_statuses)
            
            # 根据状态决定是否有完成时间
            if sync_status in ['success', 'partial']:
                # 成功或部分成功的记录有完成时间
                duration = random.randint(5, 300)  # 5秒到5分钟
                end_time = start_time + timedelta(seconds=duration)
            else:
                # 失败的记录可能没有完成时间
                end_time = start_time + timedelta(seconds=random.randint(10, 60)) if random.choice([True, False]) else None
            
            # 错误消息（失败记录才有）
            error_messages = [
                None,  # 成功记录
                'Connection timeout',
                'Server error 500',
                'Authentication failed',
                'Network unreachable',
                'Data validation error'
            ]
            
            error_message = None
            if sync_status == 'failed':
                error_message = random.choice(error_messages[1:])
            
            record = SyncRecord(
                user_id=user.id,
                device_id=str(uuid.uuid4()),
                sync_type=random.choice(sync_types),
                sync_direction=random.choice(sync_directions),
                sync_status=sync_status,
                sync_data_types=random.choice(data_types_options),
                sync_started_at=start_time,
                sync_completed_at=end_time,
                error_message=error_message
            )
            
            test_records.append(record)
        
        # 批量插入数据库
        db.session.add_all(test_records)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已成功创建 {len(test_records)} 条测试同步记录'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建测试数据失败: {str(e)}'
        }), 500

@sync_management_bp.route('/api/stats')
@login_required
def api_stats():
    """获取同步统计数据API"""
    return jsonify(get_sync_stats())

@sync_management_bp.route('/api/records/<int:record_id>/details')
@login_required
def api_record_details(record_id):
    """获取同步记录详情API"""
    record = SyncRecord.query.get_or_404(record_id)
    user = User.query.get(record.user_id)
    
    return jsonify({
        'id': record.id,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname
        } if user else None,
        'device_id': record.device_id,
        'sync_type': record.sync_type,
        'sync_direction': record.sync_direction,
        'sync_status': record.sync_status,
        'sync_data_types': record.sync_data_types,
        'error_message': record.error_message,
        'sync_started_at': record.sync_started_at.isoformat() if record.sync_started_at else None,
        'sync_completed_at': record.sync_completed_at.isoformat() if record.sync_completed_at else None,
        'duration': str(record.sync_completed_at - record.sync_started_at) if record.sync_completed_at and record.sync_started_at else None
    })

def get_sync_stats():
    """获取同步统计信息"""
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # 总统计
    total_records = SyncRecord.query.count()
    success_records = SyncRecord.query.filter_by(sync_status='success').count()
    failed_records = SyncRecord.query.filter_by(sync_status='failed').count()
    
    # 今日统计
    today_records = SyncRecord.query.filter(
        func.date(SyncRecord.sync_started_at) == today
    ).count()
    
    # 7天统计
    week_records = SyncRecord.query.filter(
        SyncRecord.sync_started_at >= week_ago
    ).count()
    
    # 30天统计
    month_records = SyncRecord.query.filter(
        SyncRecord.sync_started_at >= month_ago
    ).count()
    
    # 活跃用户
    active_users = db.session.query(func.count(func.distinct(SyncRecord.user_id))).filter(
        SyncRecord.sync_started_at >= week_ago
    ).scalar()
    
    # 设备数量
    active_devices = db.session.query(func.count(func.distinct(SyncRecord.device_id))).filter(
        SyncRecord.sync_started_at >= week_ago
    ).scalar()
    
    # 成功率
    success_rate = (success_records / total_records * 100) if total_records > 0 else 0
    
    return {
        'total_records': total_records,
        'success_records': success_records,
        'failed_records': failed_records,
        'success_rate': round(success_rate, 2),
        'today_records': today_records,
        'week_records': week_records,
        'month_records': month_records,
        'active_users': active_users,
        'active_devices': active_devices
    }

def export_sync_records_csv(query):
    """导出同步记录为CSV文件"""
    # 获取所有记录（不分页）
    records = query.all()
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入CSV头部
    writer.writerow([
        'ID', '用户名', '昵称', '设备ID', '同步类型', '同步方向', 
        '同步状态', '数据类型', '开始时间', '完成时间', '耗时(秒)', '错误信息'
    ])
    
    # 写入数据行
    for record, user in records:
        duration = ''
        if record.sync_completed_at and record.sync_started_at:
            duration = str((record.sync_completed_at - record.sync_started_at).total_seconds())
            
        sync_type_map = {'full': '全量同步', 'incremental': '增量同步'}
        sync_direction_map = {'upload': '上传', 'download': '下载', 'bidirectional': '双向'}
        sync_status_map = {'success': '成功', 'failed': '失败', 'partial': '部分成功'}
        
        writer.writerow([
            record.id,
            user.username if user else '未知用户',
            user.nickname if user else '',
            record.device_id,
            sync_type_map.get(record.sync_type, record.sync_type),
            sync_direction_map.get(record.sync_direction, record.sync_direction),
            sync_status_map.get(record.sync_status, record.sync_status),
            record.sync_data_types or '',
            record.sync_started_at.strftime('%Y-%m-%d %H:%M:%S') if record.sync_started_at else '',
            record.sync_completed_at.strftime('%Y-%m-%d %H:%M:%S') if record.sync_completed_at else '',
            duration,
            record.error_message or ''
        ])
    
    # 准备响应
    output.seek(0)
    filename = f'sync_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
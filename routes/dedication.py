from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from database import db
from models.dedication_template import DedicationTemplate
from sqlalchemy import or_

dedication_bp = Blueprint('dedication', __name__)

@dedication_bp.route('/')
@login_required
def index():
    """回向文模板管理页面"""
    # 获取搜索参数
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询
    query = DedicationTemplate.query
    
    if search:
        query = query.filter(
            or_(
                DedicationTemplate.title.contains(search),
                DedicationTemplate.content.contains(search)
            )
        )
    
    # 分页查询
    templates = query.order_by(DedicationTemplate.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('dedication/index.html', 
                         templates=templates.items,
                         pagination=templates,
                         search=search)
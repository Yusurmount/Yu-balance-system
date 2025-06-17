from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from functools import wraps
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.log import OperationLog
from app.forms.admin import LoginForm, UserForm, BalanceOperationForm, SettingsForm
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# 管理员登录验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录以访问该页面')
            return redirect(url_for('admin.login', next=request.url))
        if not hasattr(current_user, 'user_type') or current_user.user_type != 'admin':
            flash('请使用管理员账号登录')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    管理员登录路由
    """
    if current_user.is_authenticated and hasattr(current_user, 'user_type') and current_user.user_type == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        admin = User.query.filter_by(username=form.username.data, user_type='admin').first()
        if admin is None or not admin.check_password(form.password.data):
            flash('无效的管理员用户名或密码')
            return redirect(url_for('admin.login'))
        
        login_user(admin)
        # 记录登录日志
        log = OperationLog(action='管理员登录系统', admin_id=admin.id, admin_username=admin.username)
        db.session.add(log)
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('admin.dashboard'))
    
    return render_template('admin/login.html', title='后台登录', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    """
    管理员登出路由
    """
    # 记录登出日志
    if hasattr(current_user, 'id'):
        log = OperationLog(action='管理员登出系统', admin_id=current_user.id, admin_username=current_user.username)
        db.session.add(log)
        db.session.commit()
    
    logout_user()
    return redirect(url_for('index'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    管理员仪表盘，显示系统概览数据
    """
    total_users = User.query.count()
    total_balance = db.session.query(db.func.sum(User.balance)).scalar() or 0
    total_admins = User.query.filter_by(user_type='admin').count()
    recent_logs = OperationLog.query.order_by(OperationLog.timestamp.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          title='后台余额管理系统',
                          total_users=total_users,
                          total_balance=total_balance,
                          total_admins=total_admins,
                          current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          recent_logs=recent_logs)

@admin_bp.route('/users')
@admin_required
def user_list():
    """
    用户管理列表，支持分页、搜索和筛选
    """
    page = request.args.get('page', 1, type=int)
    per_page = 30
    
    # 搜索和筛选
    search_username = request.args.get('username', '')
    user_type = request.args.get('type', '')
    sort_by = request.args.get('sort', 'register_time')
    sort_order = request.args.get('order', 'desc')
    
    query = User.query
    
    if search_username:
        query = query.filter(User.username.like(f'%{search_username}%'))
    
    if user_type and user_type in ['user', 'admin']:
        query = query.filter(User.user_type == user_type)
    
    # 排序
    if sort_by == 'username':
        if sort_order == 'asc':
            query = query.order_by(User.username.asc())
        else:
            query = query.order_by(User.username.desc())
    else:
        if sort_order == 'asc':
            query = query.order_by(User.register_time.asc())
        else:
            query = query.order_by(User.register_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return render_template('admin/users.html', 
                          title='用户管理',
                          users=users,
                          pagination=pagination,
                          search_username=search_username,
                          user_type=user_type,
                          sort_by=sort_by,
                          sort_order=sort_order)

@admin_bp.route('/operations', methods=['GET', 'POST'])
@admin_required
def operations():
    """
    余额操作页面 - 处理充值、扣款和转账
    """
    form = BalanceOperationForm()
    if form.validate_on_submit():
        # 获取操作数据
        username = form.username.data
        operation_type = form.operation_type.data
        amount = form.amount.data
        target_user = form.target_user.data
        reason = form.reason.data
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f'用户 {username} 不存在')
            return redirect(url_for('admin.operations'))
        
        # 处理不同操作类型
        if operation_type == 'recharge':
            user.balance += amount
            action_desc = f'为用户 {username} 充值 {amount} 元'
        elif operation_type == 'deduct':
            if user.balance < amount:
                flash(f'用户 {username} 余额不足')
                return redirect(url_for('admin.operations'))
            user.balance -= amount
            action_desc = f'从用户 {username} 扣款 {amount} 元'
        elif operation_type == 'transfer':
            if not target_user:
                flash('请输入目标用户')
                return redirect(url_for('admin.operations'))
            target = User.query.filter_by(username=target_user).first()
            if not target:
                flash(f'目标用户 {target_user} 不存在')
                return redirect(url_for('admin.operations'))
            if user.balance < amount:
                flash(f'用户 {username} 余额不足')
                return redirect(url_for('admin.operations'))
            user.balance -= amount
            target.balance += amount
            action_desc = f'从用户 {username} 向 {target_user} 转账 {amount} 元'
        
        # 保存更改并记录日志
        db.session.commit()
        log = OperationLog(
            action=action_desc,
            admin_id=current_user.id,
            admin_username=current_user.username,
            user_id=user.id,
            user_username=user.username,
            amount=amount
        )
        db.session.add(log)
        db.session.commit()
        
        flash('操作成功完成')
        return redirect(url_for('admin.operations'))
    return render_template('admin/operations.html', title='余额操作', form=form)

@admin_bp.route('/logs')
@admin_required
def logs():
    """
    操作日志页面
    """
    logs = OperationLog.query.order_by(OperationLog.timestamp.desc()).all()
    return render_template('admin/logs.html', title='操作日志', logs=logs)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    """
    添加新用户
    """
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在')
            return redirect(url_for('admin.add_user'))
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # 记录操作日志
        log = OperationLog(action=f'添加新用户: {form.username.data}', admin_id=current_user.id, admin_username=current_user.username)
        db.session.add(log)
        db.session.commit()
        
        flash('用户添加成功')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/add_user.html', title='添加用户', form=form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """
    编辑用户信息
    """
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # 检查用户名是否已存在（排除当前用户）
        existing_user = User.query.filter(User.username == form.username.data, User.id != user_id).first()
        if existing_user:
            flash('用户名已存在')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # 更新用户信息
        user.username = form.username.data
        user.email = form.email.data
        user.user_type = form.user_type.data
        user.is_active = form.is_active.data
        
        # 如果提供了新密码，则更新密码
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        # 记录操作日志
        log = OperationLog(
            action=f'编辑用户: {user.username}', 
            admin_id=current_user.id, 
            admin_username=current_user.username,
            user_id=user.id,
            user_username=user.username
        )
        db.session.add(log)
        db.session.commit()
        
        flash('用户信息已更新')
        return redirect(url_for('admin.user_list'))
    
    return render_template('admin/edit_user.html', title='编辑用户', form=form, user=user)

@admin_bp.route('/users/toggle/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    """
    切换用户启用/停用状态
    """
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    status = '启用' if user.is_active else '停用'
    
    db.session.commit()
    
    # 记录操作日志
    log = OperationLog(
        action=f'{status}用户: {user.username}', 
        admin_id=current_user.id, 
        admin_username=current_user.username,
        user_id=user.id,
        user_username=user.username
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'用户已{status}')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """
    系统设置页面 - 加载并保存系统配置
    """
    import json
    import os
    from flask import current_app
    
    # 配置文件路径
    config_path = os.path.join(current_app.root_path, 'config.json')
    default_config = {'balance_unit': '元', 'balance_emoji': '💰'}
    
    # 加载现有配置
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            config = default_config
    else:
        config = default_config
    
    # 初始化表单
    form = SettingsForm(data=config)
    
    if form.validate_on_submit():
        # 保存新配置
        new_config = {
            'balance_unit': form.balance_unit.data,
            'balance_emoji': form.balance_emoji.data
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            flash('设置已成功保存', 'success')
        except IOError as e:
            flash(f'保存设置失败: {str(e)}', 'danger')
        
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', title='系统设置', form=form)
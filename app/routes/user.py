from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.forms.user import LoginForm

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录路由
    """
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码')
            return redirect(url_for('user.login'))
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('user.dashboard'))
    
    return render_template('user/login.html', title='用户登录', form=form)

@user_bp.route('/logout')
@login_required
def logout():
    """
    用户登出路由
    """
    logout_user()
    return redirect(url_for('index'))

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """
    用户仪表盘，显示余额信息
    """
    return render_template('user/dashboard.html', title='余额系统', user=current_user)
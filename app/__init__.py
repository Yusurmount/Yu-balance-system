import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import dotenv

dotenv.load_dotenv()

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap()
csrf = CSRFProtect()

# 配置登录视图
login_manager.login_view = 'user.login'
login_manager.login_message = '请先登录以访问该页面'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    # 加载用户并根据类型区分
    user = User.query.get(int(user_id))
    return user


def create_app():
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_for_testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///balance_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    csrf.init_app(app)
    
    # 注册蓝图
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 主页路由
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app
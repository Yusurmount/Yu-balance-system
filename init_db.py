from app import create_app, db
from app.models.user import User
from app.models.log import OperationLog
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 创建所有数据库表
    db.create_all()
    
    # 检查是否已有管理员账户
    admin = User.query.filter_by(username='admin', user_type='admin').first()
    
    if not admin:
        # 创建默认管理员账户
        admin = User(
                username='admin',
                email='admin@example.com',
                user_type='admin',
                balance=0.0
            )
        admin.set_password('admin123')  # 默认密码
        db.session.add(admin)
        db.session.commit()
        print('默认管理员账户已创建: 用户名=admin, 密码=admin123')
    else:
        print('管理员账户已存在')
    
    print('数据库初始化完成')
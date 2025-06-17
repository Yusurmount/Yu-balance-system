from datetime import datetime
from app import db

class OperationLog(db.Model):
    """
    操作日志模型，记录管理员的所有操作
    """
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_username = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_username = db.Column(db.String(64), nullable=True)
    amount = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<OperationLog {self.action} by {self.admin_username} at {self.timestamp}>'
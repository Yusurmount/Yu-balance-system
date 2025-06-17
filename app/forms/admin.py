from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, EqualTo
from datetime import datetime

class LoginForm(FlaskForm):
    """
    管理员登录表单
    """
    username = StringField('管理员用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class UserForm(FlaskForm):
    """
    用户添加/编辑表单
    """
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('邮箱', validators=[Optional(), Email(), Length(0, 120)])
    password = PasswordField('密码', validators=[Optional()])
    confirm_password = PasswordField('确认密码', validators=[EqualTo('password', message='密码必须匹配')])
    balance = FloatField('初始余额', validators=[Optional(), NumberRange(min=0)])
    user_type = SelectField('用户类型', choices=[('user', '普通用户'), ('admin', '管理员')], default='user')
    is_active = BooleanField('启用账号', default=True)
    submit = SubmitField('保存')

class BalanceOperationForm(FlaskForm):
    """
    余额操作表单（充值/扣款/转账）
    """
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    operation_type = SelectField('操作类型', choices=[('recharge', '充值'), ('deduct', '扣款'), ('transfer', '转账')], validators=[DataRequired()])
    amount = FloatField('金额', validators=[DataRequired(), NumberRange(min=0.01)])
    target_user = StringField('目标用户', validators=[Optional(), Length(1, 64)])  # 仅转账时需要
    reason = TextAreaField('操作原因', validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField('执行操作')

class SettingsForm(FlaskForm):
    """
    系统设置表单
    """
    balance_unit = StringField('余额单位', validators=[DataRequired(), Length(1, 10)], default='元')
    balance_emoji = StringField('余额图标(Emoji)', validators=[Optional(), Length(1, 2)], default='💰')
    submit = SubmitField('保存设置')
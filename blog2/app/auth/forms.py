#coding:utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from flask.ext.wtf import Form 
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import Required,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(Form):
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('密码',validators=[Required()])
    remember_me=BooleanField('记住我')
    submit=SubmitField('登录')

class RegistrationForm(Form):
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    username=StringField('用户名',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,"用户名必须是字母，数字，下划线和点")])
    password=PasswordField('密码',validators=[Required(),Length(1,64),EqualTo('password2',message='密码不一致')])
    password2=PasswordField('确认密码',validators=[Required()])
    submit=SubmitField('注册')

    def validate_email(self,field):#表单类中定义了以validate_开头且后面跟着字段名的方法，者个方法就和常规到验证函数一起调用
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("该邮箱已经注册")

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')

class ChangePasswordForm(Form):
    old_password=PasswordField("旧密码",validators=[Required()])
    password=PasswordField('新密码',validators=[Required(),EqualTo('password2',message='密码不匹配')])
    password2=PasswordField('确认新密码',validators=[Required()])
    submit=SubmitField('更新密码')

class PasswordResetRequestForm(Form):
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    submit=SubmitField('重置密码')

class PasswordResetForm(Form):
    email=StringField('邮箱',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('新密码',validators=[Required(),EqualTo('password2',message='密码不匹配')])
    password2=PasswordField('确认新密码',validators=[Required()])
    submit=SubmitField('重置密码')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError("该邮箱不存在！")
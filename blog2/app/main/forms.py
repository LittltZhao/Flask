# coding:utf-8
import os,sys
reload(sys)
sys.setdefaultencoding('utf8')

from flask.ext.wtf import Form 
from wtforms import StringField,SubmitField,TextAreaField,SelectField, BooleanField
from wtforms.validators import Required,Length,Regexp
from ..models import Role,User,Blogtype
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField


class NameForm(Form):
    name=StringField("名字",validators=[Required()])
    submit=SubmitField('提交')

class EditProfileForm(Form):
    name=StringField("真实姓名",validators=[Length(0,64)])
    location=StringField('地址',validators=[Length(0,64)])
    about_me=TextAreaField("关于我")
    submit=SubmitField("提交")

class EditProfileAdminForm(Form):#管理员表单
    email=StringField('邮箱',validators=[Required()])
    username=StringField('用户名',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                                        '用户名必须是字母数字下划线或者点')])
    confirmed=BooleanField('确认用户')
    role=SelectField('Role',coerce=int)#choices列表再表单的构造函数中设定，其值从Role模型获取
    name=StringField('姓名',validators=[Length(0,64)])#coerce=int将字段的值设置为整数，不使用默认的字符串
    location=StringField('地址',validators=[Length(0,64)])
    about_me=TextAreaField("关于我")
    submit=SubmitField("提交")

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices=[(role.id,role.name) for role in Role.query.order_by(Role.name).all()]#初始化函数中对SelectField中的choices进行赋值
        self.user=user 

    def validate_email(self,field):
        if field.data!=self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱早已存在！')

    def validate_username(self,field):
        if field.data!=self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError("用户名已存在！")

class PostForm(Form):#提交博客文章表单
    tag=SelectField("博客类型",coerce=int)
    title=StringField('标题:',validators=[Required()])
    body=PageDownField("正文",validators=[Required()])#转换为markdown富文本编辑器
    submit=SubmitField('发布')

    def __init__(self,*args,**kwargs):
        super(PostForm,self).__init__(*args,**kwargs)
        self.tag.choices=[(tag.id,tag.name)  for tag in Blogtype.query.order_by(Blogtype.name).all()]

class CommentForm(Form):
    body=TextAreaField('',validators=[Required()])
    submit=SubmitField('提交')
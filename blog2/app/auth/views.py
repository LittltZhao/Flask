#coding:utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from flask import render_template,redirect,request,url_for,flash
from flask.ext.login import login_user,logout_user,login_required,current_user
from . import auth
from .. import db
from ..models import User 
from ..email import send_email
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,\
                                    PasswordResetRequestForm,PasswordResetForm

@auth.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):#验证登录
            login_user(user,form.remember_me.data)#登录,remember_me.data为可选项，是否记住登录状态，记住则写入一个长期到cookie
            return redirect(request.args.get('next') or url_for('main.user',username=user.username))#'next'参数保存原页面到地址，可以在request.args中获取
        flash('用户名或密码错误')
    return render_template('auth/login.html',form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()#删除并重设用户会话
    flash("您已经退出")
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form=RegistrationForm()
    if form.validate_on_submit():
        user=User(email=form.email.data,
                            username=form.username.data,
                            password=form.password.data)#创建用户提交密码，将密码直接转换为散列值存储
                                                                                # self.password_hash=generate_password_hash(password)
        db.session.add(user)
        db.session.commit()#提交数据之后才能赋予新用户id值，因此不能延迟提交
        token=user.generate_confirmation_token()
        send_email(user.email,'确认账户','auth/email/confirm',user=user,token=token)
        flash("一封确认邮件已经发送至您的邮箱，清注意查收")
        return redirect(url_for('main.index'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required#flask-login 提供的修饰器，要求登录用户才能进行此操作
def confirm(token):#确认邮件中有包含本方法到链接
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash("您已经完成验证账户，谢谢！")
    else:
        flash("确认链接无效")
    return redirect(url_for('main.index'))

@auth.before_app_request#登录但还未确认的用户，指向未确认页面unconfirmed
def before_request():
    if current_user.is_authenticated:
        current_user.ping()#更新最新登录时间
        if not current_user.confirmed and request.endpoint[:5]!='auth.':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=current_user.generate_confirmation_token()#current_user为已经登录的用户，也是目标用户
    send_email(current_user.email,'确认账户','auth/email/confirm',user=current_user,token=token )
    flash("一封新确认邮件已发送至您的邮箱")
    return redirect(url_for('main.index'))

@auth.route('/change-password',methods=['GET','POST'])
@login_required#不是auth.login_required
def change_password():
    form=ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password=form.password.data
            db.session.add(current_user)
            flash("密码修改成功")
            return redirect(url_for("main.index"))
        else:
            flash("原密码错误！")
    return render_template('auth/change_password.html',form=form)

@auth.route('/reset',methods=['GET','POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form=PasswordResetRequestForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            token=user.generate_reset_token()
            send_email(user.email,"重置密码",'auth/email/reset_password',
                        user=user,token=token,next=request.args.get("next"))
        flash("重置密码的邮件已经发送至您的邮箱")
        return redirect(url_for("auth.login"))
    return render_template('auth/reset_password.html',form=form)


@auth.route('/reset/<token>',methods=['GET','POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form=PasswordResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for("main.index"))
        if user.reset_password(token,form.password.data):
            flash("您的密码已找回")
            return redirect(url_for("auth.login"))
        else:
            return redirect(url_for("main.index"))
    return render_template("auth/reset_password.html",form=form)
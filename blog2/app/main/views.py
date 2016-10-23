# coding: utf-8
import os,sys
reload(sys)
sys.setdefaultencoding('utf8')

from flask import render_template, session, redirect, url_for,current_app,\
abort,flash,request,current_app,make_response
from datetime import datetime
from . import main
from  .forms import NameForm,EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import User,Role,Post,Permission,Follow,Comment,Blogtype
from ..email import send_email
from flask.ext.login import login_required,current_user
from ..decorators import admin_required,permission_required


@main.route('/')#路由修饰器由蓝本提供
def index():
    page=request.args.get('page',1,type=int)#渲染的页数从请求的查询字符串中获取
    pagination=Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASK_POST_PER_PAGE'],error_out=False)
    posts=pagination.items
    return render_template('index.html',posts=posts, pagination=pagination)


@main.route('/blog/edit',methods=['GET','POST'])
@login_required
def create_blog():#创建博客
    form=PostForm()
    if form.validate_on_submit():
        post=Post(tag=Blogtype.query.get(form.tag.data),body=form.body.data,title=form.title.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    return render_template('edit_blog.html',form=form)


@main.route('/blogtype/<username>/<int:id>')#博客分类
def blogtype(id,username):
    user=User.query.filter_by(username=username).first_or_404()
    posts=user.posts.filter_by(tag_id=id).all()
    return render_template("blogtype.html",posts=posts)
    # pagination=user.posts.filter_by(tag_id=id).all().paginate(
    #     page,per_page=current_app.config['FLASK_POST_PER_PAGE'],error_out=False)
    # posts=pagination.items
    # return render_template("blogtype.html",posts=posts,pagination=pagination)

@main.route('/user/<username>')
def user(username):#用户博客目录页面
    user=User.query.filter_by(username=username).first_or_404()
    page=request.args.get('page',1,type=int)
    pagination=user.posts.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASK_POST_PER_PAGE'],error_out=False)
    posts=pagination.items
    return render_template("user.html",user=user,posts=posts,pagination=pagination)


@main.route('/information/<username>')
@login_required
def inf(username):#用户信息页面
    user=User.query.filter_by(username=username).first_or_404()
    return render_template("information.html",user=user)

@main.route('/delete/<username>/<int:id>')
def delete(id,username):#删除文章
    post=Post.query.get_or_404(id)
    if post:
        db.session.delete(post)#删除记录
        db.session.commit()
        flash("文章已删除")
        return redirect(url_for('.user',username=username))





@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():#编辑个人信息
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)#sudo su进入root权限    设置mysql编码为utf8
        flash("您的资料已修改")
        return redirect(url_for('main.user',username=current_user.username))
    form.name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template("edit_profile.html",form=form)

@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):#管理员编辑个人信息
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)
        user.name=form.name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)
        flash("信息已更改")
        return redirect(url_for('.user',username=user.username))
    form.email.data=user.email
    form.username.data=user.email
    form.confirmed.data= user.confirmed
    form.role.data=user.role_id
    form.name.data=user.name
    form.location.data=user.location
    form.about_me.data=user.about_me
    return render_template('edit_profile.html',form=form,user=user)

@main.route("/post/<int:id>",methods=['GET','POST'])#有form就有method
def post(id):#页面永久链接    评论要显示在单篇博客文章页面中
    post=Post.query.get_or_404(id)
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data,post=post,author=current_user._get_current_object())
        db.session.add(comment)#评论的 author字段也不能直接设为 current_user ,因为这个变量是上下文代理对象
        flash("您的评论已提交！")
        return redirect(url_for('.post',id=post.id,page=-1))#用来请求评论的最后一页
    page=request.args.get('page',1,type=int)
    if page==-1:
        page=(post.comments.count()-1)/current_app.config['FLASK_COMMENTS_PER_PAGE']+1
    pagination=post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FLASK_COMMENTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination)

@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):#编辑文章
    post=Post.query.get_or_404(id)
    if current_user!=post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form =PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        post.title=form.title.data
        post.tag=Blogtype.query.get(form.tag.data)#重新提交博客分类
        db.session.add(post)
        flash('文章已更改')
        return redirect(url_for('.post',id=post.id))
    form.body.data=post.body
    form.title.data=post.title
    form.tag.data=post.tag_id
    return render_template('edit_post.html',form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):#关注
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash('此用户不存在！')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('您已经关注了该用户！')
        return redirect(url_for('.user',username=username))
    current_user.follow(user)
    flash('您现在正在关注 %s' %username)
    return redirect(url_for('.user',username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):#取消关注
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('I该用户不存在')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('您没有关注该用户！')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('您正在取消关注%s ' % username)
    return redirect(url_for('.user', username=username))

@main.route('/followers/<username>')
def followers(username):#关注的人
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('该用户不存在！')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="关注我的人",
                           endpoint='.followers', pagination=pagination,follows=follows)

@main.route('/followed-by/<username>')
def followed_by(username):#被关注的人
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('该用户不存在！')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="我关注的人",
                           endpoint='.followed_by', pagination=pagination,follows=follows)

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page=request.args.get('page',1,type=int)
    pagination=Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASK_COMMENTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination,page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=False
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=True
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))














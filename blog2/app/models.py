#coding:utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from . import db,login_manager
from werkzeug.security import generate_password_hash,check_password_hash
from flask.ext.login import UserMixin,AnonymousUserMixin#UserMixin类包含用户认证方法到默认实现：is_authenticated()，is_active()，is_anonymous()，get_id()
from itsdangerous import  TimedJSONWebSignatureSerializer as Serializer 
from flask import current_app,request
from datetime import datetime
import hashlib
import bleach
from markdown import markdown

class Permission:
    FOLLOW=0x01#关注
    COMMENT=0x02#评论
    WRITE_ARTICLES=0x04#写文章
    MODERATE_COMMENTS=0x08#管理评论
    ADMINISTER=0x80#管理员

class Follow(db.Model):#关注关联表 把这个多对多关系的左右两侧拆分成两个基本的一对多关系
    __tablename__="follows"
    follower_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)

class Role(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)#permissions不同的值代表不同的权限
    users=db.relationship('User',backref='role',lazy='dynamic')

    @staticmethod#创建三种用户角色
    def insert_roles():#先查找角色，如果不存在则创建新角色
        roles={
        'User':(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES,True),#0x07
        'Moderator':(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|Permission.MODERATE_COMMENTS,False),#0x0f
        'Administrator':(0xff,False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()
    

    def __repr__(self):
        return "<Role %s>" % self.name



class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username=db.Column(db.String(64),unique=True,index=True)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    password_hash=db.Column(db.String(128))
    confirmed=db.Column(db.Boolean,default=False)
    name=db.Column(db.String(64))#用户信息用户的真实姓名
    location=db.Column(db.String(64))#所在地
    about_me=db.Column(db.Text())#自我介绍
    member_since=db.Column(db.DateTime,default=datetime.utcnow)#注册日期,default参数可以接受函数为默认值，故utcnow后面没有括号
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)#最后访问日期
    avatar_hash=db.Column(db.String(32))
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    followed=db.relationship('Follow',
                                                foreign_keys=[Follow.follower_id],
                                                backref=db.backref('follower',lazy='joined'),#lazy="joined"可以再一次数据库查询中完成所有操作
                                                lazy="dynamic",
                                                cascade='all,delete-orphan')
    followers=db.relationship('Follow',
                                                    foreign_keys=[Follow.followed_id],
                                                    backref=db.backref('followed',lazy='joined'),
                                                    lazy="dynamic",
                                                    cascade='all,delete-orphan')#启用所有默认层叠选项,而且还要删除孤儿记录。
    comments=db.relationship('Comment',backref='author',lazy='dynamic')

    @property#将password当属性使用，可以直接赋值
    def password(self):
        raise AttributeError('密码不可读取')

    @password.setter
    def password(self,password):#赋值时将传递进来的通过散列值函数产生散列值并保存到数据库
        self.password_hash=generate_password_hash(password)#产生密码散列值，不同用户同一密码散列值不同

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)#验证密码


    #确认用户函数 generate_confirmation_token(）  confirm()。确认链接http://www.example.com/auth/confirm/<id>。将id转换成令牌进行确认
    def generate_confirmation_token(self,expiration=3600):#生成一个令牌，有效期默认为一个小时
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})#dumps为指定数据生成加密签名，然后对数据和签名进行序列化产生令牌字符串

    def confirm(self,token):#验证签名
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)#检验签名和过期时间
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        return True 

    def generate_reset_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self,token,new_password):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('reset')!=self.id:
            return False
        self.password=new_password
        db.session.add(self)
        return True

    def __init__(self,**kwargs):#为用户创建角色
        super(User,self).__init__(**kwargs)#父类构造
        if self.role is None:
            if self.email==current_app.config['FLASK_ADMIN']:#有FLASK_ADMIN邮箱的创建为管理员
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role=Role.query.filter_by(default=True).first()#其余默认创建为一般用户
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash=hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))#自我关注，显示关注用户的文章时也显示自己的文章

    def can(self,permissions):#检查用户是否有指定权限，通过permissions来进行指定
        return self.role is not None and (self.role.permissions&permissions)==permissions

    def is_administrator(self):#调用can()来判定管理员权限
        return self.can(Permission.ADMINISTER)

    def ping(self):#刷新用户最后的访问时间
        self.last_seen=datetime.utcnow()
        db.session.add(self)

    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url='https://secure.gravatar.com/avatar'
        else:
            url='http://www.gravatar.com/avatar'
        hash=self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url,hash=hash,size=size,default=default,rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed 
        import forgery_py
        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
                    username=forgery_py.internet.user_name(True),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    name=forgery_py.name.full_name(),
                    location=forgery_py.address.city(),
                    about_me=forgery_py.lorem_ipsum.sentence(),
                    member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def follow(self,user):#关注？？？？？
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)

    def unfollow(self,user):#取消关注
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self,user):#是否关注user
        return self.followed.filter_by(followed_id=user.id
            ).first() is not None 

    def is_followed_by(self,user):#是否被user关注
        return self.followers.filter_by(followers_id=user.id).first() is not None 


    @staticmethod
    def add_self_follows():#自己关注自己
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    

    def __repr__(self):
        return "<User %s>" % self.username

class AnonymouUser(AnonymousUserMixin):#不用先检查用户是否登录，就可以自动调用current_user.can()
                                                                                #和current_user.is_adminstrator()
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user=AnonymouUser



class Blogtype(db.Model):#博客类型模型
    __tablename__='blogtype'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    post=db.relationship('Post',backref='tag',lazy='dynamic')

    @staticmethod
    def insert_blogtype():
        types=["闲话日常","学习笔记","神秘学","转载文章"]
        for t in types:
            typ=Blogtype.query.filter_by(name=t).first()
            if typ is None:
                typ=Blogtype(name=t)
            db.session.add(typ)
        db.session.commit()

    def __repr__(self):
        return "<Blogtype %s>" % self.name


class Post(db.Model):#提交博客
    __tablename__="posts"
    id=db.Column(db.Integer,primary_key=True)
    tag_id=db.Column(db.Integer,db.ForeignKey('blogtype.id'))
    title=db.Column(db.String(256))
    body=db.Column(db.Text)
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    comments=db.relationship('Comment',backref='post',lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py
        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0,user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                timestamp=forgery_py.date.date(True),
                author=u)
            db.session.add(p)
            db.session.commit()
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a', 'abbr', 'acronym', 'b', 'blockquote', 'code','em', 'i', 'li', 'ol', 'pre', 'strong', 'ul','h1', 'h2', 'h3', 'p']
        target.body_html=bleach.linkify(bleach.clean(
            markdown(value,output_form='html'),tags=allowed_tags,strip=True))
    def __repr__(self):
        return "<Post %s>" % self.title
db.event.listen(Post.body,'set',Post.on_changed_body)

class Comment(db.Model):
    __tablename__="comments"
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled=db.Column(db.Boolean)#协管员通过这个字段查禁不当评论
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_is=db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a', 'abbr', 'acronym', 'b', 'code','em', 'i',  'strong']
        target.body_html=bleach.linkify(bleach.clean(
            markdown(value,output_form='html'),tags=allowed_tags,strip=True))
db.event.listen(Comment.body,'set',Comment.on_changed_body)





        


@login_manager.user_loader      #加载用户到回调函数，使用指定的标识符加载用户
def load_user(user_id):
    return User.query.get(int(user_id))
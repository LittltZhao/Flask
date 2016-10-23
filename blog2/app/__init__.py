# coding:utf-8
from flask import Flask,render_template
from flask.ext.bootstrap import Bootstrap 
from flask.ext.mail import Mail 
from flask.ext.moment import Moment 
from flask.ext.sqlalchemy import SQLAlchemy 
from config import config
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown 

bootstrap=Bootstrap()
mail=Mail()
moment=Moment()
db=SQLAlchemy()
pagedown=PageDown()#markdown

login_manager=LoginManager()
login_manager.session_protection="strong"#可设置为None,'basic','strong'提供不同安全等级
login_manager.login_view='auth.login'#设置登录页面的端点，在auth蓝本中定义，因此要加auth.


def create_app(config_name):#程序工厂函数，参数为配置参数，可以创建不同配置的程序（动态配置）
    app=Flask(__name__)
    app.config.from_object(config[config_name])#from_object()从config中直接导入配置
    config[config_name].init_app(app)#初始化配置

    bootstrap.init_app(app)#扩展自带init_app()方法
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)#注册蓝本，路由才成为程序的一部分

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix="/auth")#注册后蓝本中定义到路由都会加上指定前缀

    return app
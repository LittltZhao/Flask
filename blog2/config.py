# coding: utf-8
import os,sys
reload(sys)
sys.setdefaultencoding('utf8')

class Config:
    SECRET_KEY=os.environ.get('SECRET_KEY') or "hard to gues string"#跨站请求伪造（CSRF）保护密钥 flask-wtf
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True#True每次请求结束后都会自动提交数据库中的变动
    MAIL_SERVER='smtp.qq.com'
    MAIL_PORT=465
    MAIL_USE_SSL=True#安全套接层协议
    # MAIL_USE_TLS = True#安全传输层协议
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME')#从环境中导入帐号密码 export MAIL_USERNAME='自己的帐号'
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')
    FLASK_MAIL_SUBJECT_PREFIX='[ 曲径通幽 ]'#邮件主题
    FLASK_MAIL_SENDER='曲径通幽 <694104630@qq.com>'
    FLASK_ADMIN=os.environ.get('FLASK_ADMIN')#接收邮件
    FLASK_POST_PER_PAGE=20
    FLASK_FOLLOWERS_PER_PAGE=20
    FLASK_COMMENTS_PER_PAGE=20

    @staticmethod#类方法应当只被类调用，实例方法实例调用，静态方法两者都能调用。
    def init_app(app):#参数为程序实例，通过使用该方法可以使当前配置初始化
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or \
                                                    "mysql://root:root@localhost/flask_dev"         #连接mysql 数据库 
                                                    #第一个root为用户名,第二个root为密码，flask_dev为数据库名称

class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI=os.environ.get('TEST_DATABASE_URL') or \
                                                    "mysql://root:root@localhost/flask_test"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or \
                                                    "myslq://root:root@localhost/flask"


config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopmentConfig
}
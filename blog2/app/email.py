#coding:utf-8
from threading import Thread 
from flask import current_app,render_template
from flask.ext.mail import Message
from . import mail
#current_app:指向正在处理请求的应用。这对于想要支持同时运行多个应用的扩展有用。 
#它由应用上下文驱动，而不是请求上下文，所以你可以用 app_context() 方法修改这个代理的值。
def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)


def send_email(to,subject,template,**kwargs):
    app=current_app._get_current_object()#current_app是代理，如果需要访问潜在到被代理对象，使用_get_current_object()方法
    msg=Message(app.config['FLASK_MAIL_SUBJECT_PREFIX']+' '+subject,
        sender=app.config['FLASK_MAIL_SENDER'],recipients=[to])
    msg.body=render_template(template+'.txt',**kwargs)
    msg.html=render_template(template+'.html',**kwargs)
    thr=Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr
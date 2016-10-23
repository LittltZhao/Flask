# coding:utf-8
#在蓝本中定义到路由处于休眠状态，直到蓝本注册到程序上后，路由才真正成为程序的一部分
#蓝本创建再main子包到构造文件中
from flask import Blueprint
from ..models import Permission
main=Blueprint('main',__name__)#实例化蓝本程序，main为蓝本的名字。两个参数：蓝本名字和蓝本所在到包或模块。

@main.app_context_processor#模板中检查权限，为了调用render_template减少一个参数，使用上下文管理器，让变量在所有模板中全局访问
def inject_permissions():
    return dict(Permission=Permission)

from . import views,errors#将views,errors和蓝本进行关联，末尾导入避免循环导入依赖
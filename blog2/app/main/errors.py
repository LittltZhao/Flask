# coding:utf-8
from flask import render_template
from . import main

@main.app_errorhandler(404)#若使用errorhandler则只有蓝本中到错误才能触发程序，要注册全局到错误处理程序，则必须使用app_errorhandler
def page_not_found(e):
    return render_template('404.html'),404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500
#coding:utf-8
from flask import Blueprint

auth=Blueprint('auth',__name__)#不同的程序功能要使用不同到蓝本

from . import views
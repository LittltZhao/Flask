# coding:utf-8
import os,sys
reload(sys)
sys.setdefaultencoding('utf8')
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from models import Permission

def permission_required(permission):#带参数的修饰器
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decorator

def admin_required(f):#管理员修饰器
    return permission_required(Permission.ADMINISTER)(f)
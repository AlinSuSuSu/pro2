#用户认证系统相关的路由蓝本
from flask import  Blueprint

auth = Blueprint('auth', __name__)

from . import views

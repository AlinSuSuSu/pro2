#用户认证系统香瓜的路由蓝本
from flask import  Blueprint

auth = Blueprint('auth', __name__)

from . import views

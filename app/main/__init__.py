'''蓝本中实现程序功能'''
from flask import Blueprint

main = Blueprint('main',__name__)

from . import  views,errors

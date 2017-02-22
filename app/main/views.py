#蓝本中定义的程序路由

from datetime import  datetime
from flask import render_template,session,redirect,url_for

from . import main
#from . forms import NameForm
from .. import db
#from ..models import User


@main.route('/',methods = ['GET','POST'])
def index():
    #form = NameForm
    return render_template('index.html')
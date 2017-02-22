'''程序包的构造文件'''

from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config


bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()

#工厂函数
def create_app(config_name):
    from .main import main as main_blueprint
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.register_blueprint(main_blueprint)
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    #附加路由和自定义的错误页面

    return app
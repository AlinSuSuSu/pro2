#在User模型中加入密码散列
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import  UserMixin, AnonymousUserMixin
from . import login_manager
from . import db


class Permission:
    FOLLOW = 0x01
    COMMIT = 0X02
    WRITE_ARTICLE =0x04
    MODERATE_COMMITS=0x08
    ADMINISTER=0x80


#加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean,default= False,index=True)
    permissions = db.Column(db.Integer)

    #创建角色
    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.FOLLOW|
                    Permission.COMMIT|
                    Permission.WRITE_ARTICLE,True),
            'Moderator':(Permission.FOLLOW|
                         Permission.COMMIT|
                         Permission.WRITE_ARTICLE|
                         Permission.MODERATE_COMMITS,False),
            'Adminstrator':(0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name = r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname=db.Column(db.String(64),unique= True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    def verify_password(self,password):
         return check_password_hash(self.password_hash, password)

    #定义默认角色
    def __int__(self,**kwargs):
        super(User, self).__int__(**kwargs)
        if self.role is None:
            if self.nickname == 'admin':
                self.role = Role.query.filter_by(permission=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
    #检查用户是否有指定的权限
    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)



    def __repr__(self):
        return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_adminstrator(self):
        return False

login_manager.anonymous_user=AnonymousUser
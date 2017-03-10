#在User模型中加入密码散列
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import  UserMixin, AnonymousUserMixin
from . import login_manager
from . import db
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,url_for
from markdown import markdown
from app.exceptions import ValidationError
import bleach

class Permission:
    FOLLOW = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES =0x04
    MODERATE_COMMENTS=0x08
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
                    Permission.COMMENT|
                    Permission.WRITE_ARTICLES,True),
            'Moderator':(Permission.FOLLOW|
                         Permission.COMMENT|
                         Permission.WRITE_ARTICLES|
                         Permission.MODERATE_COMMENTS,False),
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

class Follow(db.Model):
    __tablename__='follows'
    follower_id =db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id =db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)


class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(64),unique=True,index=True)
    nickname=db.Column(db.String(64),unique= True,index=True)
    username = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
    confirmed = db.Column(db.Boolean,default=True)
    posts = db.relationship('Post',backref='author',lazy='dynamic')
    followed = db.relationship('Follow',foreign_keys=[Follow.follower_id],backref=db.backref('follower',lazy="joined"),lazy="dynamic",cascade="all,delete-orphan")
    followers = db.relationship('Follow',foreign_keys=[Follow.followed_id],backref=db.backref('followed',lazy="joined"),lazy="dynamic",cascade="all,delete-orphan")


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    def verify_password(self,password):
         return check_password_hash(self.password_hash, password)

    #定义默认角色
    def __init__(self,**kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.nickname == 'admin':
                self.role = Role.query.filter_by(permissions=0xff).first()

            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    #检查用户是否有指定的权限
    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 刷新用户的最后访问时间,每次用户请求时都要调用ping()方法。
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    ##确认用户
    # 生成令牌，有效时间一个小时
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

        # 检查令牌中的id是否和存储在current_user中的已登录用户匹配
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        seed()
        for i in range(count):
            u = User(email =forgery_py.internet.email_address(),
                     nickname=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     username=forgery_py.name.full_name(),
                     location = forgery_py.address.city(),
                     member_since = forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


    def follow(self,user):
        if not self.is_following(user):
            f = Follow(follower=self,followed=user)
            db.session.add(f)
    def unfollow(self,user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).first() is not None
    def is_followed_by(self,user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def to_json(self):
        json_user={
            'url':url_for('api.get_user',id = self.id,_external=True),
            'username':self.username,
            'member_since':self.member_since,
            'last_seen':self.last_seen,
            'posts':url_for('api.get_user_posts',id=self.id,_external=True),
            'followed_posts':url_for('api.get_user_followed_posts',id=self.id,_external=True),
            'post_count':self.posts.count()
        }
        return json_user


    #支持基于令牌的认证
    def generate_auth_token(self,expiration):
        s =Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id':self.id})
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)


    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_adminstrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

class Post(db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0,user_count-1)).first()
            p =Post(body=forgery_py.lorem_ipsum.sentence(),
                    timestamp=forgery_py.date.date(True),
                    author=u)
            db.session.add(p)
            db.session.commit()
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','blockquote','code','em','i','li','ol','pre','strong','ul','h1','h2','h3','p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))

    def to_json(self):
        json_post={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True),

        }
        return json_post
    #从JSON格式数据创建一篇博客文章
    @staticmethod
    def from_json(json_post):
        body=json_post.get('body')
        if body is None or body =='':
            raise ValidationError('post does not have a body')
        return Post(body=body)

db.event.listen(Post.body,'set',Post.on_changed_body)


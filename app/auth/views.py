#蓝本中的路由和视图函数
from flask import render_template, redirect,request,url_for,flash
from . import auth
from flask_login import login_user,logout_user,login_required,current_user,UserMixin
from ..models import User,Role
from . forms import LoginForm,ChangePasswordForm
from . forms import RegistrationForm
from app import db


@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(nickname=form.nickname.data).first()
        if user is not None and user.verify_password((form.password.data)):
            login_user(user,form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html',form = form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(nickname=form.nickname.data,username = form.nickname.data,

                    password=form.password.data)
        if form.nickname.data == 'admin':
            user.role_id = 2

        db.session.add(user)
        flash('You can now login.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/change-password',methods = ['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.ad(current_user)
            flash("your password has been updated")
            return redirect(url_for('main.index'))
        else:
            flash('Invalidate password')
    return render_template('auth/change_password.html', form = form)

#更新已登录用户的访问时间
@auth.before_app_request
def befor_request():
    if current_user.is_authenticated:
        current_user.ping()

#蓝本中的路由和视图函数
from flask import render_template, redirect,request,url_for,flash
from . import auth
from flask_login import login_user,logout_user,login_required,current_user,UserMixin
from ..models import User,Role
from . forms import LoginForm,ChangePasswordForm
from . forms import RegistrationForm
from app import db
from ..sendemail import send_email

@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
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
        user = User(email=form.email.data,nickname=form.nickname.data,username = form.nickname.data,

                    password=form.password.data)

        db.session.add(user)
        db.session.commit()
        token =user.generate_confirmation_token()
        send_email(user.email,'Confirm your accout','auth/email/confirm',user=user,token=token)
        flash('A confirmation email has been sent to you by email')
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
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))



#过滤未确认的用户
@auth.before_app_request
def befor_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.'\
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
         return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

#确认用户的账户
@auth.route('confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('you have confirmed your account,thanks!')
    else:
        flash("the confirmation link is invalid or has expired.")
    return redirect(url_for('main.index'))

#重新发送账户确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,'confirm your account','auth/email/confirm',user=current_user,token=token)
    flash('a new confirmation email has been sent to you by email')
    return redirect(url_for('main.index'))
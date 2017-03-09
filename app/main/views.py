#蓝本中定义的程序路由

from datetime import  datetime
from flask import render_template,session,redirect,make_response,url_for,flash,request,current_app
from flask_login import login_required,current_user
from . import main
from . forms import NameForm,PostForm,EditProfileForm,EditProfileAdminForm
from .. import db
from ..decorators import admin_required,permission_required
from ..models import User,Role,Permission,Post
from flask import abort


@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html',form=form, posts=posts, show_followed=show_followed,pagination=pagination)
    #posts =Post.query.order_by(Post.timestamp.desc()).all()
    #return render_template('index.html',form =form,posts=posts)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/user/<nickname>')
def user(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config[
        'FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,pagination=pagination)

@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.location = form.location.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', nickname=current_user.nickname))
    form.username.data = current_user.username
    form.location.data = current_user.location
    return render_template('edit_profile.html', form=form)


@main.route('/mod1')
def mod1():
    return render_template('mod1.html')


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.nickname = form.nickname.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.username = form.username.data
        user.location = form.location.data
        #user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', nickname=user.nickname))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.nickname.data = user.nickname
    form.location.data = user.location
    #form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>')
def post(id):
    post=Post.query.get_or_404(id)
    return render_template('post.html',posts=[post])

@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@main.route('/follow/<nickname>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash("Invalid user")
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash("you are already following this user")
        return redirect(url_for('.user',nickname=nickname))
    current_user.follow(user)
    flash("you are now following %s" % nickname)
    return redirect(url_for('.user',nickname=nickname))


@main.route('/unfollow/<nickname>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(nickname):
     user = User.query.filter_by(nickname=nickname).first()
     if user is None:
         flash('Invalid user.')
         return redirect(url_for('.index'))
     if not current_user.is_following(user):
         flash('You are not following this user.')
         return redirect(url_for('.user', nickname=nickname))
     current_user.unfollow(user)
     flash('You are not following %s anymore.' % nickname)
     return redirect(url_for('.user', nickname=nickname))
 
 
@main.route('/followers/<nickname>')
def followers(nickname):
     user = User.query.filter_by(nickname=nickname).first()
     if user is None:
         flash('Invalid user.')
         return redirect(url_for('.index'))
     page = request.args.get('page', 1, type=int)
     pagination = user.followers.paginate(
         page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
         error_out=False)
     follows = [{'user': item.follower, 'timestamp': item.timestamp}
                for item in pagination.items]
     return render_template('followers.html', user=user, title="Followers of",
                            endpoint='.followers', pagination=pagination,
                            follows=follows)
 
 
@main.route('/followed-by/<nickname>')
def followed_by(nickname):
     user = User.query.filter_by(nickname=nickname).first()
     if user is None:
         flash('Invalid user.')
         return redirect(url_for('.index'))
     page = request.args.get('page', 1, type=int)
     pagination = user.followed.paginate(
         page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
         error_out=False)
     follows = [{'user': item.followed, 'timestamp': item.timestamp}
                for item in pagination.items]
     return render_template('followers.html', user=user, title="Followed by",
                            endpoint='.followed_by', pagination=pagination,
                            follows=follows)


from flask_wtf import Form
from  wtforms import StringField, PasswordField,BooleanField,SubmitField
from wtforms.validators import Required,Length,Email,Regexp,EqualTo
from ..models import User
from wtforms import ValidationError

class LoginForm(Form):
    nickname = StringField('nickname',validators=[Required()])
    password = PasswordField('Password',validators=[Required()])
    remember_me = BooleanField('Keep me logged in ')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    nickname = StringField('nickname',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'username must have only letters')])
    password = PasswordField('Password',validators=[Required(),EqualTo('password2',message='Passwords must match')])
    password2=PasswordField('Confirm password',validators=[Required()])
    submit = SubmitField('Register')
    def validate_nickname(self,field):
        if User.query.filter_by(nickname=field.data).first():
            raise  ValidationError('nickname alread registered')


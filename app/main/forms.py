from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required,Length


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    username = StringField("Real Name",validators=[Length(0,64)])
    location = StringField("Locaiton",validators=[Length(0,64)])
    submit = SubmitField("Submit")


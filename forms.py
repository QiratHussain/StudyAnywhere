from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login!")

    from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField
from wtforms.widgets import ListWidget, CheckboxInput

class SubjectForm(FlaskForm):
    subjects = SelectMultipleField("Choose your subjects", coerce=int,widget=ListWidget(prefix_label=False),option_widget=CheckboxInput(),)
    submit = SubmitField("Save")
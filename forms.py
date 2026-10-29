from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField,SubmitField, PasswordField, RadioField
from wtforms.validators import DataRequired
from wtforms.widgets import ListWidget, CheckboxInput

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login!")

class SubjectForm(FlaskForm):
    subjects = SelectMultipleField("Choose your subjects", coerce=int,widget=ListWidget(prefix_label=False),option_widget=CheckboxInput(),)
    submit = SubmitField("Save")

class QuizForm(FlaskForm):
    choice = RadioField("Choice",choices=[],validators=[DataRequired(message="Please select an answer.")],)
    submit = SubmitField("Check answer")
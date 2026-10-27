from flask import Flask, render_template, url_for , redirect, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from flask_bootstrap import Bootstrap5
from forms import RegisterForm, LoginForm
from dotenv import load_dotenv
load_dotenv()


# configure
app = Flask(__name__)
app.config['WTF_CSRF_TIME_LIMIT'] = None  
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Bootstrap5(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profiles.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager= LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
# tables
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    

with app.app_context():
    db.create_all()
# routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        new_user = User(email=form.email.data,name=form.name.data,password=hash_and_salted_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)

@app.route('/login', methods=['POST','GET'])
def login():
    login_form= LoginForm()
    if login_form.validate_on_submit():
        user= db.session.execute(db.select(User).where(User.email == login_form.email.data )).scalar()
        if not user:
            flash('email does not exist')
        elif check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Incorrect Password')
            return redirect(url_for('login'))
    return render_template("login.html", form= login_form,user=current_user)

@app.route("/logout")
def logout():
    login_user()
    return redirect(url_for("home"))

@app.route("/home")
@login_required
def contents():
    return render_template("contents.html")
# TODO: 4. logout
# TODO: 5. users database
# TODO: 6. quiz questions data
# TODO: 7. users results
# TODO: 8. results page
# TODO: 9. subjects page
# TODO: 10. quiz form
# TODO: 11. quiz page
# TODO: 12. users profiles

if __name__ == "__main__":
    app.run(debug=True, port=5003)
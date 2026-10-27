from flask import Flask, render_template, url_for , redirect
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from flask_bootstrap import Bootstrap5
from forms import RegisterForm
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
        return redirect(url_for("home"))
    return render_template("register.html", form=form)

# TODO: 2. set registration 
# TODO: 3. login
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
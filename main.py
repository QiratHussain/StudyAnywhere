from flask import Flask, render_template, url_for , redirect, flash, request, abort
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import  DeclarativeBase, relationship,Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey, func, select
from flask_bootstrap import Bootstrap5
from forms import RegisterForm, LoginForm, SubjectForm, QuizForm
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
    results = relationship("Result", back_populates="user", cascade="all, delete-orphan")

class Subject(db.Model):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    questions = relationship("Questions", back_populates="subject", cascade="all, delete-orphan")

class Questions(db.Model):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("subjects.id"))
    subject = relationship("Subject", back_populates="questions")
    question_text: Mapped[str] = mapped_column(String(100))
    option_a: Mapped[str] = mapped_column(String(1000))
    option_b: Mapped[str] = mapped_column(String(100))
    option_c: Mapped[str] = mapped_column(String(100))
    option_d: Mapped[str] = mapped_column(String(100))
    right_option: Mapped[str] = mapped_column(String(100))

class Result(db.Model):
    __tablename__ = "results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    subject_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("subjects.id"))
    marks: Mapped[int] = mapped_column(Integer, nullable=True) 
    user = relationship("User", back_populates="results")
    subject = relationship("Subject")
    __table_args__ = (db.UniqueConstraint("user_id", "subject_id"),)

with app.app_context():
    db.create_all()
    if not db.session.execute(db.select(Subject)).first():
        db.session.add_all([Subject(name=n) for n in ["English", "Math", "Physics", "Chemistry", "Biology"]])
        db.session.commit()

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
    logout_user()
    return redirect(url_for("home"))

@app.route("/home")
@login_required
def contents():
    return render_template("contents.html")


@app.route("/subjects", methods=["GET", "POST"])
# @login_required
def choose_subjects():
    form = SubjectForm()
    all_subjects = db.session.execute(db.select(Subject)).scalars().all()
    form.subjects.choices = [(s.id, s.name) for s in all_subjects]
    if form.validate_on_submit():
        selected = set(form.subjects.data)
        existing = {r.subject_id: r for r in current_user.results}
        # add newly selected
        for sid in selected - existing.keys():
            db.session.add(Result(user_id=current_user.id, subject_id=sid))
        # remove deselected
        for sid in existing.keys() - selected:
            db.session.delete(existing[sid])
        db.session.commit()
        return redirect(url_for("results"))
    if request.method == "GET":
        form.subjects.data = [r.subject_id for r in current_user.results]  # pre-tick current choices
    return render_template("subjects.html", form=form)


@app.route("/results")
@login_required
def results():
    return render_template("results.html", results=current_user.results)

quiz = {
    "id": "q1",
    "question": "Which planet in the solar system has the shortest orbit around the Sun?",
    "choices": [
        ("A", "Venus"),
        ("B", "Mercury"),
        ("C", "Mars"),
        ("D", "Earth"),
    ],
    "answer": "B",
}

@app.route("/quiz", methods=["GET", "POST"])
def quiz_page():
    form = QuizForm()
    form.choice.choices = quiz["choices"]
    result = None
    if form.validate_on_submit():
        selected = form.choice.data
        texts = dict(quiz["choices"])
        result = {"selected": selected,"selected_text": texts[selected],"correct": quiz["answer"],"correct_text": texts[quiz["answer"]],"is_correct": selected == quiz["answer"],}
    return render_template("quiz.html", form=form, quiz=quiz, result=result)

# TODO: 10. quiz form
# TODO: 11. quiz page
# TODO: 12. users profiles

if __name__ == "__main__":
    app.run(debug=True, port=5003)
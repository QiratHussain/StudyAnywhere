from flask import Flask, render_template, url_for , redirect, flash, request, abort, session
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
import random


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
    marks: Mapped[int] = mapped_column(Integer, default=0)
    attempted_qs: Mapped[int] = mapped_column(Integer, default=0)
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
        user= db.session.execute(db.select(User).where(User.email == form.email.data )).scalar()
        if not user:
            hash_and_salted_password = generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
            new_user = User(email=form.email.data,name=form.name.data,password=hash_and_salted_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('contents'))
        else:
            flash("email already exists, log in instead")
            return redirect(url_for("login"))
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
            return redirect((url_for('contents')))
        else:
            flash('Incorrect Password')
            return redirect(url_for('login'))
    return render_template("login.html", form= login_form,user=current_user)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/contents")
@login_required
def contents():
    return render_template("contents.html")


@app.route("/subjects", methods=["GET", "POST"])
# @login_required
def subjects():
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

@app.route("/quiz/<int:subject_id>", defaults={"index": 0}, methods=["GET", "POST"])
@app.route("/quiz/<int:subject_id>/<int:index>", methods=["GET", "POST"])
@login_required
def quiz(subject_id, index):
    questions = db.session.execute(
        db.select(Questions).where(Questions.subject_id == subject_id).order_by(Questions.id)
    ).scalars().all()
    if not questions:
        abort(404)
    if index >= len(questions):
        return redirect(url_for("results"))

    # get (or create) this user's result row for the subject
    res = db.session.execute(
        db.select(Result).where(Result.user_id == current_user.id, Result.subject_id == subject_id)
    ).scalar()
    if not res:
        res = Result(user_id=current_user.id, subject_id=subject_id, marks=0, attempted_qs=0)
        db.session.add(res)
        db.session.commit()

    # new run through the quiz: forget which questions were already counted
    # (the saved totals in the database are NOT touched)
    key = f"answered_{subject_id}"
    if index == 0 and request.method == "GET":
        session.pop(key, None)

    q = questions[index]
    question = {
        "id": q.id,
        "question": q.question_text,
        "choices": [("A", q.option_a), ("B", q.option_b), ("C", q.option_c), ("D", q.option_d)],
        "answer": q.right_option,
    }
    form = QuizForm()
    form.choice.choices = question["choices"]
    result = None

    if form.validate_on_submit():
        selected = form.choice.data
        texts = dict(question["choices"])
        is_correct = selected == question["answer"]
        result = {
            "selected": selected,
            "selected_text": texts[selected],
            "correct": question["answer"],
            "correct_text": texts[question["answer"]],
            "is_correct": is_correct,
        }
        # count each question once per run (guards against refresh/resubmit)
        answered = session.get(key, [])
        if q.id not in answered:
            res.attempted_qs = (res.attempted_qs or 0) + 1
            if is_correct:
                res.marks = (res.marks or 0) + 1
            session[key] = answered + [q.id]
            db.session.commit()

    return render_template(
        "question.html", form=form, quiz=question, result=result,
        subject_id=subject_id, index=index, is_last=(index == len(questions) - 1),
    )
    
@app.route("/start_quiz")
@login_required
def start_quiz():
    my_subjects = [r.subject for r in current_user.results]
    return render_template("quiz.html", subjects=my_subjects)

if __name__ == "__main__":
    app.run(debug=True, port=5003)
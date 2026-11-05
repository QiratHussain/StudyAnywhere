from flask import Flask, render_template, url_for , redirect, flash, Response,request, abort, session
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import  DeclarativeBase, relationship,Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey, func, Text, CheckConstraint
from flask_bootstrap import Bootstrap5
from forms import RegisterForm, LoginForm, SubjectForm, QuizForm
from dotenv import load_dotenv
load_dotenv()
import random
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import smtplib, os


app = Flask(__name__)
app.config['WTF_CSRF_TIME_LIMIT'] = None  
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
Bootstrap5(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]  
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"] 
app.config["MAIL_DEFAULT_SENDER"] = os.environ["MAIL_USERNAME"]
mail = Mail(app)

def send_verification_email(user):
    token = serializer.dumps(user.email, salt="email-confirm")
    link = url_for("confirm_email", token=token, _external=True)
    msg = Message(subject="Verify your email",recipients=[user.email],body=f"Hi {user.name},\n\nClick the link to verify your account:\n{link}\n\nThis link expires in 1 hour.",) 
    mail.send(msg)


class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_LINK')
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
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    results = relationship("Result", back_populates="user", cascade="all, delete-orphan")

class Subject(db.Model):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    questions = relationship("Questions", back_populates="subject", cascade="all, delete-orphan")

class Questions(db.Model):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("subjects.id"),nullable=False)
    subject = relationship("Subject", back_populates="questions")
    question_text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    right_option: Mapped[str] = mapped_column(String(1), nullable=False)
    __table_args__ = (CheckConstraint("right_option IN ('A', 'B', 'C', 'D')"),)

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
    # if not db.session.execute(db.select(Subject)).first():
    #     db.session.add_all([Subject(name=n) for n in ["English", "Math", "Physics", "Chemistry", "Biology"]])
    #     db.session.commit()

# routes
@app.route("/robots.txt")
def robots():
    base_url = request.url_root.rstrip("/")
    txt = f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n"
    return Response(txt, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    base_url = request.url_root.rstrip("/")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>{base_url}/</loc>
        </url>
    </urlset>
    """
    return Response(xml, mimetype="application/xml")
    
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()                      # new: normalize
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            hash_and_salted_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            new_user = User(email=email, name=form.name.data, password=hash_and_salted_password, is_verified=False)  # new: is_verified
            db.session.add(new_user)
            db.session.commit()

            try:                                                      # new: send email instead of login_user()
                send_verification_email(new_user)
                flash("Account created! Check your email to verify it.")
            except Exception:
                flash("Account created, but we couldn't send the email. Try logging in to resend it.")
            return redirect(url_for('login'))
        else:
            if not user.is_verified:                                  # new: resend for unverified accounts
                try:
                    send_verification_email(user)
                    flash("This email is registered but not verified. We sent a new verification link.")
                except Exception:
                    flash("This email is registered but not verified, and we couldn't send the email. Try again later.")
            else:
                flash("email already exists, log in instead")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/confirm/<token>")                                        # new route
def confirm_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
    except Exception:
        flash("That link is invalid or has expired.")
        return redirect(url_for("login"))

    user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    if not user:
        flash("Account not found.")
        return redirect(url_for("register"))

    if not user.is_verified:
        user.is_verified = True
        db.session.commit()
    flash("Email verified! You can log in now.")
    return redirect(url_for("login"))


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data.strip().lower()                 # new: normalize
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash('email does not exist')
        elif check_password_hash(user.password, login_form.password.data):
            if user and check_password_hash(user.password,login_form.password.data):
                if not user.is_verified:
                    try:
                        send_verification_email(user)
                        flash("Please verify your email first. We sent a new link.")
                    except Exception:
                        app.logger.exception("Resend failed")
                        flash("Please verify your email first. We couldn't send the link, try again later.")
                    return redirect(url_for("login"))
                login_user(user)
            return redirect((url_for('contents')))
        else:
            flash('Incorrect Password')
            return redirect(url_for('login'))
    return render_template("login.html", form=login_form, user=current_user)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/contents")
@login_required
def contents():
    return render_template("contents.html")


@app.route("/subjects", methods=["GET", "POST"])
@login_required
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
    all_questions = db.session.execute(
        db.select(Questions).where(Questions.subject_id == subject_id)
    ).scalars().all()
    if not all_questions:
        abort(404)
    by_id = {q.id: q for q in all_questions}

    # get (or create) this user's result row for the subject
    res = db.session.execute(
        db.select(Result).where(Result.user_id == current_user.id, Result.subject_id == subject_id)
    ).scalar()
    if not res:
        res = Result(user_id=current_user.id, subject_id=subject_id, marks=0, attempted_qs=0)
        db.session.add(res)
        db.session.commit()

    answered_key = f"answered_{subject_id}"
    order_key = f"order_{subject_id}"

    # new run: forget counted questions AND reshuffle
    if index == 0 and request.method == "GET":
        session.pop(answered_key, None)
        session.pop(order_key, None)

    # keep the shuffled order stable for the whole run
    order = session.get(order_key)
    if not order or set(order) != set(by_id):   # missing, or questions added/removed
        order = list(by_id)
        random.shuffle(order)
        session[order_key] = order
    if index >= len(order):
        return redirect(url_for("results"))
    q = by_id[order[index]]
    question = {"id": q.id,"question": q.question_text,"choices": [("A", q.option_a), ("B", q.option_b), ("C", q.option_c), ("D", q.option_d)],"answer": q.right_option,}
    form = QuizForm()
    form.choice.choices = question["choices"]
    result = None
    if form.validate_on_submit():
        selected = form.choice.data
        texts = dict(question["choices"])
        is_correct = selected == question["answer"]
        result = {"selected": selected,"selected_text": texts[selected],"correct": question["answer"],"correct_text": texts[question["answer"]],"is_correct": is_correct,}
        answered = session.get(answered_key, [])
        if q.id not in answered:
            res.attempted_qs = (res.attempted_qs or 0) + 1
            if is_correct:
                res.marks = (res.marks or 0) + 1
            session[answered_key] = answered + [q.id]
            db.session.commit()
    return render_template("question.html", form=form, quiz=question, result=result,subject_id=subject_id, index=index, is_last=(index == len(order) - 1),)
    
@app.route("/start_quiz")
@login_required
def start_quiz():
    my_subjects = [r.subject for r in current_user.results]
    return render_template("quiz.html", subjects=my_subjects)

if __name__ == "__main__":
    with app.app_context():
        with db.engine.connect() as connection:
            print(connection.execute(db.text("SELECT version()")).scalar())
    app.run(debug= False)

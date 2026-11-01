# StudyAnywhere

A web-based learning and MCQ practice platform designed to help students study, assess their knowledge, and track their academic progress.

## Features

- **User Authentication:** Register and log in securely using hashed passwords.
- **Email Verification:** Verify registered email addresses through time-limited confirmation links.
- **Subject Selection:** Choose multiple subjects to include in your learning dashboard.
- **Interactive MCQ Quizzes:** Attempt multiple-choice questions with four answer options.
- **Randomized Questions:** Questions are shuffled for each new quiz session.
- **Instant Feedback:** See your selected answer, the correct answer, and whether your response was correct.
- **Performance Tracking:** Track marks and attempted questions separately for each subject.
- **Session Management:** Maintain quiz progress during an active session.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| SQLAlchemy | Database ORM |
| SQLite / PostgreSQL | Database |
| Flask-Login | User authentication |
| Flask-WTF | Form handling and validation |
| HTML & CSS | Frontend |
| Bootstrap | Responsive interface |
| Jinja2 | HTML templating |
| Vercel | Deployment |

## Database Structure

The application uses relational database models:

- **Users:** Stores user information, credentials and verification status.
- **Subjects:** Stores available academic subjects.
- **Questions:** Stores MCQs, their four options and correct answers.
- **Results:** Stores user performance, marks and attempted-question counts for each subject.

Relationships are managed through SQLAlchemy.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/StudyAnywhere.git
cd StudyAnywhere
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\Scripts\activate
```

Linux / macOS:
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and configure the required application settings, including:

- Flask secret key
- Database connection URL
- Email server credentials

Never commit your `.env` file or expose credentials in your repository.

### 5. Run the application

```bash
python main.py
```

Open:

```text
http://127.0.0.1:5003
```

## Project Status

StudyAnywhere is an independent project under active development.

Upcoming improvements include:

- Expanded subject-wise question banks
- Improved performance analytics
- Additional quiz functionality
- Enhanced user experience
- Production PostgreSQL deployment

## Author

**Qirat Hussain**

GitHub: https://github.com/QiratHussain

---

*Built with Python, Flask and a genuine interest in making learning more accessible.*

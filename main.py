from flask import Flask, render_template
import os
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['WTF_CSRF_TIME_LIMIT'] = None  
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Bootstrap5(app)

@app.route("/")
def home():
    return render_template("index.html")


# TODO: 1. set home page
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
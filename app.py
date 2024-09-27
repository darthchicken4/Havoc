# import
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask import url_for
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# index page, shows recent posts


@app.route("/")
@login_required
def index():
    user = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"]
    )
    posts = db.execute(
        "SELECT * FROM posts WHERE user = ?", user[0]["username"]
    )
    return render_template("index.html", posts=posts)
# guidlines page, shows guidlines


@app.route("/guidlines")
@login_required
def guidlines():
    return render_template("guidlines.html")

# allows the user to sign in


@app.route("/signin", methods=["GET", "POST"])
def signin():

    print("user login")
    # loose the old id
    session.clear()

    # post
    if request.method == "POST":
        # check for inputted info
        if not request.form.get("username"):
            return apology("Must provide username", 403)
        elif not request.form.get("password"):
            return apology("Must provide password", 403)
        # get user
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        # check the hash
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("Wrong username or password", 403)
        # set session to user id
        session["user_id"] = rows[0]["id"]

        # send to index page
        print("redirect index")
        return redirect("/")

    # display page if get
    else:
        print("redirect signing")
        return render_template("signin.html")

# allows user to sing out


@login_required
@app.route("/signout")
def signout():

    # end session
    session.clear()

    # redirect to signedout
    return redirect("/signin")

# allow user to report other users


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    # post
    if request.method == "POST":
        if not request.form.get("subject"):
            return apology("We need a subject", 400)
        if not request.form.get("desc"):
            return apology("We need a description", 400)
        # get user
        rows = db.execute(
            "SELECT username FROM users WHERE id = ?", session["user_id"]
        )
        # insert values
        db.execute("INSERT INTO reports (desc, subject, user) VALUES (?, ?, ?)",
                   request.form.get("thread_id"), request.form.get("text"), rows[0]["username"])
        return redirect("/")
    # display page if get
    if request.method == "GET":
        return render_template('report.html')


# page where users create threads
@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    # display page if get
    if request.method == "GET":
        print("rendered forums")
        return render_template('create.html')
    # end info if post
    if request.method == "POST":
        # Ensure stuff was submitted
        if not request.form.get("title"):
            return apology("Must provide a title", 400)
        elif not request.form.get("text"):
            return apology("Must provide a description", 400)
        # get user
        rows = db.execute(
            "SELECT username FROM users WHERE id = ?", session["user_id"]
        )
        db.execute("INSERT INTO threads (title, user, content) VALUES (?, ?, ?)",
                   request.form.get("title"), rows[0]['username'], request.form.get("text"))

        threadS = db.execute("SELECT * FROM threads ORDER BY created DESC")
        # format the date
        for thread in threadS:
            datetime_object = datetime.strptime(thread["created"], '%Y-%m-%d %H:%M:%S')
            thread["formatted_created"] = datetime_object.strftime('%m/%d/%Y')
        # send the dictionary of threads with the newly added formatted date
        return render_template('forums.html', threads=threadS)


# allow user to view a list of fourms
@app.route("/forums", methods=["GET", "POST"])
@login_required
def forums():
    # display get
    if request.method == "GET":
        threadS = db.execute("SELECT * FROM threads ORDER BY created DESC")
        print("rendered forums")
        # format the date and put it in a dictionary
        for thread in threadS:
            created = thread["created"]
            datetime_object = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
            thread["formatted_created"] = datetime_object.strftime('%m/%d/%Y')
        return render_template('forums.html', threads=threadS)


# allow user to post on a thread
@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    # send information
    if request.method == "POST":
        if not request.form.get("text"):
            return apology("You can't comment nothing", 400)
        if not request.form.get("thread_id"):
            return apology("Hmm.. This shouldn't happen", 400)
        # get user
        rows = db.execute(
            "SELECT username FROM users WHERE id = ?", session["user_id"]
        )
        # insert values
        db.execute("INSERT INTO posts (user, thread_id, content) VALUES (?, ?, ?)",
                   rows[0]["username"], request.form.get("thread_id"), request.form.get("text"))
        # redirect to the same page
        return redirect(url_for('thread', thread_id=request.form.get("thread_id")))


# allow user to view the thread they chose
@app.route('/thread/<int:thread_id>', methods=["GET"])
@login_required
def thread(thread_id):
    # thread
    thread = db.execute("SELECT * FROM threads WHERE id = ?", thread_id)
    created = thread[0]["created"]
    Posts = db.execute("SELECT * FROM posts WHERE thread_id = ? ORDER BY created", thread[0]["id"])
    datetime_object = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
    date_only = datetime_object.strftime('%Y-%m-%d')
    # render the thread template
    return render_template('thread.html', title=thread[0]["title"], creation=date_only, text=thread[0]["content"], user=thread[0]["user"], thread_id=thread[0]["id"], posts=Posts)


# allow user to register
@app.route("/register", methods=["GET", "POST"])
def register():
    # if get then register
    if request.method == "GET":
        return render_template('register.html')
    # if not then post
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure stuff was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must rewrite password", 400)
        elif not request.form.get("email"):
            return apology("must enter email", 400)
        # check if the username is unique
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if not rows:
            if request.form.get("password") == request.form.get("confirmation"):
                hash = generate_password_hash(request.form.get("password"))
                db.execute("INSERT INTO users (username, hash, email, title) VALUES (?, ?, ?, ?)",
                           request.form.get("username"), hash, request.form.get("email"), "Peasent")
                id = db.execute("SELECT id FROM users WHERE username = ?",
                                request.form.get("username"))
                # Remember which user has logged in
                print("hi")
                print("hi")
                session["user_id"] = id[0]['id']

                # Redirect user to home page
                return redirect("/")
            else:
                return apology("passwords must match", 400)
        else:
            return apology("username must be unique", 400)

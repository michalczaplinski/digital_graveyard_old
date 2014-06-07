from flask import Flask, render_template, g
import sqlite3, os, os.path


app = Flask(__name__)
DATABASE = os.path.join(os.getenv('OPENSHIFT_DATA_DIR'), 'tweets.db')
INCLUDE_RETWEETS = False

@app.before_request
def before_request():
    g.db = sqlite3.connect(DATABASE)


@app.route("/")
def hello():
    if INCLUDE_RETWEETS:
        tweets = g.db.execute("SELECT name, user, time FROM tweet").fetchall()
    else:
        tweets = g.db.execute("SELECT name, user, time FROM tweet where retweet_status == 1").fetchall()
    length = len(tweets)
    return render_template('index.html', length=length, tweets=tweets)


if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask

from latexbuddy import __name__ as name


app = Flask(name)


def run_server():
    app.run()


@app.route("/")
def index():
    return "<p>Just a test for now...</p>"

#!/usr/bin/python3
"""
Main file
"""
import os
from flask import Flask, render_template, request, send_file, g, redirect

from . import auth, albums, partition

app = Flask(__name__)

app.config.from_mapping(
    # a default secret that should be overridden by instance config
    SECRET_KEY="dev",
    # store the database in the instance folder
    DATABASE=os.path.join(app.instance_path, f"{__name__}.sqlite"),
)

app.register_blueprint(auth.bp)
app.register_blueprint(albums.bp)
app.register_blueprint(partition.bp)


@app.route("/")
def home():
    """Redirect to home"""
    return redirect("/albums/")


if __name__ == "__main__":
    app.run(host="0.0.0.0")

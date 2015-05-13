#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from database_setup import Base, Category, Item
from flask import Flask
import jinja2
import os
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)


# Database configuration.
engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


# Template configuration.
jinjaEnv = jinja2.Environment(
    loader = jinja2.FileSystemLoader("templates"))


categories = []
items = []


@app.route('/')
def IndexHandler():
    category = categories[0]
    template = jinjaEnv.get_template("index.html")
    return template.render(categories = categories, items = items)

if __name__ == "__main__":
    categories = session.query(Category).all()
    items = session.query(Item).all()

    app.debug = True
    app.run(host = "0.0.0.0", port = 8000)

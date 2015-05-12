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

_this_file_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

# Database configuration.
engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Template configuration.
jinjaEnv = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.join(_this_file_dir, "templates"))
)


@app.route('/')
def IndexHandler():
    category = session.query(Category).first()
    items = session.query(Item).filter_by(category_id = category.cid)
    template = jinjaEnv.get_template("index.html")
    return template.render(category = category, items = items)

if __name__ == "__main__":
    app.debug = True
    app.run(host = "0.0.0.0", port = 8000)

#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from database_setup import Base, Category, Item
from flask import Flask, render_template
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


categories = {}
items = {}


@app.route("/")
def home():
    jumbotron = render_template("index-jumbo.html")
    abstracts = [render_template("item-abstract.html", item=i)
                 for d in items.values() for i in d.values()]
    category_links = [render_template("category-link.html",
                                      category=c, active=False)
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/r/<category_name>")
def read_category(category_name):
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
    jumbotron = render_template("category-jumbo.html", category = category)
    abstracts = [render_template("item-abstract.html", item=i)
                 for i in items[category_name].values()]
    category_links = [render_template("category-link.html",
                                      category=c, active=(c==category))
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/r/<category_name>/<item_name>")
def read_item(category_name, item_name):
    if category_name not in categories or item_name not in items[category_name]:
        return "Not Found", 404
    category = categories[category_name]
    item = items[category_name][item_name]
    jumbotron = render_template("item-jumbo.html", item = item)
    category_links = [render_template("category-link.html",
                                      category=c, active=(c==category))
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = [],
                           category_links = category_links)


@app.route("/u/<category_name>")
def update_category(category_name):
    return render_template("edit.html")


@app.route("/u/<category_name>/<item_name>")
def update_item(category_name, item_name):
    return render_template("edit.html")


if __name__ == "__main__":
    for c in session.query(Category).all():
        categories[c.name] = c
    for item in session.query(Item).all():
        cname = [c for c in categories.values()
                 if c.cid == item.category_id][0].name
        item.category_name = cname
        items.setdefault(cname, {})[item.name] = item

    app.debug = True
    app.run(host = "0.0.0.0", port = 8000)

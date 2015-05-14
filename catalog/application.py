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
jinjaEnv = jinja2.Environment(loader = jinja2.FileSystemLoader("templates"))


categories = {}
items = {}


def render_category_link(category, is_active=False):
    return '<a href="/{0}" class="list-group-item {1}">{0}</a>'.format(
        category.name, is_active and "active" or "")


@app.route("/")
def IndexHandler():
    jumbotron = jinjaEnv.get_template("index-jumbo.html").render()
    abstract_template = jinjaEnv.get_template("item-abstract.html")
    abstracts = [abstract_template.render(item=i)
                 for d in items.values() for i in d.values()]
    category_links = [render_category_link(c) for c in categories.values()]
    return jinjaEnv.get_template("view.html").render(
        jumbotron = jumbotron,
        abstracts = abstracts,
        category_links = category_links
    )


@app.route("/<category_name>")
def CategoryHandler(category_name):
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]

    jumbotron = jinjaEnv.get_template("category-jumbo.html").render(
        category = category)

    abstract_template = jinjaEnv.get_template("item-abstract.html")
    abstracts = [abstract_template.render(item=i)
                 for i in items[category_name].values()]

    category_links = [render_category_link(c, c==category)
                      for c in categories.values()]

    return jinjaEnv.get_template("view.html").render(
        jumbotron = jumbotron,
        abstracts = abstracts,
        category_links = category_links
    )


@app.route("/<category_name>/<item_name>")
def ItemHandler(category_name, item_name):
    if category_name not in categories or item_name not in items[category_name]:
        return "Not Found", 404
    category = categories[category_name]
    item = items[category_name][item_name]
    jumbotron = jinjaEnv.get_template("item-jumbo.html").render(item = item)
    category_links = [render_category_link(c, c==category)
                      for c in categories.values()]
    return jinjaEnv.get_template("view.html").render(
        jumbotron = jumbotron,
        abstracts = [],
        category_links = category_links
    )


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

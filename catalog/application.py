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


categories = {}
items = {}


def render_category_link(category, is_active=False):
    return '<a href="/{0}" class="list-group-item {1}">{0}</a>'.format(
        category.name, is_active and "active" or "")


def render_category_info(category):
    return u'<h1>{0}</h1><p>{1} <a href="{2}">[Wiki Page]</a></p>'.format(
        category.name, category.description, category.wiki_url)

def render_item_preview_div(item):
    template = (
        u'<div class="col-xs-6 col-lg-4">\n'
        '  <h2>{0}</h2>\n'
        '  <p>{1}</p>\n'
        '  <p><a class="btn btn-default" href="#" role="button">'
        'View details &raquo;</a></p>\n'
        '</div><!--/.col-xs-6.col-lg-4-->'
    )
    return template.format(item.name, item.short_description(200))


@app.route("/")
def IndexHandler():
    template = jinjaEnv.get_template("category.html")
    category_links = [render_category_link(c) for c in categories.values()]
    item_divs = [render_item_preview_div(i)
                 for d in items.values() for i in d.values()]
    category_info = """<h1>Hello, world!</h1>
    <p>In this project, we develop an application that provides a list
    of items within a variety of categories as well as provide a user
    registration and authentication system. Registered users will have
    the ability to post, edit and delete their own items.</p>"""
    return template.render(item_divs = item_divs,
                           category_links = category_links,
                           category_info = category_info)


@app.route("/<category_name>")
def CategoryHandler(category_name):
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
    template = jinjaEnv.get_template("category.html")
    category_links = [render_category_link(c, c==category)
                      for c in categories.values()]
    item_divs = [render_item_preview_div(i)
                 for i in items[category_name].values()]
    category_info = render_category_info(category)
    return template.render(item_divs = item_divs,
                           category_links = category_links,
                           category_info = category_info)


@app.route("/<category>/<item>")
def ItemHandler(category, item):
    return "Handling %s in %s" % (category, item)


if __name__ == "__main__":
    for c in session.query(Category).all():
        categories[c.name] = c
    for item in session.query(Item).all():
        cname = [c for c in categories.values()
                 if c.cid == item.category_id][0].name
        items.setdefault(cname, {})[item.name] = item

    app.debug = True
    app.run(host = "0.0.0.0", port = 8000)

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


def render_category_link(category):
    return '<a href="#" class="list-group-item">{0}</a>'.format(category.name)


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
    category_links = [render_category_link(c) for c in categories]
    item_divs = [render_item_preview_div(i) for i in items]
    return template.render(item_divs = item_divs,
                           category_links = category_links)


@app.route("/<category>")
def CategoryHandler(category):
    return "Handling: " + category


@app.route("/<category>/<item>")
def ItemHandler(category, item):
    return "Handling %s in %s" % (category, item)


if __name__ == "__main__":
    categories = session.query(Category).all()
    items = session.query(Item).all()

    app.debug = True
    app.run(host = "0.0.0.0", port = 8000)

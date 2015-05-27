#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from datetime import datetime
import os.path

from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.ext.seasurf import SeaSurf


# These definitions need to come before importing any module in current
# directory, in order to avoid circular import issues.
app = Flask(__name__)
csrf = SeaSurf(app)


import catalog.create
import catalog.data as data
import catalog.delete
import catalog.login as login
import catalog.read
import catalog.update


# TODO: These import might not necessary or should be from `catalog.data`.
from database_setup import Base
from database_setup import DATABASE_NAME
from database_setup import Category
from database_setup import Item

# TODO: We should not need db_session in this module.
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
db_session = scoped_session(sessionmaker(bind = data.engine))



# Secret key generated with `os.urandom(24)`.
app.secret_key = '\x8bu\xc5\x87\x07$4\x83\xcbz\xfaB %\xc8\xf9A\xe2J=\x0e/"#'


# We use two in-memory dictionaries to cache the catalog data used by this app,
# which are read from the database when the app starts. When the user makes a
# create/update/delete request, we modify both the in-memory dictionaries as
# well as the underlying database and keep the two consistent all the time.
#
# The `items` is a dictionary of dictionary. For outer dictionary, the key is
# still category name, and for inner dictionary, the key is item name (which
# should be unique within a category) and value is an `Item` object. In other
# word, to access an item, use `items[category_name][item_name]`.

items = {}

# Read the categories and items from database into memory.
for category_name in data.get_categories():
    items[category_name] = data.get_items(category_name)
    """
for item in db_session.query(Item).all():
    cname = [c for c in data.get_categories().values()
             if c.cid == item.category_id][0].name
    item.category_name = cname
    items.setdefault(cname, {})[item.name] = item
    """


@app.route("/")
def home():
    """Render the home page."""
    jumbotron = render_template("index-jumbo.html")
    abstracts = []
    """
    abstracts = [render_template("item-abstract.html", item=i)
                 for d in items.values() for i in d.values()]
    """
    category_links = [render_template("category-link.html",
                                      category=c, active=False)
                      for c in data.get_categories().values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/d/<category_name>", methods=["POST"])
@login.login_required
def delete_category(category_name):
    """Handle delete category request."""
    # First delete the items inside the category.
    for item in items[category_name].values():
        # TODO
        # db_session.delete(item)
        pass
    del items[category_name]
    # Then delete the category itself.
    data.delete_category(category_name)
    flash("The category '{0}' has been deleted.".format(category_name))
    return redirect('/')


def category_to_json(category):
    """Return a 'json-ready' dictionary that contains category name,
    description, wiki url, as well as all the items of this category inside
    this list."""
    return {
        "name": category.name,
        "description": category.description,
        "wiki_url": category.wiki_url,
        "items": [item_to_json(i)
                  for i in items[category.name].values()]
    }


def item_to_json(item):
    """Return a 'json-ready' dictionary that contains the item name,
    description, wiki url. Note that the category information is not contained
    in this dictionary."""
    return {
        "name": item.name,
        "description": item.description,
        "wiki_url": item.wiki_url
    }


@app.route("/j/")
def api_json():
    """Return a json object containing all categories and items."""
    return jsonify(categories = [category_to_json(c)
                                 for c in categories.values()])


@app.route("/j/<category_name>")
def api_json_category(category_name):
    """Return a json object containing information of the requested category."""
    category = data.get_category(category_name)
    return jsonify(category = category_to_json(category))


@app.route("/j/<category_name>/<item_name>")
def api_json_item(category_name, item_name):
    """Return a json object containing information of the requested item."""
    return jsonify(item = item_to_json(items[category_name][item_name]))

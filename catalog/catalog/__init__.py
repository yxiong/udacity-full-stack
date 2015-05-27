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


import catalog.data as data
import catalog.login as login
import catalog.view


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


@app.route("/c/category")
@login.login_required
def create_category():
    """Render create category page."""
    category = Category(name="Category name",
                        description="Add some description.",
                        wiki_url = "http://www.wikipedia.org/xxx")
    return render_template("edit.html",
                           title = "Create a category.",
                           entity = category,
                           cancel_url = '/')


@app.route("/c/category", methods=["POST"])
@login.login_required
def create_category_post():
    """Handle create category request."""
    name = request.form["name"]
    # Make sure the category name does not already exist.
    if name in data.get_categories():
        flash("Error: The category name '{0}' already exists.".format(name))
        return redirect(url_for('create_category'))
    # Create a `Category` object and add into database.
    category = Category(name=name,
                        description = request.form["description"],
                        wiki_url = request.form["wiki"],
                        last_modified = datetime.now())
    data.add_category(category)
    flash("The category has been added.")
    return redirect(url_for('read_category', category_name = name))


@app.route("/c/<category_name>/item")
@login.login_required
def create_item(category_name):
    """Render create item page."""
    item = Item(name="Item name",
                description="Add some description.",
                wiki_url = "http://www.wikipedia.org/xxx")
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Create an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/c/<category_name>/item", methods=["POST"])
@login.login_required
def create_item_post(category_name):
    """Handle create item request."""
    name = request.form["name"]
    # Make sure the item name does not exist in the same category.
    if name in items[category_name]:
        flash("Error: The item name '{0}' already exists"
              "in this category.".format(name))
        return redirect(url_for('create_item', category_name=category_name))
    # Create an `Item` object and add into database.
    item = Item(name=name,
                description = request.form["description"],
                wiki_url = request.form["wiki"],
                category = categories[category_name],
                last_modified = datetime.now())
    db_session.add(item)
    db_session.commit()
    # Update in-memory cache.
    item.category_name = category_name
    items[category_name][name] = item
    flash("The item has been added.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = name))


@app.route("/r/<category_name>/<item_name>")
def read_item(category_name, item_name):
    """Render read item page."""
    categories = data.get_categories()
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


@app.route("/u/<category_name>", methods=["GET"])
@login.login_required
def update_category(category_name):
    """Render update category page."""
    category = data.get_category(category_name)
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Edit a category.",
                           entity = category,
                           cancel_url = cancel_url)


@app.route("/u/<category_name>", methods=["POST"])
@login.login_required
def update_category_post(category_name):
    """Handle update category request."""
    categories = data.get_categories()
    category = categories[category_name]
    # Check if the category name has changed.
    old_name = category.name
    new_name = request.form["name"]
    if old_name != new_name:
        # Make sure the new name does not already exist.
        if new_name in categories:
            flash("Error: The category name '{0}' already exists.".format(
                new_name))
            return redirect(url_for('update_category',
                                    category_name = old_name))
        # Update the in-memory cache about the category name change.
        items[new_name] = items[old_name]
        del items[old_name]
        for item in items[new_name].values():
            item.category_name = new_name
        data.change_category_name_in_cache(old_name, new_name)
        category.name = new_name
    # Update description and wiki url, and update into database.
    category.description = request.form["description"]
    category.wiki_url = request.form["wiki"]
    category.last_modified = datetime.now()
    data.add_category(category)
    flash("The category has been updated.")
    return redirect(url_for('read_category', category_name = new_name))


@app.route("/u/<category_name>/<item_name>")
@login.login_required
def update_item(category_name, item_name):
    """Render update item page."""
    item = items[category_name][item_name]
    cancel_url = url_for('read_item',
                         category_name = category_name,
                         item_name = item_name)
    return render_template("edit.html",
                           title = "Edit an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/u/<category_name>/<item_name>", methods=["POST"])
@login.login_required
def update_item_post(category_name, item_name):
    """Handle update item request."""
    category = data.get_category(category_name)
    item = items[category_name][item_name]
    # Check if the item name has changed.
    old_name = item.name
    new_name = request.form["name"]
    if old_name != new_name:
        # Make sure the new name does not already exist in this category.
        if new_name in items[category_name]:
            flash("Error: The item name '{0}' already exists"
                  "in this category.".format(new_name))
            return redirect(url_for('update_item',
                                    category_name = category_name,
                                    item_name = item_name))
        # Update the in-memory cache about the item name change.
        items[category_name][new_name] = items[category_name][old_name]
        del items[category_name][old_name]
        item.name = new_name
    # Update description and wiki url and update into database.
    item.description = request.form["description"]
    item.wiki_url = request.form["wiki"]
    item.last_modified = datetime.now()
    db_session.add(item)
    db_session.commit()
    flash("The item has been updated.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = new_name))


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


@app.route("/d/<category_name>/<item_name>", methods=["POST"])
@login.login_required
def delete_item(category_name, item_name):
    """Handle delete item request."""
    # Delete the item from the database.
    item = items[category_name][item_name]
    db_session.delete(item)
    db_session.commit()
    # Delete from the in-memory cache as well.
    del items[category_name][item_name]
    flash("The item '{0}' has been deleted.".format(item_name))
    return redirect(url_for('read_category', category_name = category_name))


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

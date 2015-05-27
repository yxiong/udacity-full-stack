#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 27, 2015.

from datetime import datetime

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from catalog import app
import catalog.data as data
from catalog.data import MemCategory as Category
from catalog.data import MemItem as Item
import catalog.login as login


@app.route("/c/category")
@login.login_required
def create_category():
    """Render create category page."""
    category = Category(cid = None,
                        name = "Category name",
                        description = "Add some description.",
                        wiki_url = "http://www.wikipedia.org/xxx",
                        last_modified = datetime.now())
    return render_template("edit.html",
                           title = "Create a category.",
                           entity = category,
                           cancel_url = '/')


@app.route("/c/category", methods=["POST"])
@login.login_required
def create_category_post():
    """Handle create category request."""
    # Make sure the category name does not already exist.
    name = request.form["name"]
    if name in data.get_categories():
        flash("Error: The category name '{0}' already exists.".format(name))
        return redirect(url_for('create_category'))
    # Create a `Category` object and add into database.
    category = Category(cid = None,
                        name = name,
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
    category = data.get_category(category_name)
    if not category:
        return "Category '%s' not found" % category_name, 404
    item = Item(category = category,
                iid = None,
                name = "Item name",
                description = "Add some description.",
                wiki_url = "http://www.wikipedia.org/xxx",
                last_modified = datetime.now())
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Create an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/c/<category_name>/item", methods=["POST"])
@login.login_required
def create_item_post(category_name):
    """Handle create item request."""
    # Check the `category_name`.
    category = data.get_category(category_name)
    if not category:
        return "Category '%s' not found" % category_name, 404
    # Make sure the item name does not exist in the same category.
    items = data.get_items(category_name)
    name = request.form["name"]
    if name in items:
        flash("Error: The item name '{0}' already exists"
              "in this category.".format(name))
        return redirect(url_for('create_item', category_name=category_name))
    # Create an `Item` object and add into database.
    item = Item(category = category,
                iid = None,
                name = name,
                description = request.form["description"],
                wiki_url = request.form["wiki"],
                last_modified = datetime.now())
    data.add_item(item)
    flash("The item has been added.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = name))

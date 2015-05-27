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
import catalog.login as login


@app.route("/u/<category_name>/<item_name>")
@login.login_required
def update_item(category_name, item_name):
    """Render update item page."""
    item = data.get_item(category_name, item_name)
    if not item:
        return "Not Found", 404
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
    # Get the item to be updated.
    item = data.get_item(category_name, item_name)
    if not item:
        return "Not Found", 404
    # Check if the item name has changed.
    old_name = item.name
    new_name = request.form["name"]
    if old_name != new_name:
        # Make sure the new name does not already exist in this category.
        items = data.get_items(category_name)
        if new_name in items:
            flash("Error: The item name '{0}' already exists "
                  "in this category.".format(new_name))
            return redirect(url_for('update_item',
                                    category_name = category_name,
                                    item_name = item_name))
        # Update the in-memory cache about the item name change.
        data.change_item_name_in_cache(category_name, old_name, new_name)
        item.name = new_name
    # Update description and wiki url and update into database.
    item.description = request.form["description"]
    item.wiki_url = request.form["wiki"]
    item.last_modified = datetime.now()
    data.update_item(item)
    flash("The item has been updated.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = new_name))

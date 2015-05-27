#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 27, 2015.

from flask import flash
from flask import redirect
from flask import url_for

from catalog import app
import catalog.data as data
import catalog.login as login


@app.route("/d/<category_name>", methods=["POST"])
@login.login_required
def delete_category(category_name):
    """Handle delete category request."""
    category = data.get_category(category_name)
    data.delete_category(category)
    flash("The category '{0}' has been deleted.".format(category_name))
    return redirect('/')


@app.route("/d/<category_name>/<item_name>", methods=["POST"])
@login.login_required
def delete_item(category_name, item_name):
    """Handle delete item request."""
    item = data.get_item(category_name, item_name)
    if not item:
        return "Not Fount", 404
    data.delete_item(item)
    flash("The item '{0}' has been deleted.".format(item_name))
    return redirect(url_for('read_category', category_name = category_name))

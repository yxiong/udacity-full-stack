#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 27, 2015.

from flask import jsonify

from catalog import app
import catalog.data as data


@app.route("/j/")
def api_json():
    """Return a json object containing all categories."""
    return jsonify(categories = [c.to_json()
                                 for c in data.get_categories().values()])


@app.route("/j/<category_name>")
def api_json_category(category_name):
    """Return a json object containing information of the requested category
    together with all items inside this category."""
    category = data.get_category(category_name)
    if not category:
        return "Not Found", 404
    items = data.get_items(category_name).values()
    return jsonify(
        category = category.to_json(),
        items = [i.to_json() for i in items]
    )


@app.route("/j/<category_name>/<item_name>")
def api_json_item(category_name, item_name):
    """Return a json object containing information of the requested item."""
    item = data.get_item(category_name, item_name)
    if not item:
        return "Not Found", 404
    return jsonify(item = item.to_json())

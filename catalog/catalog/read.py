#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 27, 2015.

from flask import render_template

from catalog import app
import catalog.data as data


@app.route("/")
def home():
    """Render the home page."""
    jumbotron = render_template("index-jumbo.html")
    abstracts = [render_template("item-abstract.html", item=i)
                 for i in data.get_latest_items()]
    category_links = [render_template("category-link.html",
                                      category=c, active=False)
                      for c in data.get_categories().values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/r/<category_name>")
def read_category(category_name):
    """Render read category page."""
    # Get the category.
    categories = data.get_categories()
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
    # Render the page.
    jumbotron = render_template("category-jumbo.html", category = category)
    abstracts = [render_template("item-abstract.html", item=i)
                 for i in data.get_items(category_name).values()]
    category_links = [render_template("category-link.html",
                                      category=c, active=(c==category))
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/r/<category_name>/<item_name>")
def read_item(category_name, item_name):
    """Render read item page."""
    # Get the category.
    categories = data.get_categories()
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
    # Get the item.
    items = data.get_items(category_name)
    if item_name not in items:
        return "Not Found", 404
    item = items[item_name]
    # Render the page.
    jumbotron = render_template("item-jumbo.html", item = item)
    category_links = [render_template("category-link.html",
                                      category=c, active=(c==category))
                      for c in categories.values()]

    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = [],
                           category_links = category_links)

#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 27, 2015.

from flask import render_template

from catalog import app
import catalog.data as data


@app.route("/r/<category_name>")
def read_category(category_name):
    """Render read category page."""
    categories = data.get_categories()
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
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

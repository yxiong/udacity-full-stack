#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from database_setup import Base, Category, Item
from flask import Flask, render_template, url_for, request, redirect, flash
import os
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = "secret"  # TODO


# Database configuration.
engine = create_engine("sqlite:///catalog.db",
                       connect_args = {"check_same_thread":False}) # TODO
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


categories = {}
items = {}


@app.route("/")
def home():
    jumbotron = render_template("index-jumbo.html")
    abstracts = [render_template("item-abstract.html", item=i)
                 for d in items.values() for i in d.values()]
    category_links = [render_template("category-link.html",
                                      category=c, active=False)
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/c/category")
def create_category():
    category = Category(name="Category name",
                        description="Add some description.",
                        wiki_url = "Wikipedia url")
    return render_template("edit.html",
                           title = "Create a category.",
                           entity = category,
                           cancel_url = '/')


@app.route("/c/category", methods=["POST"])
def create_category_post():
    name = request.form["name"]
    if name in categories:
        flash("The category name '{0}' already exists.".format(name))
        return redirect(url_for('create_category'))
    category = Category(name=name,
                        description = request.form["description"],
                        wiki_url = request.form["wiki"])
    categories[name] = category
    items[name] = {}
    session.add(category)
    session.commit()
    flash("The category has been added.")
    return redirect(url_for('read_category', category_name = name))


@app.route("/c/<category_name>/item")
def create_item(category_name):
    item = Item(name="Item name",
                description="Add some description.",
                wiki_url = "Wikipedia url")
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Create an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/c/<category_name>/item", methods=["POST"])
def create_item_post(category_name):
    name = request.form["name"]
    if name in items[category_name]:
        flash("The item name '{0}' already exists in this category.".format(
            name))
        return redirect(url_for('create_item', category_name=category_name))
    item = Item(name=name,
                description = request.form["description"],
                wiki_url = request.form["wiki"],
                category = categories[category_name])
    item.category_name = category_name
    items[category_name][name] = item
    session.add(item)
    session.commit()
    flash("The item has been added.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = name))


@app.route("/r/<category_name>")
def read_category(category_name):
    if category_name not in categories:
        return "Not Found", 404
    category = categories[category_name]
    jumbotron = render_template("category-jumbo.html", category = category)
    abstracts = [render_template("item-abstract.html", item=i)
                 for i in items[category_name].values()]
    category_links = [render_template("category-link.html",
                                      category=c, active=(c==category))
                      for c in categories.values()]
    return render_template("view.html",
                           jumbotron = jumbotron,
                           abstracts = abstracts,
                           category_links = category_links)


@app.route("/r/<category_name>/<item_name>")
def read_item(category_name, item_name):
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
def update_category(category_name):
    category = categories[category_name]
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Edit a category.",
                           entity = category,
                           cancel_url = cancel_url)


@app.route("/u/<category_name>", methods=["POST"])
def update_category_post(category_name):
    category = categories[category_name]
    old_name = category.name
    new_name = request.form["name"]
    if old_name != new_name:
        if new_name in categories:
            flash("The category name '{0}' already exists.".format(new_name))
            return redirect(url_for('update_category',
                                    category_name = old_name))

        items[new_name] = items[old_name]
        del items[old_name]
        for item in items[new_name].values():
            item.category_name = new_name

        categories[new_name] = categories[old_name]
        del categories[old_name]
        category.name = new_name

    category.description = request.form["description"]
    category.wiki_url = request.form["wiki"]
    session.add(category)
    session.commit()
    flash("The category has been updated.")
    return redirect(url_for('read_category', category_name = new_name))


@app.route("/u/<category_name>/<item_name>")
def update_item(category_name, item_name):
    item = items[category_name][item_name]
    cancel_url = url_for('read_item',
                         category_name = category_name,
                         item_name = item_name)
    return render_template("edit.html",
                           title = "Edit an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/u/<category_name>/<item_name>", methods=["POST"])
def update_item_post(category_name, item_name):
    category = categories[category_name]
    item = items[category_name][item_name]
    old_name = item.name
    new_name = request.form["name"]
    if old_name != new_name:
        if new_name in items[category_name]:
            flash("The item name '{0}' already exists in this category.".format(
                new_name))
            return redirect(url_for('update_item',
                                    category_name = category_name,
                                    item_name = item_name))

        items[category_name][new_name] = items[category_name][old_name]
        del items[category_name][old_name]
        item.name = new_name

    item.description = request.form["description"]
    item.wiki_url = request.form["wiki"]
    session.add(item)
    session.commit()
    flash("The item has been updated.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = new_name))


@app.route("/d/<category_name>", methods=["POST"])
def delete_category(category_name):
    for item in items[category_name].values():
        session.delete(item)
    del items[category_name]
    category = categories[category_name]
    session.delete(category)
    session.commit()
    del categories[category_name]
    flash("The category '{0}' has been deleted.".format(category_name))
    return redirect('/')


@app.route("/d/<category_name>/<item_name>", methods=["POST"])
def delete_item(category_name, item_name):
    category = categories[category_name]
    item = items[category_name][item_name]
    session.delete(item)
    session.commit()
    del items[category_name][item_name]
    flash("The item '{0}' has been deleted.".format(item_name))
    return redirect(url_for('read_category', category_name = category_name))


if __name__ == "__main__":
    for c in session.query(Category).all():
        categories[c.name] = c
    for item in session.query(Item).all():
        cname = [c for c in categories.values()
                 if c.cid == item.category_id][0].name
        item.category_name = cname
        items.setdefault(cname, {})[item.name] = item

    app.debug = True  # TODO
    app.run(host = "0.0.0.0", port = 8000)

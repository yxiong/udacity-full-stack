#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from database_setup import Base, Category, Item
from flask import Flask
from flask import render_template, url_for, request, redirect, flash
from flask import session as login_session
import httplib2
import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import os.path
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)
# Secret key generated with `os.urandom(24)`.
app.secret_key = '\x8bu\xc5\x87\x07$4\x83\xcbz\xfaB %\xc8\xf9A\xe2J=\x0e/"#'


# Database configuration.
engine = create_engine("sqlite:///catalog.db",
                       connect_args = {"check_same_thread":False}) # TODO
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
db_session = DBSession()


# Google+ authentication configuration.
client_secrets = json.loads(
    open("client_secrets.json", 'r').read())['web']['client_id']


# We use two in-memory dictionaries to cache the catalog data used by this app,
# which are read from the database when the app starts. When the user makes a
# create/update/delete request, we modify both the in-memory dictionaries as
# well as the underlying database and keep the two consistent all the time.
#
# The `categories` is a dictionary whose key is a the category name (which
# should be unique) and value is a `Category` object.
#
# The `items` is a dictionary of dictionary. For outer dictionary, the key is
# still category name, and for inner dictionary, the key is item name (which
# should be unique within a category) and value is an `Item` object. In other
# word, to access an item, use `items[category_name][item_name]`.
categories = {}
items = {}


@app.route("/")
def home():
    """Render the home page."""
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


@app.route("/login")
def login():
    """Render the login page."""
    state = os.urandom(16).encode('hex')
    login_session["state"] = state
    return render_template("login.html", state=state)


@app.route("/gconnect", methods=['POST'])
def gconnect():
    """Handle request to connect with a Google+ account."""
    # Make sure the user is the one who made the login request by checking if
    # he/she has the correct 'state' we gave them.
    if request.args.get("state") != login_session["state"]:
        return "Invalid state parameter", 401
    # Get the one-time-use code.
    code = request.data
    try:
        # Give the one-time-use authroization code to Google in exchange for a
        # credentials object.
        oauth_flow = flow_from_clientsecrets("client_secrets.json", scope="")
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return "Failed to verify the authorization code.", 401
    # Get the access token from the credentials object and check if it is valid.
    access_token = credentials.access_token
    url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?"
           "access_token={0}".format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])
    if result.get("error") is not None:
        # The access token we get from Google is invalid for some reason
        # (probably not our or user's fault).
        return json.dumps(result.get('error')), 500
    # Verify that the access token is used for the intended user and is valid
    # for this app.
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        return "Token's user ID doesn't match given user ID", 401
    if result["issued_to"] != client_secrets:
        return "Token's client ID does not match app's.", 401
    # Check if the user is already logged in.
    stored_gplus_id = login_session.get("gplus_id")
    if gplus_id == stored_gplus_id:
        flash("You already logged in as {0}".format(login_session["username"]))
        return "Current user is already logged in.", 200
    # Store the access toekn in the session for later use.
    login_session["access_token"] = access_token
    login_session["gplus_id"] = gplus_id
    # Get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt":"json"}
    answer = requests.get(userinfo_url, params = params)
    data = json.loads(answer.text)
    # Store the interested info into session.
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]
    # Logged in successfully.
    flash("You are now logged in as {0}".format(login_session["username"]))
    return "Logged in successfully.", 200


@app.route("/gdisconnect")
def gdisconnect():
    """Disconnect user's Google+ account."""
    # Check if the user is connected, i.e. if the user has an access token.
    access_token = login_session.get("access_token")
    if access_token is None:
        return "Current user is not connected.", 401
    # Execute HTTP GET request to revoke current token.
    url = ("https://accounts.google.com/o/oauth2/revoke?"
           "token={0}".format(access_token))
    h = httplib2.Http()
    result = h.request(url, "GET")[0]
    if result["status"] == "200":
        # Reset the user's session if the request is successful.
        del login_session["access_token"]
        del login_session["gplus_id"]
        del login_session["username"]
        del login_session["picture"]
        del login_session["email"]
        flash("You have successfully signed out.")
        return "Successfully disconnected.", 200
    else:
        # For some unknown reason, the token was invalid or cannot be
        # disconnected at this time.
        return "Error: Failed to revoke token for given user.", 400


@app.route("/c/category")
def create_category():
    """Render create category page."""
    if "username" not in login_session:
        return redirect("/login")
    category = Category(name="Category name",
                        description="Add some description.",
                        wiki_url = "http://www.wikipedia.org/xxx")
    return render_template("edit.html",
                           title = "Create a category.",
                           entity = category,
                           cancel_url = '/')


@app.route("/c/category", methods=["POST"])
def create_category_post():
    """Handle create category request."""
    if "username" not in login_session:
        return redirect("/login")
    name = request.form["name"]
    # Make sure the category name does not already exist.
    if name in categories:
        flash("Error: The category name '{0}' already exists.".format(name))
        return redirect(url_for('create_category'))
    # Create a `Category` object and add into database.
    category = Category(name=name,
                        description = request.form["description"],
                        wiki_url = request.form["wiki"])
    db_session.add(category)
    db_session.commit()
    # Update in-memory cache.
    categories[name] = category
    items[name] = {}
    flash("The category has been added.")
    return redirect(url_for('read_category', category_name = name))


@app.route("/c/<category_name>/item")
def create_item(category_name):
    """Render create item page."""
    if "username" not in login_session:
        return redirect("/login")
    item = Item(name="Item name",
                description="Add some description.",
                wiki_url = "http://www.wikipedia.org/xxx")
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Create an item.",
                           entity = item,
                           cancel_url = cancel_url)


@app.route("/c/<category_name>/item", methods=["POST"])
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
                category = categories[category_name])
    db_session.add(item)
    db_session.commit()
    # Update in-memory cache.
    item.category_name = category_name
    items[category_name][name] = item
    flash("The item has been added.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = name))


@app.route("/r/<category_name>")
def read_category(category_name):
    """Render read category page."""
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
    """Render read item page."""
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
    """Render update category page."""
    if "username" not in login_session:
        return redirect("/login")
    category = categories[category_name]
    cancel_url = url_for('read_category', category_name = category_name)
    return render_template("edit.html",
                           title = "Edit a category.",
                           entity = category,
                           cancel_url = cancel_url)


@app.route("/u/<category_name>", methods=["POST"])
def update_category_post(category_name):
    """Handle update category request."""
    if "username" not in login_session:
        return redirect("/login")
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
        categories[new_name] = categories[old_name]
        del categories[old_name]
        category.name = new_name
    # Update description and wiki url, and update into database.
    category.description = request.form["description"]
    category.wiki_url = request.form["wiki"]
    db_session.add(category)
    db_session.commit()
    flash("The category has been updated.")
    return redirect(url_for('read_category', category_name = new_name))


@app.route("/u/<category_name>/<item_name>")
def update_item(category_name, item_name):
    """Render update item page."""
    if "username" not in login_session:
        return redirect("/login")
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
    """Handle update item request."""
    if "username" not in login_session:
        return redirect("/login")
    category = categories[category_name]
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
    db_session.add(item)
    db_session.commit()
    flash("The item has been updated.")
    return redirect(url_for('read_item',
                            category_name = category_name,
                            item_name = new_name))


@app.route("/d/<category_name>", methods=["POST"])
def delete_category(category_name):
    """Handle delete category request."""
    if "username" not in login_session:
        return redirect("/login")
    # First delete the items inside the category.
    for item in items[category_name].values():
        db_session.delete(item)
    del items[category_name]
    # Then delete the category itself.
    category = categories[category_name]
    db_session.delete(category)
    db_session.commit()
    del categories[category_name]
    flash("The category '{0}' has been deleted.".format(category_name))
    return redirect('/')


@app.route("/d/<category_name>/<item_name>", methods=["POST"])
def delete_item(category_name, item_name):
    """Handle delete item request."""
    if "username" not in login_session:
        return redirect("/login")
    # Delete the item from the database.
    category = categories[category_name]
    item = items[category_name][item_name]
    db_session.delete(item)
    db_session.commit()
    # Delete from the in-memory cache as well.
    del items[category_name][item_name]
    flash("The item '{0}' has been deleted.".format(item_name))
    return redirect(url_for('read_category', category_name = category_name))


if __name__ == "__main__":
    # Read the categories and items from database into memory.
    for c in db_session.query(Category).all():
        categories[c.name] = c
    for item in db_session.query(Item).all():
        cname = [c for c in categories.values()
                 if c.cid == item.category_id][0].name
        item.category_name = cname
        items.setdefault(cname, {})[item.name] = item

    app.debug = True  # TODO
    app.run(host = "0.0.0.0", port = 8000)

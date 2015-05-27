#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

"""This module contains definition and utilities of our data model. The
utilities include getting and putting data from and to database as well as
memory cache, and keeping the two consistent."""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from werkzeug.contrib.cache import SimpleCache

from catalog import app

# TODO: These classes should be moved in this module.
from database_setup import Base
from database_setup import DATABASE_NAME
from database_setup import Category
from database_setup import Item


engine = create_engine(DATABASE_NAME)
Base.metadata.bind = engine
db_session = scoped_session(sessionmaker(bind = engine))


# Currently we cache following objects:
# * "categories": this is a dictionary whose key is a the category name (which
#   should be unique) and value is a `Category` object.
cache = SimpleCache()


def get_categories():
    """Get all categories in the database (likely from cache)."""
    categories = cache.get("categories")
    if categories:
        return categories
    categories = {}
    for c in db_session.query(Category).all():
        categories[c.name] = c
    cache.set("categories", categories)
    return categories


def get_category(category_name):
    """Get a category by name."""
    return get_categories()[category_name]


def add_category(category):
    """Add a category to the database and keep the cache consistent. This also
    works if the `category` is already in the database, in which case an update
    operation will be performed. However, if the category name is changed during
    the update, one needs to call `change_category_name_in_cache` first."""
    db_session.add(category)
    db_session.commit()
    categories = cache.get("categories")
    if categories:
        categories[category.name] = category
        cache.set("categories", categories)


def delete_category(category_name):
    """Delete a category from the database and the cache."""
    category = get_category(category_name)
    db_session.delete(category)
    db_session.commit()
    categories = cache.get("categories")
    if categories:
        del categories[category_name]
        cache.set("categories", categories)


def change_category_name_in_cache(old_name, new_name):
    """Since we use category name as key for cache and cached dictionaries, this
    function needs to be called whenever a category name changes. This function
    only update cache keys but not change the category object itself or touch
    the database."""
    categories = cache.get("categories")
    if categories:
        categories[new_name] = categories[old_name]
        del categories[old_name]
        cache.set("categories", categories)

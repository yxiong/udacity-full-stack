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
from database_setup import Item as DBItem


engine = create_engine(DATABASE_NAME)
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
db_session = scoped_session(sessionmaker(bind = engine))


# Currently we cache following objects:
#
# * "categories": this is a dictionary whose key is a the category name (which
#   should be unique) and value is a `Category` object.
#
# * "items/<category_name>": there is a dictionary for each `category_name`, and
#   the key of the dictionary is the item name (which should be unique within a
#   category) and the value is an `Item` object.
cache = SimpleCache()


def abbrev_text(text, n):
    """Abbreviate the input `text` to a maximum length `n`."""
    if len(text) < n:
        return text
    # Cut off at a whole word (delimited by space).
    cutoff = text.rfind(' ', 0, n-3)
    return text[:cutoff] + "..."


class MemCategory():
    def __init__(self, cid, name, description, wiki_url, last_modified):
        self.cid = cid
        self.name = name
        self.description = description
        self.wiki_url = wiki_url
        self.last_modified = last_modified

    @classmethod
    def from_db_category(cls, db_category):
        return cls(db_category.cid,
                   db_category.name,
                   db_category.description,
                   db_category.wiki_url,
                   db.last_modified)


class MemItem():
    def __init__(self, category, iid, name, description, wiki_url,
                 last_modified):
        self.category = category
        self.iid = iid
        self.name = name
        self.description = description
        self.wiki_url = wiki_url
        self.last_modified = last_modified

    def short_description(self, n):
        """Return a short version of the description."""
        return abbrev_text(self.description, n)

    @classmethod
    def from_db_item(cls, db_item, mem_category):
        return cls(mem_category,
                   db_item.iid,
                   db_item.name,
                   db_item.description,
                   db_item.wiki_url,
                   db_item.last_modified)


################################################################
# Utilities for getting and putting `Category`s.
################################################################
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
    return get_categories().get(category_name, None)


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


################################################################
# Utilities for getting and putting items.
################################################################
def get_items(category_name):
    """Get all items that belongs to the given category.

    * If the category does not exist, a `None` will be returned.
    * If the category exists but contains no item, an empty dictionary will be
      returned."""
    # Check cache first.
    items = cache.get("items/"+category_name)
    if items:
        return items
    # Make sure the `category_name` is valid.
    category = get_category(category_name)
    if not category:
        return None
    # Make a query to the database and copy the results to memory.
    items = {}
    session = DBSession()
    for i in session.query(DBItem).filter(
            DBItem.category_id == category.cid).all():
        items[i.name] = MemItem.from_db_item(i, category)
    session.close()
    cache.set("items/"+category_name, items)
    return items


def add_item(mem_item):
    # Add to database.
    db_item = DBItem(name = mem_item.name,
                     description = mem_item.description,
                     wiki_url = mem_item.wiki_url,
                     last_modified = mem_item.last_modified,
                     category_id = mem_item.category.cid)
    session = DBSession()
    session.add(db_item)
    session.commit()
    mem_item.iid = db_item.iid
    session.close()
    # Update in cache.
    items = cache.get("items/"+mem_item.category.name)
    if items:
        items[mem_item.name] = mem_item
        cache.set("items/"+mem_item.category.name, items)

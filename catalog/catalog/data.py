#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

"""This module contains definition and utilities of our data model. The
utilities include getting and putting data from and to database as well as
memory cache, and keeping the two consistent."""

import os.path

from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import UnicodeText
from werkzeug.contrib.cache import SimpleCache

from catalog import app


################################################################
# Configurations and models for database.
################################################################
_this_file_path = os.path.dirname(os.path.realpath(__file__))
DATABASE_NAME = "sqlite:///%s/catalog.db" % _this_file_path


engine = create_engine(DATABASE_NAME)
Base = declarative_base()
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)


class DBCategory(Base):
    __tablename__ = "category"

    cid = Column(Integer, Sequence("cid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))
    last_modified = Column(DateTime)


class DBItem(Base):
    __tablename__ = "item"

    iid = Column(Integer, Sequence("iid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))
    last_modified = Column(DateTime)
    category_id = Column(Integer, ForeignKey("category.cid"))

    category = relationship(DBCategory)


################################################################################
# Configurations and models for cache. Currently we cache following objects:
#
# * "categories": this is a dictionary whose key is a the category name (which
#   should be unique) and value is a `MemCategory` object.
#
# * "items/<category_name>": there is a dictionary for each `category_name`, and
#   the key of the dictionary is the item name (which should be unique within a
#   category) and the value is an `MemItem` object.
#
# * "latest_items": this is a list of `MemItem`s ordered by last modified time.
################################################################################
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
                   db_category.last_modified)


    def to_json(self):
        """Return a 'json-ready' dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "wiki_url": self.wiki_url,
            "last_modified": self.last_modified
        }


class MemItem():
    def __init__(self, category, iid, name, description, wiki_url,
                 last_modified):
        self.iid = iid
        self.name = name
        self.description = description
        self.wiki_url = wiki_url
        self.last_modified = last_modified
        self.category_id = category.cid
        self.category_name = category.name

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


    def to_json(self):
        """Return a 'json-ready' dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "wiki_url": self.wiki_url,
            "last_modified": self.last_modified
        }


################################################################
# Utilities for getting and putting categories.
################################################################
def get_categories():
    """Get all categories in the database (likely from cache)."""
    # Check cache first.
    categories = cache.get("categories")
    if categories:
        return categories
    # Make a query to the database and copy the results to memory.
    categories = {}
    session = DBSession()
    for c in session.query(DBCategory).all():
        categories[c.name] = MemCategory.from_db_category(c)
    session.close()
    cache.set("categories", categories)
    return categories


def get_category(category_name):
    """Get a category by name."""
    return get_categories().get(category_name, None)


def add_category(mem_category):
    """Add a category to the database and keep the cache consistent."""
    # Add to database.
    db_category = DBCategory(name = mem_category.name,
                             description = mem_category.description,
                             wiki_url = mem_category.wiki_url,
                             last_modified = mem_category.last_modified)
    session = DBSession()
    session.add(db_category)
    session.commit()
    mem_category.cid = db_category.cid
    session.close()
    # Update cache.
    categories = cache.get("categories")
    if categories:
        categories[mem_category.name] = mem_category
        cache.set("categories", categories)


def update_category(mem_category):
    """Update a category in database and in cache."""
    # Update the database.
    session = DBSession()
    db_category = session.query(DBCategory).filter_by(
        cid = mem_category.cid).first()
    db_category.name = mem_category.name
    db_category.description = mem_category.description
    db_category.wiki_url = mem_category.wiki_url
    db_category.last_modified = mem_category.last_modified
    session.commit()
    session.close()
    # Update cache.
    categories = cache.get("categories")
    if categories:
        categories[mem_category.name] = mem_category
        cache.set("categories", categories)


def delete_category(mem_category):
    """Delete a category from the database and the cache."""
    # Delete in database.
    session = DBSession()
    db_items = session.query(DBItem).filter_by(
        category_id = mem_category.cid).all()
    for i in db_items:
        session.delete(i)
    db_category = session.query(DBCategory).filter_by(
        cid = mem_category.cid).first()
    session.delete(db_category)
    session.commit()
    session.close()
    # Update cache.
    cache.delete("items/"+mem_category.name)
    categories = cache.get("categories")
    if categories:
        del categories[mem_category.name]
        cache.set("categories", categories)
    # Deleting a category will very likely remove one of the latest items.
    # Therefore we evict the cache.
    cache.delete("latest_items")


def change_category_name_in_cache(old_name, new_name):
    """Since we use category name as key for cache and cached dictionaries, this
    function needs to be called whenever a category name changes. This function
    only updates cache keys and cached objects but does not touch the
    database."""
    # Update `categories` in cache.
    categories = cache.get("categories")
    if categories:
        categories[new_name] = categories[old_name]
        del categories[old_name]
        categories[new_name].name = new_name
        cache.set("categories", categories)
    # Update `items/<category_name>` in cache.
    items = cache.get("items/"+old_name)
    if items:
        cache.delete("items/"+old_name)
        for i in items.values():
            i.category_name = new_name
        cache.set("items/"+new_name, items)
    # Update `latest_items` in cache.
    latest_items = cache.get("latest_items")
    if latest_items:
        for item in [i for i in latest_items if i.category_name==old_name]:
            item.category_name = new_name
        cache.set("latest_items", latest_items)


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
    for i in session.query(DBItem).filter_by(category_id = category.cid).all():
        items[i.name] = MemItem.from_db_item(i, category)
    session.close()
    cache.set("items/"+category_name, items)
    return items


def get_item(category_name, item_name):
    """Get the item by category name and item name. Return `None` if either
    argument is invalid."""
    items = get_items(category_name)
    if not items:
        return None
    else:
        return items.get(item_name, None)


def add_item(mem_item):
    """Add an item to database and update the cache correspondingly."""
    # Add to database.
    db_item = DBItem(name = mem_item.name,
                     description = mem_item.description,
                     wiki_url = mem_item.wiki_url,
                     last_modified = mem_item.last_modified,
                     category_id = mem_item.category_id)
    session = DBSession()
    session.add(db_item)
    session.commit()
    mem_item.iid = db_item.iid
    session.close()
    # Update cache.
    items = cache.get("items/"+mem_item.category_name)
    if items:
        items[mem_item.name] = mem_item
        cache.set("items/"+mem_item.category_name, items)
    latest_items = cache.get("latest_items")
    if latest_items:
        latest_items.insert(0, mem_item)
        latest_items.pop()
        cache.set("latest_items", latest_items)


def update_item(mem_item):
    """Update an item in database and in cache."""
    # Update in database.
    session = DBSession()
    db_item = session.query(DBItem).filter_by(iid = mem_item.iid).first()
    db_item.name = mem_item.name
    db_item.description = mem_item.description
    db_item.wiki_url = mem_item.wiki_url
    db_item.last_modified = mem_item.last_modified
    session.commit()
    session.close()
    # Update cache.
    items = cache.get("items/"+mem_item.category_name)
    if items:
        items[mem_item.name] = mem_item
        cache.set("items/"+mem_item.category_name, items)
    latest_items = cache.get("latest_items")
    if latest_items:
        item = next((i for i in latest_items if i.iid == mem_item.iid), None)
        if item:
            latest_items.remove(item)
        else:
            latest_items.pop()
        latest_items.insert(0, mem_item)
        cache.set("latest_items", latest_items)


def delete_item(mem_item):
    """Delete an item in database and in cache."""
    # Delete in database.
    session = DBSession()
    db_item = session.query(DBItem).filter_by(iid = mem_item.iid).first()
    session.delete(db_item)
    session.commit()
    session.close()
    # Update cache.
    items = cache.get("items/"+mem_item.category_name)
    if items:
        del items[mem_item.name]
        cache.set("items/"+mem_item.category_name, items)
    # In case the deleted item is one of the latest, we evict the 'latest_items'
    # cache because it takes another database query to replace the removed item.
    latest_items = cache.get("latest_items")
    if latest_items:
        item = next((i for i in latest_items if i.iid == mem_item.iid), None)
        if item:
            cache.delete("latest_items")


def change_item_name_in_cache(category_name, old_name, new_name):
    """Similar to `change_category_name_in_cache`, this function updates cache
    keys and cached objects but does not touch the database."""
    items = cache.get("items/"+category_name)
    if items:
        items[new_name] = items[old_name]
        del items[old_name]
        items[new_name].name = new_name
        cache.set("items/"+category_name, items)
    latest_items = cache.get("latest_items")
    if latest_items:
        item = next((i for i in latest_items if i.iid == items[new_name].iid),
                    None)
        if item:
            item.name = new_name
            cache.set("latest_items", latest_items)


def get_latest_items():
    """Retrieve the most recently modified items."""
    # Check cache first.
    latest_items = cache.get("latest_items")
    if latest_items:
        return latest_items
    # Make a query to the database and copy the results to memory.
    latest_items = []
    num = 10
    session = DBSession()
    db_items = session.query(DBItem).order_by(
        DBItem.last_modified.desc()).limit(num)
    categories = get_categories().values()
    for i in db_items:
        category = next(c for c in categories if c.cid == i.category_id)
        latest_items.append(MemItem.from_db_item(i, category))
    session.close()
    cache.set("latest_items", latest_items)
    return latest_items

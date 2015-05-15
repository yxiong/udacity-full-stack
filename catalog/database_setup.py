#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

"""This module defines the data model (ORM) of the catalog app. If invoked as a
script, it will create a database and inject with some initial data read from
raw UTF-8 unicode files in the `data/` directory."""

import os
import os.path
from sqlalchemy import Column, ForeignKey, Sequence, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import Integer, String, UnicodeText

Base = declarative_base()

def abbrev_text(text, n):
    """Abbreviate the input `text` to a maximum length `n`."""
    if len(text) < n:
        return text
    # Cut off at a whole word (delimited by space).
    cutoff = text.rfind(' ', 0, n-3)
    return text[:cutoff] + "..."

class Category(Base):
    __tablename__ = "category"

    cid = Column(Integer, Sequence("cid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))

    def short_description(self, n):
        """Return a short version of the description."""
        return abbrev_text(self.description, n)

    def __unicode__(self):
        return u"{0}: {1}. {2} [{3}]".format(
            self.cid, self.name, self.short_description(40), self.wiki_url)

    def __str__(self):
        return unicode(self).encode("utf-8")


class Item(Base):
    __tablename__ = "item"

    iid = Column(Integer, Sequence("iid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))
    category_id = Column(Integer, ForeignKey("category.cid"))

    category = relationship(Category)

    def short_description(self, n):
        """Return a short version of the description."""
        return abbrev_text(self.description, n)

    def __unicode__(self):
        return u"{0}: {1} (cid: {2}). {3} [{4}]".format(
            self.iid, self.name, self.category_id,
            self.short_description(40), self.wiki_url)

    def __str__(self):
        return unicode(self).encode("utf-8")


def read_raw_category_file(filename):
    """Read the content of a UTF-8 unicode file and parse them into a list of
    `Category`s. See `data/categories.txt` for format specification."""
    with open(filename, 'r') as f:
        rawlines = [l.decode("utf8").strip() for l in f.readlines()]
        # Skip empty and comment lines.
        lines = [l for l in rawlines if len(l) > 0 and not l.startswith('#')]
    # Each `Category` is consisted of a group of 3 consecutive lines.
    group = 3
    assert len(lines) % group == 0
    categories = []
    for i in xrange(len(lines) / group):
        categories.append(Category(
            name = lines[i*group],
            description = lines[i*group+1],
            wiki_url = lines[i*group+2]
        ))
    return categories


def read_raw_item_file(filename, categories_by_name):
    """Read the content of a UTF-8 unicode file and parse them into a list of
    `Item`s. See `data/items.txt` for format specification."""
    with open(filename, 'r') as f:
        rawlines = [l.decode("utf8").strip() for l in f.readlines()]
        lines = [l for l in rawlines if len(l) > 0 and not l.startswith('#')]
    # Each `Item` is consisted of a group of 4 consecutive lines.
    group = 4
    assert len(lines) % group == 0
    items = []
    for i in xrange(len(lines) / group):
        items.append(Item(
            name = lines[i*group],
            category = categories_by_name[lines[i*group+1]],
            description = lines[i*group+2],
            wiki_url = lines[i*group+3]
        ))
    return items


if __name__ == "__main__":
    # Remove the database file if already exists.
    if os.path.exists("catalog.db"):
        os.remove("catalog.db")

    # Create the database.
    engine = create_engine("sqlite:///catalog.db")
    Base.metadata.create_all(engine)

    # Make a session from the database engine.
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    session = DBSession()

    # Read category file and inject into database.
    raw_categories = read_raw_category_file("data/categories.txt")
    for rc in raw_categories:
        session.add(rc)
    session.commit()

    # Read categories from the database and index them by name.
    categories_by_name = {}
    for c in session.query(Category).all():
        categories_by_name[c.name] = c

    # Read item file and inject into database.
    raw_items = read_raw_item_file("data/items.txt", categories_by_name)
    for ri in raw_items:
        session.add(ri)
    session.commit()

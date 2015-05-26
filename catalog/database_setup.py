#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

"""This module defines the data model (ORM) of the catalog app. If invoked as a
script, it will create a database and inject with some initial data read from
raw UTF-8 unicode files in the `data/` directory."""

import json
import os
import os.path
from sqlalchemy import Column, ForeignKey, Sequence, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import Integer, String, UnicodeText

DATABASE_NAME = "sqlite:///catalog.db"

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


if __name__ == "__main__":
    # Remove the database file if already exists. This only works for sqlite.
    if DATABASE_NAME == "sqlite:///catalog.db" and os.path.exists("catalog.db"):
        os.remove("catalog.db")

    # Create the database.
    engine = create_engine(DATABASE_NAME)
    Base.metadata.create_all(engine)

    # Make a session from the database engine.
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    session = DBSession()

    # Read category file and inject into database.
    with open("data/categories.json", 'r') as f:
        categories_json = json.load(f)
    for c in categories_json:
        session.add(Category(
            name = c["name"],
            description = c["description"],
            wiki_url = c["wiki_url"]
        ))
    session.commit()

    # Read categories from the database and index them by name.
    categories_by_name = {}
    for c in session.query(Category).all():
        categories_by_name[c.name] = c

    # Read item file and inject into database.
    with open("data/items.json", 'r') as f:
        items_json = json.load(f)
    for i in items_json:
        session.add(Item(
            name = i["name"],
            category = categories_by_name[i["category"]],
            description = i["description"],
            wiki_url = i["wiki_url"]
        ))
    session.commit()

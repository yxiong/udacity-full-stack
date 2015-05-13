#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

import os
import os.path
from sqlalchemy import Column, ForeignKey, Sequence, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import Integer, String, UnicodeText

Base = declarative_base()

def abbrev_text(text, n):
    """TODO: Add docs."""
    if len(text) < n:
        return text
    cutoff = text.rfind(' ', 0, n-3)
    return text[:cutoff] + "..."

class Category(Base):
    """TODO: Add docs."""
    __tablename__ = "category"

    cid = Column(Integer, Sequence("cid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))

    def short_description(self, n):
        return abbrev_text(self.description, n)

    def __unicode__(self):
        abbrev_description = abbrev_text(self.description, 40)
        return u"{0}: {1}. {2} [{3}]".format(
            self.cid, self.name, abbrev_description, self.wiki_url)

    def __str__(self):
        return unicode(self).encode("utf-8")


class Item(Base):
    """TODO: Add docs."""
    __tablename__ = "item"

    iid = Column(Integer, Sequence("iid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    wiki_url = Column(String(255))
    category_id = Column(Integer, ForeignKey("category.cid"))

    category = relationship(Category)

    def short_description(self, n):
        return abbrev_text(self.description, n)

    def __unicode__(self):
        abbrev_description = abbrev_text(self.description, 40)
        return u"{0}: {1} (cid: {2}). {3} [{4}]".format(
            self.iid, self.name, self.category_id,
            abbrev_description, self.wiki_url)

    def __str__(self):
        return unicode(self).encode("utf-8")


def read_raw_category_file(filename):
    """TODO: Add docs."""
    with open(filename, 'r') as f:
        rawlines = [l.decode("utf8").strip() for l in f.readlines()]
        lines = [l for l in rawlines if len(l) > 0 and not l.startswith('#')]
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
    """TODO: Add docs."""
    with open(filename, 'r') as f:
        rawlines = [l.decode("utf8").strip() for l in f.readlines()]
        lines = [l for l in rawlines if len(l) > 0 and not l.startswith('#')]
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

    # TODO: Remove the following test code.
    for c in session.query(Category).all():
        print c
    for i in session.query(Item).all():
        print i

    cc = session.query(Category).all()

    item = session.query(Item).filter_by(name = "Boston").one()
    item.description = u"The city I am living in."
    session.add(item)
    session.commit()
    print item.description

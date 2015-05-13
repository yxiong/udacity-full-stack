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

class Category(Base):
    __tablename__ = "category"

    cid = Column(Integer, Sequence("cid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)

    def __str__(self):
        return "{0}: {1}".format(self.cid, self.name)


class Item(Base):
    __tablename__ = "item"

    iid = Column(Integer, Sequence("iid_seq"), primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    category_id = Column(Integer, ForeignKey("category.cid"))

    category = relationship(Category)

    def __str__(self):
        return "{0}: {1}".format(self.iid, self.name)


if __name__ == "__main__":
    if os.path.exists("catalog.db"):
        os.remove("catalog.db")

    engine = create_engine("sqlite:///catalog.db")
    Base.metadata.create_all(engine)

    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    session = DBSession()

    with open("data/categories.txt", 'r') as f:
        lines = f.read()
        categories = [l.strip() for l in lines.split('\n')
                      if len(l.strip()) > 0]
    for c in categories:
        session.add(Category(name = c))
    session.commit()

    category_by_name = {}
    for c in session.query(Category).all():
        category_by_name[c.name] = c

    separator = "================"
    with open("data/items.txt", 'r') as f:
        rawlines = [l.decode("utf8").strip() for l in f.readlines()]
        lines = [l for l in rawlines if len(l) > 0 and l != separator]
    group = 4
    assert len(lines) % group == 0
    for i in xrange(len(lines) / group):
        name = lines[i*group]
        category = category_by_name[lines[i*group+1]]
        description = lines[i*group+2]
        item = Item(name = name,
                    description = description,
                    category = category)
        session.add(item)
    session.commit()

    myFirstCategory = Category(cid = 1000, name = "USA")
    session.add(myFirstCategory)
    session.commit()
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

#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from sqlalchemy import Column, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import Integer, String, UnicodeText

Base = declarative_base()


class Category(Base):
    __tablename__ = "category"

    cid = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)


class Item(Base):
    __tablename__ = "item"

    iid = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    description = Column(UnicodeText)
    category_id = Column(Integer, ForeignKey("category.cid"))

    category = relationship(Category)


if __name__ == "__main__":
    engine = create_engine("sqlite:///catalog.db")
    Base.metadata.create_all(engine)

    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    session = DBSession()

    myFirstCategory = Category(cid = 1, name = "USA")
    session.add(myFirstCategory)
    session.commit()
    print session.query(Category).all()

    myFirstItem = Item(iid = 1, name = "Boston", category_id = 1,
                       description = u"The city I lived in.",
                       category = myFirstCategory)
    session.add(myFirstItem)
    session.commit()
    print session.query(Item).first().name

    item = session.query(Item).filter_by(name = "Boston").one()
    item.description = u"The city I am living in."
    session.add(item)
    session.commit()
    print item.description

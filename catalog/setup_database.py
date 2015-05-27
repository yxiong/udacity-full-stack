#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

"""This module defines the data model (ORM) of the catalog app. If invoked as a
script, it will create a database and inject with some initial data read from
raw UTF-8 unicode files in the `data/` directory."""

from datetime import datetime
import json
import os
import os.path

from catalog.data import Base
from catalog.data import DATABASE_NAME
from catalog.data import DBCategory as Category
from catalog.data import DBItem as Item
from catalog.data import DBSession
from catalog.data import engine


if __name__ == "__main__":
    # Remove the database file if already exists. This only works for sqlite.
    if DATABASE_NAME == "sqlite:///catalog.db" and os.path.exists("catalog.db"):
        os.remove("catalog.db")

    # Create the database and make a session from the engine.
    Base.metadata.create_all(engine)
    session = DBSession()

    # Read category file and inject into database.
    with open("data/categories.json", 'r') as f:
        categories_json = json.load(f)
    for c in categories_json:
        session.add(Category(
            name = c["name"],
            description = c["description"],
            wiki_url = c["wiki_url"],
            last_modified = datetime.strptime(c["last_modified"],
                                              "%d %b %Y, at %H:%M")
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
            wiki_url = i["wiki_url"],
            last_modified = datetime.strptime(i["last_modified"],
                                              "%d %b %Y, at %H:%M")
        ))
    session.commit()

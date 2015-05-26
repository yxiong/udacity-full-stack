#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog import app
from catalog import Base
from catalog import DATABASE_NAME
from catalog import DBSession
from catalog import db_session
from catalog import engine

if __name__ == "__main__":
    # When the app is launched in debug mode, sqlite has a multi-thread issue,
    # which we try to circumvent by re-creating the engine and session with
    # `check_same_thread=False` argument.
    app.debug = True
    engine = create_engine(DATABASE_NAME,
                           connect_args={"check_same_thread": False})
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind = engine)
    db_session = DBSession()

    # Launch the application.
    app.run(host = "0.0.0.0", port = 8000)

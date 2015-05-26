#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import catalog
from catalog import app

if __name__ == "__main__":
    # When the app is launched in debug mode, sqlite has a multi-thread issue,
    # which we try to circumvent by re-creating the engine and session with
    # `check_same_thread=False` argument.
    app.debug = True
    catalog.engine = create_engine(catalog.DATABASE_NAME,
                                   connect_args={"check_same_thread": False})
    catalog.Base.metadata.bind = catalog.engine
    catalog.DBSession = sessionmaker(bind = catalog.engine)
    catalog.db_session = catalog.DBSession()

    # Launch the application.
    app.run(host = "0.0.0.0", port = 8000)

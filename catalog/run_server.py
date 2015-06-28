#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import catalog
from catalog import app

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 8000)

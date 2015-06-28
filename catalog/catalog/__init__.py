#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from flask import Flask
from flask.ext.seasurf import SeaSurf


# These definitions need to come before importing any module in current
# directory, in order to avoid circular import issues.
app = Flask(__name__)
app.config.from_object("catalog.default_config")
app.config.from_envvar("CATALOG_CONFIG_FILE", silent=True)
csrf = SeaSurf(app)


import catalog.api
import catalog.create
import catalog.data
import catalog.delete
import catalog.login
import catalog.read
import catalog.update

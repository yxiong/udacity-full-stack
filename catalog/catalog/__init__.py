#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 11, 2015.

from flask import Flask
from flask.ext.seasurf import SeaSurf


# These definitions need to come before importing any module in current
# directory, in order to avoid circular import issues.
app = Flask(__name__)
csrf = SeaSurf(app)


import catalog.api
import catalog.create
import catalog.data
import catalog.delete
import catalog.login
import catalog.read
import catalog.update


# Secret key generated with `os.urandom(24)`.
app.secret_key = '\x8bu\xc5\x87\x07$4\x83\xcbz\xfaB %\xc8\xf9A\xe2J=\x0e/"#'

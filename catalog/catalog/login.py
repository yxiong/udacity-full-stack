#!/usr/bin/env python
#
# Author: Ying Xiong.
# Created: May 26, 2015.

from functools import wraps
import json
import os

from flask import flash
from flask import render_template
from flask import request
from flask import session as login_session
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests

from catalog import app
from catalog import csrf


# Google+ authentication configuration.
_this_file_path = os.path.dirname(os.path.realpath(__file__))
client_id = json.loads(open(
    _this_file_path + "/client_secrets.json", 'r').read())['web']['client_id']


@app.route("/login")
def login():
    """Render the login page."""
    state = os.urandom(16).encode('hex')
    login_session["state"] = state
    return render_template("login.html", state=state, client_id = client_id)


@csrf.exempt
@app.route("/gconnect", methods=['POST'])
def gconnect():
    """Handle request to connect with a Google+ account."""
    # Make sure the user is the one who made the login request by checking if
    # he/she has the correct 'state' we gave them.
    if request.args.get("state") != login_session["state"]:
        return "Invalid state parameter", 401
    # Get the one-time-use code.
    code = request.data
    try:
        # Give the one-time-use authroization code to Google in exchange for a
        # credentials object.
        oauth_flow = flow_from_clientsecrets(
            _this_file_path + "/client_secrets.json", scope="")
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return "Failed to verify the authorization code.", 401
    # Get the access token from the credentials object and check if it is valid.
    access_token = credentials.access_token
    url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?"
           "access_token={0}".format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])
    if result.get("error") is not None:
        # The access token we get from Google is invalid for some reason
        # (probably not our or user's fault).
        return json.dumps(result.get('error')), 500
    # Verify that the access token is used for the intended user and is valid
    # for this app.
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        return "Token's user ID doesn't match given user ID", 401
    if result["issued_to"] != client_id:
        return "Token's client ID does not match app's.", 401
    # Check if the user is already logged in.
    stored_gplus_id = login_session.get("gplus_id")
    if gplus_id == stored_gplus_id:
        flash("You already logged in as {0}".format(login_session["username"]))
        return "Current user is already logged in.", 200
    # Store the access toekn in the session for later use.
    login_session["access_token"] = access_token
    login_session["gplus_id"] = gplus_id
    # Get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt":"json"}
    answer = requests.get(userinfo_url, params = params)
    data = json.loads(answer.text)
    # Store the interested info into session.
    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]
    # Logged in successfully.
    flash("You are now logged in as {0}".format(login_session["username"]))
    return "Logged in successfully.", 200


@app.route("/gdisconnect")
def gdisconnect():
    """Disconnect user's Google+ account."""
    # Check if the user is connected, i.e. if the user has an access token.
    access_token = login_session.get("access_token")
    if access_token is None:
        return "Current user is not connected.", 401
    # Execute HTTP GET request to revoke current token.
    url = ("https://accounts.google.com/o/oauth2/revoke?"
           "token={0}".format(access_token))
    h = httplib2.Http()
    result = h.request(url, "GET")[0]
    if result["status"] == "200":
        # Reset the user's session if the request is successful.
        del login_session["access_token"]
        del login_session["gplus_id"]
        del login_session["username"]
        del login_session["picture"]
        del login_session["email"]
        flash("You have successfully signed out.")
        return "Successfully disconnected.", 200
    else:
        # For some unknown reason, the token was invalid or cannot be
        # disconnected at this time.
        return "Error: Failed to revoke token for given user.", 400


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kw):
        if "username" not in login_session:
            return redirect(url_for('login'))
        return f(*args, **kw)
    return decorated_function

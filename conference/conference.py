#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'


from datetime import datetime
import json
import os
import time

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import StringMessage
from models import BooleanMessage
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import TeeShirtSize
from models import Session
from models import SessionForm
from models import SessionForms
from models import SessionType

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_SPEAKER_KEY_PREFIX = "FEATURED_SPEAKER-"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": [ "Default", "Topic" ],
}

SESSION_DEFAULTS = {
    "highlights": [ "Default", "Highlight" ],
    "speaker": "Default speaker",
    "duration": "0",
    "typeOfSession": "NOT_SPECIFIED",
}

OPERATORS = {
            'EQ':   '=',
            'GT':   '>',
            'GTEQ': '>=',
            'LT':   '<',
            'LTEQ': '<=',
            'NE':   '!='
            }

FIELDS =    {
            'CITY': 'city',
            'TOPIC': 'topics',
            'MONTH': 'month',
            'MAX_ATTENDEES': 'maxAttendees',
            }

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_BY_TYPE_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2),
)

SESSION_BY_SPEAKER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speaker=messages.StringField(1),
)

SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1),
)

SESSION_BY_DATE_TIME_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    date=messages.StringField(1),
    startTimeBegin=messages.StringField(2),
    startTimeEnd=messages.StringField(3),
)

SESSION_BY_TYPE_DURATION_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    typeOfSession=messages.StringField(1),
    durationMin=messages.StringField(2),
    durationMax=messages.StringField(3),
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def _getUserId():
    """A workaround implementation for getting userid."""
    auth = os.getenv('HTTP_AUTHORIZATION')
    bearer, token = auth.split()
    token_type = 'id_token'
    if 'OAUTH_USER_ID' in os.environ:
        token_type = 'access_token'
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
           % (token_type, token))
    user = {}
    wait = 1
    for i in range(3):
        resp = urlfetch.fetch(url)
        if resp.status_code == 200:
            user = json.loads(resp.content)
            break
        elif resp.status_code == 400 and 'invalid_token' in resp.content:
            url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
                   % ('access_token', token))
        else:
            time.sleep(wait)
            wait = wait + i
    return user.get('user_id', '')


def _entityByKindAndUrlsafeKeyOrNone(kind, websafeKey):
    """A helper function that turns a `kind` and a `websafeKey string` to an
    DataStore entity object.

    This function checks (and only checks) the following error cases:
    - if `websafeKey` is an invalid string, i.e. one that is not produced by `Key.urlsafe()`
    - if `websafeKey` is valid, but the key is not associated with `kind`
    - if `websafeKey` is associated with `kind` but does not exist in the database

    If any of the error above happens, the function swallows any exception and
    returns `None`, but other errors different than above can still cause an
    exception thrown (e.g. if `websafeKey` is not a string, a `TypeError` can
    still be thrown).

    See http://stackoverflow.com/questions/30337240/ for reference.
    """
    try:
        key = ndb.Key(urlsafe=websafeKey)
        entity = key.get()
        if entity and key.kind() == kind._get_kind():
            return entity
        else:
            return None
    except ProtocolBufferDecodeError:
        return None


@endpoints.api(name='conference', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf


    def _createConferenceObject(self, request):
        """Create or update Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = _getUserId()

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
            'conferenceInfo': repr(request)},
            url='/tasks/send_confirmation_email'
        )
        return request


    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = _getUserId()

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
            http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)


    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)


    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='getConferencesCreated',
            http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, _getUserId()))
        prof = ndb.Key(Profile, _getUserId()).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, getattr(prof, 'displayName')) for conf in confs]
        )


    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q


    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException("Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous filters
                # disallow the filter if inequality was performed on a different field before
                # track the field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException("Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)


    @endpoints.method(ConferenceQueryForms, ConferenceForms,
            path='queryConferences',
            http_method='POST',
            name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
                items=[self._copyConferenceToForm(conf, names[conf.organizerUserId]) for conf in \
                conferences]
        )


# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name, getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf


    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = _getUserId()
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key = p_key,
                displayName = user.nickname(),
                mainEmail= user.email(),
                teeShirtSize = str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile      # return Profile


    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        #if field == 'teeShirtSize':
                        #    setattr(prof, field, str(val).upper())
                        #else:
                        #    setattr(prof, field, val)
                        prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)


    @endpoints.method(message_types.VoidMessage, ProfileForm,
            path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()


    @endpoints.method(ProfileMiniForm, ProfileForm,
            path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)


# - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='conference/announcement/get',
            http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='conference/announcement/put',
            http_method='GET', name='putAnnouncement')
    def putAnnouncement(self, request):
        """Put Announcement into memcache"""
        return StringMessage(data=self._cacheAnnouncement())


# - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser() # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='conferences/attending',
            http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser() # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, names[conf.organizerUserId])\
         for conf in conferences]
        )


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)


# - - - Session objects - - - - - - - - - - - - - - - - -

    def _copySessionToForm(self, session):
        """Copy the relavent fields from Session to SessionForm."""
        sf = SessionForm()
        for field in sf.all_fields():
            # Need special treatment for `date` and `startTime` fields.
            if field.name in ("date", "startTime", "duration"):
                setattr(sf, field.name, str(getattr(session, field.name)))
            elif field.name == "typeOfSession":
                sf.typeOfSession = SessionType(session.typeOfSession)
            elif field.name == "websafeKey":
                sf.websafeKey = session.key.urlsafe()
            elif field.name == "websafeConferenceKey":
                sf.websafeConferenceKey = session.key.parent().urlsafe()
            elif hasattr(session, field.name):
                # name, highlights and speaker.
                setattr(sf, field.name, getattr(session, field.name))
            else:
                raise endpoints.InternalServerErrorException(
                    "Unexpected field name '%s'." % field.name)
        sf.check_initialized()
        return sf

    def _createSessionObject(self, request):
        """Create Session object, returning SessionForm/request."""
        # Authenticate user.
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = _getUserId()

        # Check that the request has a session name.
        if not request.name:
            raise endpoints.BadRequestException("Session 'name' field required")

        # Check that the request has a valid websafeConferenceKey.
        if not request.websafeConferenceKey:
            raise endpoints.BadRequestException("Session 'websafeConferenceKey' field required")
        conference = _entityByKindAndUrlsafeKeyOrNone(Conference, request.websafeConferenceKey)
        if not conference:
            raise endpoints.BadRequestException("Session 'websafeConferenceKey' field invalid")

        # Make sure the user is the conference organizer.
        if conference.organizerUserId != user_id:
            raise endpoints.UnauthorizedException('The user is not the conference organizer')

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['websafeConferenceKey']

        # convert the date and startTime into Date/Time properties
        if data['date']:
            data['date'] = datetime.strptime(data['date'], "%Y-%m-%d").date()
        if data['startTime']:
            data['startTime'] = datetime.strptime(data['startTime'], "%H:%M").time()

        # add default values for missing fields
        for df in SESSION_DEFAULTS:
            if data[df] in (None, []):
                data[df] = SESSION_DEFAULTS[df]

        # perform necessary type conversion
        data["typeOfSession"] = str(data["typeOfSession"])
        data["duration"] = int(data["duration"])

        # generate Session ID based on Conference key and get Session key from ID.
        sessionId = Session.allocate_ids(size=1, parent=conference.key)[0]
        sessionKey = ndb.Key(Session, sessionId, parent=conference.key)
        data['key'] = sessionKey

        # create Session
        session = Session(**data)
        session.put()

        # Check if the speaker should be featured. The current session has been put into Data Store by now.
        if data['speaker'] != SESSION_DEFAULTS['speaker']:
            taskqueue.add(
                params={
                    'speaker': data['speaker'],
                    'websafeConferenceKey': request.websafeConferenceKey,
                },
                url='/tasks/check_featured_speaker'
            )

        # send email to creater confirming creation of Session
        # TODO

        return self._copySessionToForm(session)

    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path='sessionByConference/{websafeConferenceKey}',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Given a conference, return all sessions."""
        # get Conference object from request; bail if not found
        conference = _entityByKindAndUrlsafeKeyOrNone(Conference, request.websafeConferenceKey)
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s.' % request.websafeConferenceKey)

        # create ancestor query for all key matches for this conference
        sessions = Session.query(ancestor=conference.key)

        # return set of SessionForm objects per Session
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

    @endpoints.method(SESSION_BY_TYPE_REQUEST, SessionForms,
                      path='sessionByType/{websafeConferenceKey}/{typeOfSession}',
                      http_method='GET', name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Given a conference, return all sessions of a specified type
        (e.g. lecture, keynote, workshop)"""
        # get Conference object from request; bail if not found
        conference = _entityByKindAndUrlsafeKeyOrNone(Conference, request.websafeConferenceKey)
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s.' % request.websafeConferenceKey)
        # check if typeOfSession is one of the enum type
        if request.typeOfSession not in SessionType.to_dict():
            raise endpoints.BadRequestException(
                'Invalid session type: %s' % request.typeOfSession)
        # query session by ancestor and then filter with session type
        sessions = Session.query(ancestor=conference.key).filter(
            Session.typeOfSession == request.typeOfSession)
        # return set of SessionForm objects per Session
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

    @endpoints.method(SESSION_BY_SPEAKER_REQUEST, SessionForms,
                      path='sessionBySpeaker/{speaker}',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Given a speaker, return all sessions given by this particular speaker,
        across all conferences."""
        sessions = Session.query(Session.speaker == request.speaker)
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

    @endpoints.method(SessionForm, SessionForm, path='session',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)

    @endpoints.method(SESSION_BY_DATE_TIME_REQUEST, SessionForms,
                      path='sessionByDateTime/{date}/{startTimeBegin}/{startTimeEnd}',
                      http_method='GET', name='getSessionsByDateTime')
    def getSessionsByDateTime(self, request):
        """Given a `date` and `startTime` range, return all sessions within this time
        frame, across all conferences."""
        # Create a query for the request.
        #
        # Note that we use "%H%M" for time format (e.g. "0700", "1830"), instead
        # of the regular "%H:%M" (e.g. "07:00", "18:30"), because the latter
        # cuase some url parsing problems in the endpoint api.
        sessions = Session.query(
            Session.date == datetime.strptime(request.date, "%Y-%m-%d").date()
        ).filter(
            Session.startTime >= datetime.strptime(request.startTimeBegin, "%H%M").time()
        ).filter(
            Session.startTime <= datetime.strptime(request.startTimeEnd, "%H%M").time()
        )
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

    @endpoints.method(SESSION_BY_TYPE_DURATION_REQUEST, SessionForms,
                      path='sessionByTypeDuration/{typeOfSession}/{durationMin}/{durationMax}',
                      http_method='GET', name='getSessionsByTypeDuration')
    def getSessionsByTypeDuration(self, request):
        """Given a `typeOfSession` and a duration limit, return all sessions of the
        specified type and within the required duration limit."""
        sessions = Session.query(
            Session.typeOfSession == request.typeOfSession
        ).filter(
            Session.duration >= int(request.durationMin)
        ).filter(
            Session.duration <= int(request.durationMax)
        )
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

# - - - Session Wishlist - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    @endpoints.method(SESSION_GET_REQUEST, BooleanMessage,
                      path='sessionWishlist/{websafeSessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Adds the session to the user's list of sessions they are interested in
        attending."""
        # get user Profile
        profile = self._getProfileFromUser()

        # check the validity of websafeSessionKey.
        session = _entityByKindAndUrlsafeKeyOrNone(Session, request.websafeSessionKey)
        if not session:
            raise endpoints.NotFoundException(
                'No session found with key: %s' % request.websafeSessionKey)

        # check if user already have this session in the wishlist
        if request.websafeSessionKey in profile.sessionKeysWishlist:
            raise ConflictException(
                "You have already added this session to your wish list")

        # add to wish list
        profile.sessionKeysWishlist.append(request.websafeSessionKey)
        profile.put()
        return BooleanMessage(data=True)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='sessionWishlist',
                      http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Query for all the sessions in a conference that the user is interested in"""
        # get user Profile
        profile = self._getProfileFromUser()

        # Get sessions in the wish list.
        sessionKeys = [ndb.Key(urlsafe=k) for k in profile.sessionKeysWishlist]
        sessions = ndb.get_multi(sessionKeys)

        # return set of SessionForm objects per Session
        return SessionForms(items=[self._copySessionToForm(s) for s in sessions])

# - - - Featured speaker - - - - - - - - - - - - - - - - - - - -
    @endpoints.method(CONF_GET_REQUEST, StringMessage,
                      path='featuredSpeaker/{websafeConferenceKey}',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Get the featured speaker for given conference."""
        # check the validity of websafeConferenceKey.
        conference = _entityByKindAndUrlsafeKeyOrNone(Conference, request.websafeConferenceKey)
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        response = memcache.get(
            MEMCACHE_FEATURED_SPEAKER_KEY_PREFIX+request.websafeConferenceKey)
        if response is None:
            response = ""
        return StringMessage(data = response)

    @staticmethod
    def _checkFeaturedSpeaker(speaker, websafeConferenceKey):
        """Helper function to check and update featured speaker for a given conference."""
        # Check that the request has a valid websafeConferenceKey.
        conference = _entityByKindAndUrlsafeKeyOrNone(Conference, websafeConferenceKey)
        if not conference:
            raise endpoints.BadRequestException("Session 'websafeConferenceKey' field invalid")
        # Get all sessions by this speaker and see if there is more than one.
        sessionsBySameSpeaker = [s for s in Session.query(
            ancestor=conference.key).filter(Session.speaker == speaker)]
        if len(sessionsBySameSpeaker) > 1:
            # Feature this speaker. Note that we only have one featured
            # speaker for each conference at one time, and therefore this
            # speaker might 'evict' the current featured speaker.
            sessionNames = [s.name for s in sessionsBySameSpeaker]
            memcache.set(
                MEMCACHE_FEATURED_SPEAKER_KEY_PREFIX+websafeConferenceKey,
                speaker + ": " + ", ".join(sessionNames)
            )

api = endpoints.api_server([ConferenceApi]) # register API

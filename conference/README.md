App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting your local server's address (by default [localhost:8080][5].)
1. (Optional) Generate your client library(ies) with [the endpoints tool][6].
1. Deploy your application.


[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool


## Task 1: Add Sessions to Conference

We created a `Session` model that contains 7 fields: `name`, `highlights`,
`speaker`, `duration`, `typeOfSession`, `date` and `startTime`. A `Session` key
will have a `Conference` key as its parent.

We also create a corresponding `SessionForm` for RPC protocol buffer
communication. This form contains additional `websafeKey` to identify this
session, and `websafeConferenceKey` to identify the conference this session
belongs to.

With these data structures, we implemented four endpoints methods:
`getConferenceSessions`, `getConferenceSessionsByType`, `getSessionsBySpeaker`
and `createSession`.


## Task 2: Add Sessions to User Wishlist

We added a repeated field `sessionKeyWishlist` to `Profile` model to keep track
of user's wishlist. Correspondingly, we implemented two endpoints methods
`addSessionToWishlist` and `getSessionsInWishlist`.


## Task 3: Work on indexes and queries

We added two additional query types:

  * `getSessionsByDateTime`: Given a `date` and `startTime` range, return all
    sessions within this time frame, across all conferences.
  * `getSessionsByTypeDuration`: Given a `typeOfSession` and a duration limit,
    return all sessions of the specified type and within the required duration
    limit.

We launch the app in local machine to automatically generate the required
indexes, and deploy those indexes to the server.

For the "don't like workshops and don't like sessions after 7pm" query, it can
not simply be done with ndb query, because it will require two inequality
condition applied to two different fields (`typeOfSession` and `startTime`),
which is not allowed in DataStore.

One way around this problem implement one query with ndb and perform the other
in memory. For example, one can get all the sessions before 7pm with an ndb
query, and then filter out workshops by looking at each session in memory.


## Task 4: Add a Task

We used `memcache` to implement featured speaker. When a new session is added to
conference, we check whether there is more than one session by the same speaker
at this conference, and if so, ad a `memcache` entry that features the speaker
and session names. Note that each conference can only have one featured speaker
at one time, and new speaker might 'evict' old ones.

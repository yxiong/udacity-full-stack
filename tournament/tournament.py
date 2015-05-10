#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def updateDatabaseHelper(*args):
    """This helper function will connect to database, get a cursor, execute the
    update command, commit the change and finally close the connection. The
    input arguments `*args` will be directly forwarded to the `cursor.execute`
    function.
    """
    db = connect()
    c = db.cursor()
    c.execute(*args)
    db.commit()
    db.close()


def queryDatabaseHelper(*args):
    """This helper function will connect to database, get a cursor, execute the
    query command, fetch all results, close the connection and finally return
    the fetched results. The input arguments `*args` will be directly forwarded
    to the `cursor.execute` function.
    """
    db = connect()
    c = db.cursor()
    c.execute(*args)
    result = c.fetchall()
    db.close()
    return result


def deleteMatches():
    """Remove all the match records from the database."""
    updateDatabaseHelper("DELETE FROM Matches;")


def deletePlayers():
    """Remove all the player records from the database."""
    updateDatabaseHelper("DELETE FROM Players;")


def countPlayers():
    """Returns the number of players currently registered."""
    # Return the first row and first column of the count query results.
    return queryDatabaseHelper("SELECT COUNT(*) FROM Players;")[0][0]


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    updateDatabaseHelper("INSERT INTO Players (pname) VALUES (%s);", (name,))


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    # Join the 'Players' table and 'PlayerRecords' view to get players' name,
    # their winning records as well as total number of matches the have played.
    command = r"""SELECT pid, Players.pname, PlayerRecords.wins,
                         (PlayerRecords.wins + PlayerRecords.losts) AS total
                  FROM Players NATURAL JOIN PlayerRecords
                  ORDER BY PlayerRecords.wins DESC;"""
    return queryDatabaseHelper(command)


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    updateDatabaseHelper("INSERT INTO Matches VALUES (%s, %s);", (winner, loser))

 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    # TODO: Current implementation passes the included tests but it would not
    # work for an actual Swiss Tournament setup. One of the primary rules of the
    # system is opponents can only face each other once. See here for additional
    # details on the basic rule set.
    # http://en.wikipedia.org/wiki/Swiss-system_tournament.

    # Join the 'Players' table and 'PlayerRecords' view so that we can sort the
    # players according to number of games they won.
    command = r"""SELECT pid, Players.pname, PlayerRecords.wins
                  FROM Players NATURAL JOIN PlayerRecords
                  ORDER BY PlayerRecords.wins DESC;"""
    r = queryDatabaseHelper(command)
    # Each player is paired with an adjacent player in the standings.
    return [(r[i][0], r[i][1], r[i+1][0], r[i+1][1])
            for i in xrange(0, len(r), 2)]

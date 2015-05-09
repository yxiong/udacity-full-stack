-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE TABLE Players ( pid SERIAL PRIMARY KEY,
                       pname varchar(255) );

CREATE TABLE Matches ( winner int,
                       loser int );


-- Create a player records view storing each player's winning and losing times.
-- For players who have not played any game, both counts should be 0.

CREATE VIEW PlayerRecords AS
       SELECT Players.pid,
              ( CASE WHEN Winning.times is NULL
                THEN 0 ELSE Winning.times END ) AS wins,
              ( CASE WHEN Losing.times is NULL
                THEN 0 ELSE Losing.times END ) AS losts
       FROM Players
            LEFT JOIN ( SELECT winner AS pid, COUNT(*) AS times FROM Matches
                        GROUP BY winner ) AS Winning
                        ON Players.pid=Winning.pid
            LEFT JOIN ( SELECT loser AS pid, COUNT(*) AS times FROM Matches
                        GROUP BY loser ) AS Losing
                        ON Players.pid=Losing.pid;

Tournament Results
==================

In this project, we developed a database schema to store the game matches
between players, and then wrote a python module to rank the players and pair
them up in matches in a tournament.

1. Launch the vagrant virtual machine: go to the parent directory (where
   `Vagrantfile` resides) and run `vagrant up`. This will create the virtual
   machine and also a tournament in it database according to the schema defined
   in `tournament.sql`. One can also create the database and import schema
   manually with the following steps:

       dropdb --if-exists tournament
       createdb tournament
       psql tournament -f /vagrant/tournament/tournament.sql

2. Log in to the virtual machine with `vagrant ssh`, and then go to
   `/vagrant/tournament` directory.

3. Run the test with `python tournament_test.py`.


Author: Ying Xiong.  
Created: May 09, 2015.

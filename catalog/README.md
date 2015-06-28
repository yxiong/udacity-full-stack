Item Catalog
============

In this project we developed an application that provides a list of items within
a variety of categories as well as provide a user registration and
authentication system. Registered users will have the ability to post, edit and
delete their own items.


Launch in a vagrant virtual machine
-----------------------------------

1. Launch the vagrant virtual machine: go to the parent directory (where
   `Vagrantfile` resides) and run `vagrant up`.

2. Log into the virtual machine with `vagrant ssh`, and then go to
   `/vagrant/catalog/` directory.

3. Download the `client_secrets.json` from Google developer console, and put it
   in `catalog` subfolder.

4. [Remove `catalog/catalog.db` if already existed.]
   Setup the database `python setup_database.py`.

5. Launch the web server
   `[CATALOG_CONFIG_FILE=/path/to/config.py] python run_server.py`.


Deploy on a Linux server
------------------------

1. Setup the database `python setup_database.py`.

2. Create a `catalog.wsgi` script that contains the following line:

       ```
       from catalog import app as application
       ```

3. Create a `catalog.conf` configuration file for this WSGI job.

4. Restart apache server.

See the `linux/README.md` file in the parent folder for an example.


Author: Ying Xiong.  
Created: May 11, 2015.

Linux Server Configuration
==========================

In this project we take a baseline installation of a Linux distribution on a
virtual machine and prepare it to host our web applications, to include
installing updates, securing it from a number of attack vectors and
installing/configuring web and database servers.

1. Launch your Virtual Machine with your Udacity account

   The public IP address of the Virtual machine is `55.25.57.93`.


2. Follow the instructions provided to SSH into your server

   Add the following to `~/.ssh/config`

       ```
       Host udacity
       HostName 55.25.57.93
       IdentityFile ~/.ssh/udacity_key.rsa
       ```

   and then we can log in with `ssh root@udacity`.

3. Create a new user named grader


4. Give the grader the permission to sudo


5. Update all currently installed packages


6. Change the SSH port from 22 to 2200


7. Configure the Universal Firewall to only allow incoming connections for SSH
   (port 2200), HTTP (port 80), and NTP (port 123)


8. Configure the local timezone to UTC


9. Install and configure Apache to serve a Python mod_wsgi application


10. Install and configure PostgreSQL:
    * Do not allow remote connections
    * Create a new user named catalog that has limited permissions to your
      catalog application database


11. Install git, clone and setup your Catalog App project (from your GitHub
    repository from earlier in the Nanodegree program) so that it functions
    correctly when visiting your server’s IP address in a browser. Remember to
    set this up appropriately so that your .git directory is not publicly
    accessible via a browser!



Author: Ying Xiong.  
Created: May 21, 2015

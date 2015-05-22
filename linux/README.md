Linux Server Configuration
==========================

In this project we take a baseline installation of a Linux distribution on a
virtual machine and prepare it to host our web applications, to include
installing updates, securing it from a number of attack vectors and
installing/configuring web and database servers.

1. Launch your Virtual Machine with your Udacity account

   The public IP address of the Virtual machine is `52.11.182.246`.


2. Follow the instructions provided to SSH into your server

   Add the following to `~/.ssh/config`

       ```
       Host udacity
       HostName 52.11.182.246
       IdentityFile ~/.ssh/udacity_key.rsa
       ```

   and then log in with `ssh root@udacity`.

3. Create a new user named grader

   `adduser grader` with a given password.

4. Give the grader the permission to sudo

   Run `visudo` and add the following line

       ```
       grader ALL=(ALL) ALL
       ```

   In addition, we did the followings

   * Allow user to login through ssh as `grader` with the same private key that
     can be used to login as `root`:

         ```
         su grader
         mkdir ~/.ssh
         chmod 700 ~/.ssh
         sudo cp /root/.ssh/authorized_keys ~/.ssh/
         sudo chown grader:grader ~/.ssh/authorized_keys
         ```
     From now on, user can login through ssh by `ssh grader@udacity`, assuming
     the `~/.ssh/config` file has been properly set. After logging in, the user
     can switch to `root` by `sudo su`.

   * Disable ssh directly to `root`: edit `/etc/ssh/sshd_config` to change the
     line `PermitRootLogin without-password` to `PermitRootLogin no`, and then
     run `sudo service ssh restart`.

5. Update all currently installed packages

   `sudo apt-get -qqy update`

6. Change the SSH port from 22 to 2200

   Edit `/etc/ssh/sshd_config` to change the line `Port 22` to `Port 2200`, and
   then run `sudo service ssh restart`.

   Also add `Port 2200` to `~/.ssh/config` file in local machine (not on the
   server).


7. Configure the Universal Firewall to only allow incoming connections for SSH
   (port 2200), HTTP (port 80), and NTP (port 123)

       ```
       sudo su
       iptables -A INPUT -i eth0 -p tcp --dport 2200 -m state --state NEW,ESTABLISHED -j ACCEPT
       iptables -A OUTPUT -o eth0 -p tcp --sport 2200 -m state --state ESTABLISHED -j ACCEPT
       iptables -A INPUT -i eth0 -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT
       iptables -A OUTPUT -o eth0 -p tcp --sport 80 -m state --state ESTABLISHED -j ACCEPT
       iptables -A INPUT -i eth0 -p tcp --dport 123 -m state --state NEW,ESTABLISHED -j ACCEPT
       iptables -A OUTPUT -o eth0 -p tcp --sport 123 -m state --state ESTABLISHED -j ACCEPT
       iptables -P INPUT DROP
       iptables -P OUTPUT DROP
       iptables -P FORWARD DROP
       iptables-save
       ```

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

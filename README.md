Getting Python / GTK+ set up
---------------------------------------------------------------
step 1: install gtk itself
---------------------------------------------------------------

SUSE:
$ zypper install gtk+-3

Debian:
sudo apt-get install gtk+-3

---------------------------------------------------------------
Step 2: install Glade, the gui editor for gtk+
---------------------------------------------------------------

SUSE: 
$ zypper install glade

Debian 
$ sudo apt-get install glade

https://python-gtk-3-tutorial.readthedocs.io/en/latest/install.html#dependencies

make sure you have the current dependencies installed


---------------------------------------------------------------
Step 3: Install gobject-introspection
---------------------------------------------------------------

SUSE
$ Zypper install gobject-introspection

Debian
$ sudo apt-get install gobject-introspection

---------------------------------------------------------------
step 4: Run starter.py
---------------------------------------------------------------

$ python3 starter.py

This should spawn a small, blank window.  From here, you can create your own interface using glade, and create the 'controller' for your windowed program in python!
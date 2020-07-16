import os
#GTK+ imports
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from os.path import abspath, dirname, join

WHERE_AM_I = abspath(dirname(__file__))
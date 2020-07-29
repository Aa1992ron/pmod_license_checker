import os
#GTK+ imports
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from os.path import abspath, dirname, join
import subprocess
import time
from subprocess import PIPE

WHERE_AM_I = abspath(dirname(__file__))
PERLMOD_DUMPFILE = "pmlist_temp.out"
REPORT_DEFAULT_NAME = "pmod_report.csv"
#we need this vaiable so that we can delete an incomplete
# report file in the event that the program terminates 
report_csv_created = False


def exit_gracefully(sig, frame, report=False):
    os.remove(PERLMOD_DUMPFILE)
    if report:
    	os.remove(REPORT_DEFAULT_NAME)
    exit(0)


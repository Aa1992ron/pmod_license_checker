# Perl Module License Checker -- a utility for examining the current perl 
# library, with the purpose of finding any perl modules which are not explicitly 
# licensed as 'free software.'  Such modules will be specified as such in the report
# generated with this program. 

# global_definitions.py

#     Copyright (C) 2020  Aaron Patrick Spencer
#     spaaron@umich.edu 

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
#GTK+ imports
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Gdk, Gio
from os.path import abspath, dirname, join
import subprocess
import time
import chardet
import queue
import math
import resource
import sys
from subprocess import PIPE

WHERE_AM_I = abspath(dirname(__file__))
PERLMOD_DUMPFILE = "pmlist_temp.out"
REPORT_DEFAULT_NAME = "pmod_report.csv"
#we need this vaiable so that we can delete an incomplete
# report file in the event that the program terminates 
global report_csv_created
report_csv_created = False


def exit_gracefully(sig, frame):
    global report_csv_created
    os.remove(PERLMOD_DUMPFILE)

    if report_csv_created:
    	os.remove(REPORT_DEFAULT_NAME)
    exit(0)

def set_report_csv(exists):
    global report_csv_created
    report_csv_created = exists
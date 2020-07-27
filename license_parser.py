#!/usr/bin/python3
import signal
import sys
import argparse

#to make certain imports usable by the license checker file (this file)
# and the gtk callback functions (gtk_helpers), use:
# global_definitions.py
from global_definitions import *
#custom gtk helper functions import:
from gtk_helpers import *

def main():
    #Help text for command line args
    MODESELECT_HELPTEXT = "Run this program in command-line mode. "
    MODESELECT_HELPTEXT += "Program runs in windowed mode by default."

    parser = argparse.ArgumentParser(prog="python3 license_parser.py", 
                                    usage="%(prog)s [options]")
    parser.add_argument('--cli', dest="cli_mode", action="store_true", 
                        required=False, help=MODESELECT_HELPTEXT)
    parser.set_defaults(cli_mode=False)
    #get command line args, if there are any passed
    args = parser.parse_args()
    cli_mode = args.cli_mode


    #Not sure if we'll ever need to handle a SIGABRT, but uncommenting
    # the line below will make you SUPER SAFE (tm)
    #signal.signal(signal.SIGABRT, exit_gracefully)

    # Connect our handler for hangup, interrupt and terminate signals ,
    # since we have a temporary file we don't want to leave behind
    signal.signal(signal.SIGSEGV, exit_gracefully)
    signal.signal(signal.SIGHUP, exit_gracefully)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    #attempt to get a list of every perl module installed:
    create_modulelist_tempfile()

    if cli_mode:
        #CLI MODE BELOW -------------------------------------------------------
        print("--- running in terminal mode ---")
        with open(PERLMOD_DUMPFILE) as mod_listfile:
            mod_listfile.readline()
            for line in mod_listfile:
                #parse the name of this perl module from the line
                pmod_name = parse_pmod_name(line)
                #run our manual check and get a result to print out
                #for this module
                #this will be in csv format -- Module::Name,[free/proprietary?]
                parse_result = pmodfile_manual_parse(pmod_name)
                if parse_result is None:
                    #in this case, an erroneous line of output was passed
                    # to perldoc -lm. 
                    pass
                else:
                    print(parse_result)
        #Now that we're done going through all those modules, delete the temp file
        os.remove(PERLMOD_DUMPFILE)
        #----------------------------------------------------------------------
    else:
        print("--- running in gui mode ---")
        #GUI MODE BELOW -------------------------------------------------------
        #win = Gtk.Window()
        #win.connect("destroy", Gtk.main_quit)
        #win.show_all()
        #Usually, you'll want to use Glade to build the interfaces 
        # Glade generates an xml file that we can load like so
        style_init()
        builder = Gtk.Builder()
        builder.add_from_file("lchecker.glade")
        window = builder.get_object("first_screen")

        #connect our callback functions to the names specified in Glade
        # (names must be an exact match). These functions are defined in
        # gtk_helpers.py
        builder.connect_signals({"destroy": quit_btn_cb,
                                 "quit_btn_cb": quit_btn_cb,
                                 "next_btn_cb": (next_btn_cb, builder), 
                                 "back_btn_cb": (back_btn_cb, builder), 
                                 "start_cb":    (start_cb, builder)})

        window.show_all()
        #alternatively, you can traverse a list of objects --
        #glade_object_list = builder.get_objects()
        Gtk.main()
        #process the modules in windowed mode here
        os.remove(PERLMOD_DUMPFILE)
        #----------------------------------------------------------------------
    
    return 0
    

if __name__ == "__main__":
	main()


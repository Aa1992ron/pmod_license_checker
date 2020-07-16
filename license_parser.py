#!/usr/bin/python3
import signal
import sys
import argparse
#to cut down on repeated imports, common imports and global
#variables are in a seperate file -- global_definitions.py
from global_definitions import *
#custom gtk helper functions import:
from gtk_helpers import style_init

#from file_read_backwards import FileReadBackwards 


def main():
    #Help text for command line args
    MODESELECT_HELPTEXT = "Run this program in command-line mode. "
    MODESELECT_HELPTEXT += "Program runs in windowed mode by default."

    parser = argparse.ArgumentParser(prog="python3 license_parser.py", 
                                    usage="%(prog)s [options]")
    parser.add_argument('--cli',dest="cli_mode", action="store_true",
                         required=False, help=MODESELECT_HELPTEXT)
    parser.set_defaults(cli_mode=False)
    #get command line args, if there are any passed
    args = parser.parse_args()
    cli_mode = args.cli_mode

    # Connect our handler for interrupt and terminate signals ,
    # since we have a temporary file we don't want to leave behind
    signal.signal(signal.SIGSEGV, exit_gracefully)
    signal.signal(signal.SIGHUP, exit_gracefully)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    #attempt to get a list of every perl module installed:
    os_status = os.system("cpan -l > "+PERLMOD_DUMPFILE)
    #check to make sure the command worked
    if os_status == 1:
        print("Failed to get a list of perl modules installed: cpan -l cmd failed\n")
        exit(1)

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
        window.connect("destroy", Gtk.main_quit)
        window.show_all()

        #alternatively, you can traverse a list of objects --
        #glade_object_list = builder.get_objects()
        Gtk.main()
        #process the modules in windowed mode here
        os.remove(PERLMOD_DUMPFILE)
        #----------------------------------------------------------------------
    
    return 0


#EFFECTS: Runs a simple manual parse to determine license data. 
#           for right now, it only checks the first 25 lines of the 
#           given perl module file to determine this license data. 
#           More functionality to be added soon
#NOTES: additional checks we could do
#       check the perldoc(?) for license info
#       if this cannot be done, we may have to resort to  reverse read
def pmodfile_manual_parse(pmod_name):
    NUM_LINES2SCAN = 25
    printout_retval = ""

    ostream = os.popen("perldoc -lm "+pmod_name+" 2>&1")
    #get the fully qualified filename from the above command
    module_filename = ostream.read()

    #If the perldoc command was successful, the first character
    # of the output will be the root path character 
    if module_filename[0] == "N":
        return None
    #strip the newline character from the output of the command
    module_filename = module_filename.rstrip("\n")
    printout_retval = pmod_name+", "
    #the .pm file can be ascii/utf-8/etc, so we want to detect 
    #the charset before opening the file
    this_charset = which_charset(module_filename)
    #scan the file for license info
    perl_modfile = open(module_filename, 'r' ,encoding=this_charset)
    is_openlicense = False
    #for now, we'll just scan the first 25 lines of the file
    for i in range(NUM_LINES2SCAN):
        if perl_modfile.read(1) != "#":
            pass
        if line_check(perl_modfile.read()):
            #as in freedom
            printout_retval += "free"
            return printout_retval
    #if the loop didn't find the keywords which signal a free license,
    # warn users that it may be a proprietary license
    if not is_openlicense:
        printout_retval += "proprietary?"
        return printout_retval

#EFFECTS: parse out the name of a perl module from a single line of output
#           from the command cpan -l
def parse_pmod_name(raw_line):
    #we don't care about the version of the module,
    # so we'll strip it out for now
    module = raw_line.split("\t")
    #Grab the name of this perl module and return it
    return str(module[0])


#REQUIRES:  perl_module is a file denoted with an absolute path.
#           If you didn't also guess by the name, it should also be 
#           perl module file, or a '.pm' file
def which_charset(perl_module):
    #the following command will guess the charset of this particular file
    ostream = os.popen("file -i "+perl_module)
    info_output = ostream.read()
    charset = info_output.split("=");
    return charset[1]


def line_check(line):
    if "free software;" in line:
        return True
    else:
        return False

def exit_gracefully(sig, frame):
    os.remove(PERLMOD_DUMPFILE)
    exit(0)

if __name__ == "__main__":
	main()


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

    output = system_call(["perldoc", "-lm", pmod_name], PIPE, 
                            subprocess.STDOUT, False)
    (out, err) = output.communicate()
    if err is not None:
        print("ERROR -- problem with initial perldoc -lm system call. Output:")
        print(err)
        os.remove(PERLDOC_DUMPFILE)
        exit_gracefully(None, None)

    #get the fully qualified filename from the above command
    module_filename = out

    #If the perldoc command was successful, the first character
    # of the output will be the root path character 
    if module_filename[0] == "N":
        return None
    #strip the newline character from the output of the command
    module_filename = module_filename.rstrip("\n")

    #store the module name for end user output in a variable for now
    printout_retval = pmod_name+", "
    # Do the perldoc "quick" check first
    if quick_check(module_filename, pmod_name):
        printout_retval += "free"
        return printout_retval
    #else we must manually parse the file header for comments 
    # which contain license info
    
    #the .pm file can be ascii/utf-8/etc, so we want to detect 
    #the charset before opening the file
    this_charset = which_charset(module_filename)
    #scan the file for license info
    perl_modfile = open(module_filename, 'r' ,encoding=this_charset)
    
    is_openlicense = False
    #for now, we'll just scan the first 25 lines of the file
    for i in range(NUM_LINES2SCAN):
        if line_check(perl_modfile.readline()):
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
def which_charset(perl_modfile):
    #FIXME modify which_charset to use subprocess module
    #the following command will guess the charset of this particular file
    output = system_call(["file", "-i", perl_modfile], PIPE, 
                            subprocess.STDOUT, False)
    (out, err) = output.communicate()
    if err is not None:
        print("ERROR -- problem with file -i system call. Output:")
        print(err)
        os.remove(PERLDOC_DUMPFILE)
        exit_gracefully(None, None)

    charset = out.split("=")

    return charset[1]


def line_check(line):
    #print(line)
    if "free software;" in line:
        return True
    else:
        return False

#NOTE fq filename is short for fully qualified filename
#RETURNS: False if the test was INCONCLUSIVE
#         True if the test verified that the pm file is free software.  
def quick_check(module_fq_filename, module_name):
    
    NUM_LINES2SCAN = 10
    PERLDOC_DUMPFILE = "perldoc_tmp.out"
    #We are using the method of dumping the output to a file here
    # in order to avoid using an additional python dependency.
    perldoc_fileobj = open(PERLDOC_DUMPFILE, "w")
    output = system_call(["perldoc", module_fq_filename], 
                                perldoc_fileobj, perldoc_fileobj, 
                                False) 

    
    #get the fully qualified filename from the above command
    (out, err) = output.communicate()
    perldoc_fileobj.close()

    if err is not None:
        print("ERROR in perldoc system call:")
        print(err)
        os.remove(PERLDOC_DUMPFILE)
        exit_gracefully(None, None)

    #check the top of the file just in case we got a "No documentation"
    # message from perldoc
    if no_documentation(PERLDOC_DUMPFILE):
        #use the name for the module rather than the fully qualified
        # filename
        perldoc_fileobj = open(PERLDOC_DUMPFILE, "w")
        output = system_call(["perldoc", module_name], 
                                perldoc_fileobj, subprocess.STDOUT, 
                                False)

        (out, err) = output.communicate()

        #close the temporary file
        perldoc_fileobj.close()

    output = system_call(["grep", "-n", "free software", PERLDOC_DUMPFILE], 
                            PIPE, subprocess.STDOUT, 
                            False) 
    (out, err) = output.communicate()
    if err is not None:
        print("ERROR: grep -n not working in quick_check. Error output:")
        print(err)
        os.remove(PERLDOC_DUMPFILE)
        exit_gracefully(None, None)

    if out == "":
        #grep didn't find any copyright info
        os.remove(PERLDOC_DUMPFILE)
        return False
    else:
        return True
    

def create_modulelist_tempfile():
    temp_fileobj = open(PERLMOD_DUMPFILE, "w")

    out = system_call(["cpan", "-l"], temp_fileobj, subprocess.STDERR, False)

    (stdout, stderr) = out.communicate()
    if stderr is not None:
        print("Error creating list of perl modules with cpan -l")
        print("Error output:\n"+str(stderr))
        temp_fileobj.close()
        exit_gracefully(None, None)

    temp_fileobj.close()

def no_documentation(DUMPFILE):
    #The number below is chosen because we only need to 
    # check the first line of the perldoc -lm output because 
    # if no documentation exists for the module file, then
    # only one line of output will be printed.  3 is chosen to be thorough
    LINES_TO_CHECK = 3
    perldoc_fileobj = open(DUMPFILE, "r")

    for i in range(0,LINES_TO_CHECK):
        try:
            line_2check = perldoc_fileobj.readline()
        except:
            perldoc_fileobj.close()
            charset = which_charset(os.path.join(WHERE_AM_I,DUMPFILE))
            perldoc_fileobj = open(DUMPFILE, 'r' ,encoding=charset)
            line_2check = perldoc_fileobj.readline()
        if "No documentation" in line_2check:
            return True

    perldoc_fileobj.close()
    return False

def system_call(cmd_array, standard_out, standard_err, gui_mode):
    if gui_mode:
        pass
    else:
        return subprocess.Popen(cmd_array, stdout=standard_out, 
                                stderr=standard_err, universal_newlines=True)
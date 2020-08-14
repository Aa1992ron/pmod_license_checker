#!/usr/bin/python3
import signal
import sys
import argparse
import chardet

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
            for line in mod_listfile:
                if "Loading internal logger" in line:
                    #skip the reccommendation for Log::Log4perl
                    continue
                free_software = False
                #parse the name of this perl module from the line
                pmod_name = parse_pmod_name(line)
                pmod_fqfilename = get_pmod_fqfn_cli(pmod_name)
                # --- Check the perldocs for this module --- #
                perldocs = get_perldocs_cli(pmod_name)

                documentation =  not no_documentation(perldocs)
                if documentation:
                    free_software = parse_perldocs(perldocs)
                else:
                    #Running perldoc on the module name failed.
                    #Get the FQFN and run perldoc on that
                    perldocs = get_perldocs_cli(pmod_fqfilename)
                    documentation =  not no_documentation(perldocs)
                    if documentation:
                        free_software = parse_perldocs(perldocs)
                    else:
                        #NOTE: for now we can continue, but once we add
                        # checks beyond perldoc parsing and manual file
                        # parsing, we'll want to set a bool here instead.
                        # The reason for this is if the code reaches here,
                        # then perldoc -lm failed to return a fully qualified
                        # filename for the module name.  This means than we 
                        # CANNOT pass the variable 'pmod_fqfilename' to
                        # the manual parse function.  
                        continue
                        
                if free_software:
                    #this perl module is licensed as free software
                    print(pmod_name+", free")
                    continue
                
                # --- Run a manual file parse here --- #
                pmodfile_charset = which_charset(pmod_fqfilename)
                free_software = pmodfile_parse(pmod_fqfilename, 
                                                pmodfile_charset)

                if free_software:
                    #this perl module is licensed as free software
                    print(pmod_name+", free")
                    continue

                print(pmod_name+", proprietary?")
                #run a different check here
                
                
        #Now that we're done going through all those modules, delete the temp file
        os.remove(PERLMOD_DUMPFILE)
        #----------------------------------------------------------------------
    else:
        print("--- running in gui mode ---")
        global gui_syscalls
        gui_syscalls = True
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

        async_data = Async_data(builder)

        #connect our callback functions to the names specified in Glade
        # (names must be an exact match). These functions are defined in
        # gtk_helpers.py
        builder.connect_signals({"destroy": Gtk.main_quit,
                                 "quit_btn_cb": quit_btn_cb,
                                 "next_btn_cb": (next_btn_cb, builder), 
                                 "back_btn_cb": (back_btn_cb, builder), 
                                 "start_cb":    (start_cb, builder, async_data)})

        window.show_all()
        #alternatively, you can traverse a list of objects --
        #glade_object_list = builder.get_objects()
        Gtk.main()

        os.remove(PERLMOD_DUMPFILE)
        #----------------------------------------------------------------------
    
    return 0
    

#EFFECTS: Runs a simple manual parse to determine license data. 
#           for right now, it only checks the first 25 lines of the 
#           given perl module file to determine this license data. 
#           if the line is not a comment, it will skip without checking
#RETURNS: True if free software, False if inconclusive
def pmodfile_parse(pmod_fqfn, charset):
    NUM_LINES2SCAN = 25

    #scan the file for license info
    perl_modfile = open(pmod_fqfn, 'r' ,encoding=charset)
    
    #for now, we'll just scan the first 25 lines of the file
    # skip all lines which are not comments. License data is not 
    # part of the perl module code (lol)
    for i in range(NUM_LINES2SCAN):
        this_line = perl_modfile.readline()
        if this_line == "":
            return False
        if this_line[0] != '#':
            continue
        if line_check(this_line):
            #as in freedom
            return True


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
    syscall_flags =  Gio.SubprocessFlags.STDOUT_PIPE
    syscall_flags |= Gio.SubprocessFlags.STDERR_MERGE
    output = Gio.Subprocess.new(["file", "-i", perl_modfile,None], syscall_flags)
    (success, out, err) = output.communicate_utf8()
    failure = not success

    if failure:
        print("ERROR calling file -i in which_charset")
        print(out)
        exit_gracefully(None, None)

    if out == "" or out == None:
        print("ERROR: command \' file -i "+perl_modfile+"\' gave no output..")
        print(out)
        exit_gracefully(None, None)

    #output is okay to split
    charset = out.split("=")

    try:
        retval = charset[1]
    except IndexError:
        print("caught an index error:")
        print("filename: "+perl_modfile)
        print("file -i output: "+out)
        exit_gracefully(None, None)

    return retval


def line_check(line):
    #print(line)
    if "free software;" in line:
        return True
    else:
        return False


#RETURNS: False if the test was INCONCLUSIVE
#         True if the test verified that the pm file is free software.  
def parse_perldocs(perldocs):
    perldoc_lines = perldocs.split("\n")
    #license info tends to be near the bottom of the perl docs,
    # so reverse the lines array
    perldoc_lines.reverse()

    for line in perldoc_lines:
        if line_check(line):
            return True
    return False


def create_modulelist_tempfile():
    temp_fileobj = open(PERLMOD_DUMPFILE, "w")

    out = subprocess.Popen(["cpan", "-l"], stdout=temp_fileobj, 
                            universal_newlines=True)

    (stdout, stderr) = out.communicate()
    if stderr is not None:
        print("Error creating list of perl modules with cpan -l")
        print("Error output:\n"+str(stderr))
        temp_fileobj.close()
        exit_gracefully(None, None)

    temp_fileobj.close()

#EFFECTS: runs syncronous perldoc command and returns the output
def get_perldocs_cli(module):
    #redirect errors to STDOUT
    syscall_flags =  Gio.SubprocessFlags.STDOUT_PIPE
    syscall_flags |= Gio.SubprocessFlags.STDERR_MERGE
    sp = Gio.Subprocess.new(["perldoc", module, None], 
                                syscall_flags)

    decode_bytes = False

    try:
        (success, out, err) = sp.communicate_utf8()
    except gi.repository.GLib.Error:
        #run the command again but get raw bytes instead of trying
        # to decode to utf-8
        sp = Gio.Subprocess.new(["perldoc", module, None], 
                                syscall_flags)
        (success, out, err) = sp.communicate()
        decode_bytes = True

    failure = not success

    if failure:
        print("ERROR in perldoc system call:")
        print(out)
        exit_gracefully(None, None)

    if out == "" or out == None:
        print("ERROR: command\' perldoc "+pmod_name+"\' gave no output..")
        print(out)
        exit_gracefully(None, None)

    if decode_bytes:
        #deal with the case where the perldocs are encoded using a charset
        # other than utf-8
        my_bytes = out.get_data()
        encoding = chardet.detect(my_bytes)['encoding']
        out = my_bytes.decode(encoding)

    #output is okay to send back to caller
    return out

# no_documentation rears its ugly head once again >:)
#EFFECTS: performs a smart check on the first line of output.  
#          We don't want to run a simple python check, because
#          if our perldoc command returned full documentation 
#          for a given module, python will search the whole thing 
#          for the string "No documentation." 
#          
#          So instead this function will grab the first line 
#          and check it for "No documentation" or "No module found"
def no_documentation(perldoc_output):
    search_limit = len(perldoc_output)
    i = 0
    first_line = ""

    while i < search_limit:
        #build the first line
        if perldoc_output[i] == '\n':
            break
        first_line += perldoc_output[i]
        i += 1

    if "No documentation" in first_line:
        return True
    elif "No module" in first_line:
        return True
    else:
        return False

def get_pmod_fqfn_cli(pmod_name):
    syscall_flags =  Gio.SubprocessFlags.STDOUT_PIPE
    syscall_flags |= Gio.SubprocessFlags.STDERR_MERGE
    #syscall_flags |= Gio.SubprocessFlags.STDERR_PIPE
    sp = Gio.Subprocess.new(["perldoc", "-lm", pmod_name, None], 
                                syscall_flags)
    #FIXME we'll want to change this into callback form that we can generalize
    # accross both gui and cli modes if we can

    (success, out, err) = sp.communicate_utf8()

    if success is not True:
        print("ERROR -- problem with perldoc -lm command. Output:")
        print(err)
        exit_gracefully(None, None)
 
    #get the fully qualified filename from the above command
    module_filename = out

    #print("CHECKING: "+pmod_name)
    #If the perldoc command was successful, the first character
    # of the output will be the root path character 
    if module_filename == "" or module_filename == None:
        print("ERROR: perldoc -lm "+pmod_name+" gave no output..")
        exit_gracefully(None,None)

    return out.rstrip("\n")


if __name__ == "__main__":
    main()
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

    output = subprocess.Popen(["perldoc", "-lm", pmod_name], 
                            stdout=PIPE, stderr=subprocess.STDOUT, 
                            universal_newlines=True)
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
    output = subprocess.Popen(["file", "-i", perl_modfile], 
                            stdout=PIPE, stderr=subprocess.STDOUT, 
                            universal_newlines=True)
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
    output = subprocess.Popen(["perldoc", module_fq_filename], 
                                stdout=perldoc_fileobj, stderr=perldoc_fileobj, 
                                universal_newlines=True) 

    
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
        output = subprocess.Popen(["perldoc", module_name], 
                                stdout=perldoc_fileobj, stderr=subprocess.STDOUT, 
                                universal_newlines=True)

        (out, err) = output.communicate()

        #close the temporary file
        perldoc_fileobj.close()

    output = subprocess.Popen(["grep", "-n", "free software", PERLDOC_DUMPFILE], 
                            stdout=PIPE, stderr=subprocess.STDOUT, 
                            universal_newlines=True) 
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

    out = subprocess.Popen(["cpan", "-l"], 
                            stdout=temp_fileobj)

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
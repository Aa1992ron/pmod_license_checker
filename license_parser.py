#!/usr/bin/python3
import os
import argparse

#from file_read_backwards import FileReadBackwards 


def main():
    #Help text for command line args
    MODESELECT_HELPTEXT = "Run this program in command-line mode. "
    MODESELECT_HELPTEXT += "Program runs in windowed mode by default."

    parser = argparse.ArgumentParser(prog="license_parser.py", 
                                    usage="%(prog)s [options]")
    parser.add_argument('--cli',dest="cli_mode", action="store_true",
                         required=False, help=MODESELECT_HELPTEXT)

    parser.set_defaults(cli_mode=False)
    args = parser.parse_args()

    cli_mode = args.cli_mode

    if cli_mode:
        print("cli mode selected")
        exit(0)
    else:
        print("gui mode selected")
        #run gui mode
        exit(0)

    NUM_LINES2SCAN = 25
    PERLMOD_DUMPFILE = "pmlist_temp.out"

    #try to output the perl module list to a temp file
    os_status = os.system("cpan -l > "+PERLMOD_DUMPFILE)
    if os_status is 1:
        print("cpan -l command failed in get_modulelist")
        exit(1)

    with open(PERLMOD_DUMPFILE) as mod_listfile:
        mod_listfile.readline()
        for line in mod_listfile:
            #we don't care about the version of the module,
            # so we'll strip it out for now
            module = line.split("\t")
            #Grab the name of this perl module
            pmod_name = str(module[0])
            #print("****"+str(module[0]))
            ostream = os.popen("perldoc -lm "+pmod_name+" 2>&1")
            #get the location of this module's perl code
            module_filename = ostream.read()
            #If the perldoc command was successful, the first character
            # of the output will be the root path character 
            if module_filename[0] is "N":
                pass
            #strip the newline character from the output of the command
            module_filename = module_filename.rstrip("\n")
            print(pmod_name+", ")
            #the .pm file can be ascii/utf-8/etc, so we want to detect 
            #the charset before opening the file
            this_charset = which_charset(module_filename)

            #scan the file for license info
            perl_modfile = open(module_filename, 'r' ,encoding=this_charset)
            is_openlicense = False
            #for now, we'll just scan the first 25 lines of the file
            for i in range(NUM_LINES2SCAN):
                if perl_modfile.read(1) is not "#":
                    pass
                if line_check(perl_modfile.read()):
                    #as in freedom
                    print("free\n")
                    is_openlicense = True
                    break

            #check the perldoc(?) for license info

            #if this cannot be done, we may have to resort to  reverse read


            #if the loop didn't find the keywords which signal a free license,
            # warn users that it may be a proprietary license
            if not is_openlicense:
                print("proprietary?\n")



    os.remove(PERLMOD_DUMPFILE)
    #First, we'll try and narrow down license comments that differ from the following:
    #module_filename = module_filename.rstrip("\n")
    # This program is free software; you can redistribute it and/or
    # modify it under the same terms as Perl itself.
    #perl_modfile = open(module_filename, "r")

    #for i in range(NUM_LINES2SCAN):
        #if line_check(perl_modfile.readline()):
            #print("Licensed as free software")

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



if __name__ == "__main__":
	main()


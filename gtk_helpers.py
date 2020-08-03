from global_definitions import *
from license_parser import create_modulelist_tempfile, parse_pmod_name
#from license_parser import pmodfile_manual_parse
import asyncio

class Async_data:
	def __init__(self, gtkbuilder):
		self.num_modules = -1
		self.builder = gtkbuilder

	def generate_report(self):
		print(self.num_modules)
		Gtk.main_quit()

	#MODIFIES: self.num_modules
	#EFFECTS: kicks of the report generating process.
	def start_callback(self, subprocess, result):
		[success, out, err] = subprocess.communicate_utf8()
		if success:
			module_amt_data = out.split(" ")
			self.num_modules = int(module_amt_data[0])
			subprocess.wait_check_finish(result)
		else:
			print("error in async wc -l call")
			exit_gracefully(None,None)
		self.generate_report()


		


#EFFECTS: Necessary to link the style sheet with our gtk windows
def style_init():
    provider = Gtk.CssProvider()
    provider.load_from_path(join(WHERE_AM_I, 'style.css'))
    screen = Gdk.Screen.get_default()
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(screen, provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)
    return


def quit_btn_cb(quit_btn):
    Gtk.main_quit()

def next_btn_cb(next_btn, builder):
	win2hide = next_btn.get_toplevel()
	win2hide.hide()
	summary_screen = builder.get_object("summary_screen")
	summary_screen.show()

def back_btn_cb(back_btn, builder):
	win2hide = back_btn.get_toplevel()
	win2hide.hide()
	summary_screen = builder.get_object("first_screen")
	summary_screen.show()

def start_cb(start_btn, builder, async_data):
	win2hide = start_btn.get_toplevel()
	win2hide.hide()
	progress_screen = builder.get_object("progress_screen")
	progress_bar = builder.get_object("progress_bar")
	progress_bar.set_fraction(0.0)
	current_module = builder.get_object("processing_text")
	progress_screen.show()

	#need to count the number of modules we'll be processing for the progress bar
	num_modules = [-1]
	syscall_flags =  Gio.SubprocessFlags.STDOUT_PIPE
	syscall_flags |= Gio.SubprocessFlags.STDERR_MERGE
	module_cnt_syscall = Gio.Subprocess.new(["wc", "-l", PERLMOD_DUMPFILE,None],
    											syscall_flags)



	#count the number of modules we have to process
	module_cnt_syscall.wait_check_async(None, async_data.start_callback)

	

	# output_sheet = open(REPORT_DEFAULT_NAME, "w")
	# #set the global variable that tells exit gracefully to 
	# # remove this file in case of interrupt/early termination
	# set_report_csv(True)

	# current_module.set_markup("Counting lines in list file")

	# output = subprocess.Popen(["wc", "-l", PERLMOD_DUMPFILE], 
 #                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
 #                            universal_newlines=True)

	# (out, err) = output.communicate()

	# if err is not None:
	# 	print("ERROR -- problem with wc -l. Output:")
	# 	print(err)
	# 	exit_gracefully(None, None)

	# module_amt_data = out.split(" ")

	# num_modules = int(module_amt_data[0])

	# progress_screen.show()
	# current_module.set_markup("Loading module list file")

	# i = 1

	# with open(PERLMOD_DUMPFILE) as mod_listfile:
	# 	mod_listfile.readline()
	# 	for line in mod_listfile:

	# 		progress_bar.set_fraction(i/num_modules)
 #            #parse the name of this perl module from the line
	# 		pmod_name = parse_pmod_name(line)

	# 		current_module.set_markup("Parsing module: "+pmod_name)
 #            #run our manual check and get a result to print out
 #            #for this module
 #            #this will be in csv format -- Module::Name,[free/proprietary?]
	# 		#parse_result = pmodfile_manual_parse(pmod_name)
	# 		parse_result = pmodfile_manual_parse(pmod_name)
	# 		i += 1
	# 		print(str(i))
	# 		if parse_result is None:
	# 		    #in this case, an erroneous line of output was passed
	# 		    # to perldoc -lm. 
	# 		    pass
	# 		else:
	# 			output_sheet.write(pmod_name+","+parse_result+"\n")
	# report_csv_created = False
	# mod_listfile.close()
	# output_sheet.close()
 #    #Now that we're done going through all those modules, delete the temp file
	# exit(0)

#FIXME we need to change the system calls to return asynchronously
#https://stackoverflow.com/questions/35036122/unable-to-initialize-a-window-and-wait-for-a-process-to-end-in-python-3-gtk-3


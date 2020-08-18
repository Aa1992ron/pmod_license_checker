from global_definitions import *
from license_parser import create_modulelist_tempfile, parse_pmod_name
from license_parser import line_check, parse_perldocs, no_documentation
#from license_parser import pmodfile_manual_parse
import threading

PDOC_NAME_CHECK = False
PDOC_PATH_CHECK = True

#best advice I've found so far -- use
#gdk_threads_add_idle_full(ui_update_func, user_data)
#or
#gdk_threads_add_timeout()
# https://www.yhi.moe/en/2019/01/23/async-gui-update-in-gtk.html

#error we're getting right now is:
#     perldoc_syscall = Gio.Subprocess.new(["perldoc", pmod_name, None],
#	gi.repository.GLib.Error: g-unix-error-quark: Too many open files (0)
# it seems as though the perldoc command actually opens the file



class Async_data:
	def __init__(self, gtkbuilder):
		#gtk objects/variables
		self.builder = gtkbuilder
		self.progress_bar = None
		self.progress_text = None
		#data processing variables
		self.num_modules = -1
		self.module_list = []
		
		self.mod_report_data = []

		self.start_q = queue.Queue()
		self.end_q = queue.Queue()
		#self.chunk_size = -1
		self.reportgen_thread = None

		self.count_queue = queue.Queue()
		self.current_module = queue.LifoQueue()

	#REQUIRES: create_modulelist_tempfile has already been called.
	#		   
	def read_modulelist_file(self):
		with open(PERLMOD_DUMPFILE) as mod_listfile:
			for line in mod_listfile:
				pmod_name = parse_pmod_name(line)
				self.module_list.append(pmod_name)
			mod_listfile.close()
		print("Finished reading file")
		self.num_modules = len(self.module_list)
		print(self.num_modules)
		return

	# DESCRIPTION: The OS limits the number of open files,
	# and the number of processes allowed for any given user. 
	# Each thread we spawn has the potential to count against
	# each of these limits, since the 'perldoc' command opens
	# files to get the module documentation.  

	def set_max_openfile_limit(self):
		(soft_limit, hard_limit) = resource.getrlimit(resource.RLIMIT_OFILE)
		resource.setrlimit(resource.RLIMIT_OFILE,
									[hard_limit-1,hard_limit])

	def set_openfile_limit(self):
		#we don't want to hit the actual limit of files, 
		# and in case the user has open files we want to have
		# a bit of wiggle room
		wiggle_room = 20

		if self.num_modules == -1:
			print("must call read_modulelist_file before calling"+
				  "get_openfile_limit\n", file=sys.stderr)
			exit(1)
		file_limit = -1
		(soft_limit, hard_limit) = resource.getrlimit(resource.RLIMIT_OFILE)

		if self.num_modules >= soft_limit:
			if self.num_modules >= hard_limit:
				#for now, print to stderr and exit.  
				# Implementation for breaking up processing into
				# chunks to come. FIXME
				print("Number of perl modules exceeds hard limit"+
				  "for the number of files allowed to be open at once\n",
				  file=sys.stderr)
				exit(1)

			if self.num_modules+wiggle_room < hard_limit:
				new_soft_limit = self.num_modules+wiggle_room
				resource.setrlimit(resource.RLIMIT_OFILE,
									[new_soft_limit,hard_limit])
			else:
				resource.setrlimit(resource.RLIMIT_OFILE,
									[self.num_modules,hard_limit])
			#double check new soft limit
			(soft_limit, hard_limit) = resource.getrlimit(resource.RLIMIT_OFILE)
			print("new soft limit is:"+str(soft_limit))
			return


 
	def check_report_data(self):
		print("checking array size")
		if self.num_modules == len(self.mod_report_data):
			return False
		else:
			return True

	def generate_report(self):
		for pmod in self.module_list:
			self.perldoc_name_check(pmod)
		pmod_report = open("pmod_report.csv", "w")
		for result in self.mod_report_data:
			pmod_report.write(result+"\n")
		self.end_q.put(1)
		return False
	
	def start_checker(self):
		#print("checking")
		if not self.start_q.empty():
			print("calling report gen")
			self.start_q.get(block=False)
			# Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, 
   #                      self.end_checker)
			#calling the function like this will block the main loop
			self.reportgen_thread = threading.Thread(group=None,
									target=self.generate_report)
			self.reportgen_thread.start()
			return False
		else:
			#keep running the check
			return True

	#EFFECTS: end_checker updates the progress bar throughout the report
	#			generation process until the full report has been generated
	#NOTE:	  This function is meant to be run as a periodic check.  As Gdk is
	#		  currently implemented, we run this in a - Gdk.threads_add_timeout()
	#		  call
	def end_checker(self):
		if not self.end_q.empty():
			self.progress_bar.set_fraction(1)
			self.progress_text.set_markup("Finished")
			print("report successfully generated")
			return False
		else:
			if not self.count_queue.empty():
				#update processing text:
				if not self.current_module.empty():
					self.progress_text.set_markup(
						"Processing module: "+
						self.current_module.get(block=False))
				#update the progress bar fraction:
				self.progress_bar.set_fraction(self.count_queue.qsize()/self.num_modules)
			else:
				self.progress_text.set_markup("Processing module list file")
				self.progress_bar.set_fraction(0.0)

			#print("ary size: "+str()
			#keep running the check
			return True

	#MODIFIES: self.num_modules
	#EFFECTS: kicks of the report generating process.

	def perldoc_name_check(self, pmod_name):
		syscall_flags =  Gio.SubprocessFlags.STDOUT_PIPE
		syscall_flags |= Gio.SubprocessFlags.STDERR_MERGE
		perldoc_syscall = Gio.Subprocess.new(["perldoc", pmod_name, None],
    											syscall_flags)
		#count the number of modules we have to process
		perldoc_syscall.communicate_async(None, None, self.pdoc_name_cb, 
										pmod_name, PDOC_NAME_CHECK)

	#EFFECTS: gets the result of a subprocess call perldoc [module name]
	#			on the first try, and perldoc [module fpath] on the
	#			second (last) try.  If there are no docs then this
	#			function will make an additional async subprocess call
	#			to get the full path for the given perl module and pass it
	#			to the manual parse function which opens the actual file.  
	def pdoc_name_cb(self, subprocess, result, pmod_name, last_try):

		[success, out, err] = subprocess.communicate_finish(result)
		if success:
			temp_bytes = out.get_data()
			encoding = chardet.detect(temp_bytes)['encoding']
			pdoc_content = temp_bytes.decode(encoding)

			if pdoc_content == "" or pdoc_content == None:
				print("ERROR: command\' perldoc "+pmod_name+"\' gave no output..")
				print(out)
				exit_gracefully(None, None)

			if no_documentation(pdoc_content):
				if last_try:
					#FIXME try the manual parse here
					self.count_queue.put(1)
					self.current_module.put(pmod_name)
					self.mod_report_data.append(pmod_name+",proprietary?")
					return
				else:
					#FIXME call a perldoc_fqfn function
					self.count_queue.put(1)
					self.current_module.put(pmod_name)
					self.mod_report_data.append(pmod_name+",proprietary?")
					return
			else:
				#parse for license data
				free_software = parse_perldocs(pdoc_content)

				if free_software:
					self.count_queue.put(1)
					self.current_module.put(pmod_name)
					self.mod_report_data.append(pmod_name+",free")
					return
				else:
					#FIXME run the manual parse
					self.count_queue.put(1)
					self.current_module.put(pmod_name)
					self.mod_report_data.append(pmod_name+",proprietary?")
					return
			
		else:
			print("error in perldoc [name] call")
			print(out)
			exit_gracefully(None,None)
		


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
	async_data.progress_bar = builder.get_object("progress_bar")
	async_data.progress_bar.set_fraction(0.0)
	async_data.progress_text = builder.get_object("processing_text")
	async_data.progress_text.set_markup("Processing module list file")
	progress_screen.show()
	#putting any item into the start_q will start the main report
	# generation process
	async_data.start_q.put(1)
	Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, 
                        async_data.end_checker)
	return
	

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


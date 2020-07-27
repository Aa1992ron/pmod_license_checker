from global_definitions import *

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

def start_cb(start_btn, builder):
	win2hide = start_btn.get_toplevel()
	win2hide.hide()
	progress_screen = builder.get_object("progress_screen")
	progress_bar = builder.get_object("progress_bar")
	progress_bar.set_fraction(0.0)
	current_module = builder.get_object("processing_text")


	output_sheet = open(REPORT_DEFAULT_NAME, "w")

	#current_module.set_markup("Counting lines in list file")

	output = subprocess.Popen(["wc", "-l", PERLMOD_DUMPFILE], 
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                            universal_newlines=True)

	(out, err) = output.communicate()

	if err is not None:
		print("ERROR -- problem with wc -l. Output:")
		print(err)
		exit_gracefully(None, None, True)

	module_amt_data = out.split(" ")

	num_modules = int(module_amt_data[0])

	progress_screen.show()
	current_module.set_markup("Loading module list file")

	i = 1

	with open(PERLMOD_DUMPFILE) as mod_listfile:
		mod_listfile.readline()
		for line in mod_listfile:
			time.sleep(0.1)
			progress_bar.set_fraction(i/num_modules)
            #parse the name of this perl module from the line
			pmod_name = parse_pmod_name(line)

			current_module.set_markup("Parsing module: "+pmod_name)
            #run our manual check and get a result to print out
            #for this module
            #this will be in csv format -- Module::Name,[free/proprietary?]
			#parse_result = pmodfile_manual_parse(pmod_name)
			parse_result = None
			i += 1
			print(str(i))
			if parse_result is None:
			    #in this case, an erroneous line of output was passed
			    # to perldoc -lm. 
			    pass
			else:
				output_sheet.write(pmod_name+","+parse_result+"\n")
	mod_listfile.close()
	output_sheet.close()
    #Now that we're done going through all those modules, delete the temp file
	return

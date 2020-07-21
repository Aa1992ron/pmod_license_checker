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
	summary_screen = builder.get_object("progress_screen")
	summary_screen.show()
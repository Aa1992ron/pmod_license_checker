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


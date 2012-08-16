# Infrared Remote Control Properties for GNOME
# Copyright (C) 2008 Fluendo Embedded S.L. (www.fluendo.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
'''
Infrared Remote Control Properties for GNOME.
'''

def run(args, datadir):
    '''
    Executes the properties dialog.
    '''

    import logging

    # Support full tracing when --debug switch is passed:
    if '--debug' in args or '-d' in args:
        logging.getLogger().setLevel(logging.NOTSET)

    # Integrate DBus with GLib main loop
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    # Initialize user interface
    import pygtk

    pygtk.require('2.0')

    from gettext               import gettext as _
    from gnome_lirc_properties import ui

    import gobject, gtk, gtk.gdk, os.path

    # Setup defaut properties:
    gobject.threads_init()
    gobject.set_application_name(_('Infrared Remote Control Properties'))
    gtk.window_set_default_icon_name('gnome-lirc-properties')

    # Enable thread support:
    gtk.gdk.threads_init()

    # Load the user interface:
    ui_filename = os.path.join(datadir, 'gnome-lirc-properties.ui')
    builder = gtk.Builder()
    builder.add_from_file(ui_filename)
    return ui.RemoteControlProperties(builder, datadir).run()

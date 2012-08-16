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
Common UI routines.
'''

import gtk, gtk.gdk, logging

def show_message(parent, message, details=None,
                 message_type=gtk.MESSAGE_ERROR,
                 buttons=gtk.BUTTONS_OK):
    '''
    Shows a message dialog.
    '''

    stock_buttons = gtk.BUTTONS_NONE

    if isinstance(buttons, gtk.ButtonsType):
        stock_buttons = buttons
        buttons = tuple()

    dialog = gtk.MessageDialog(parent=parent, flags=gtk.DIALOG_MODAL,
                               buttons=stock_buttons, type=message_type,
                               message_format = message)

    # Apply secondary text when supplied:
    if details:
        dialog.format_secondary_markup(details)

    # Apply custom buttons when supplied:
    for i, response, text in [[i] + list(b[:2]) for i, b in enumerate(buttons)]:
        button = dialog.add_button(text, response)

        if 3 == len(buttons[i]):
            stock_id = buttons[i][2]
            image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)

    if buttons:
        dialog.set_default_response(buttons[-1][0])

    # Show and run the dialog:
    response = dialog.run()
    dialog.destroy()

    return response

def thread_callback(callback):
    '''
    Decorate a function with code to acquire and release the big GDK lock.
    '''

    def wrapper(*args, **kwargs):
        '''
        Wrapper around the function to acquire and release the big GDK lock.
        '''

        logging.info('waiting for big GDK lock: %s', callback.__name__)
        gtk.gdk.threads_enter()

        try:
            callback(*args, **kwargs)

        finally:
            logging.info('releasing big GDK lock: %s', callback.__name__)
            gtk.gdk.threads_leave()

    wrapper.callback = callback

    return wrapper


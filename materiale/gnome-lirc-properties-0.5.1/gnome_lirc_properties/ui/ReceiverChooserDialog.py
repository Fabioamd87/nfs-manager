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
A dialog for choosing among multiple detected IR receivers.
'''

import gobject, gtk, pango

class ReceiverChooserModel(gtk.ListStore):
    '''
    Tree-model for listing auto-detected IR receivers.
    '''

    COLUMN_MARKUP, COLUMN_RECEIVER, COLUMN_UDI, COLUMN_DEVICE = range(4)

    def __init__(self):
        super(ReceiverChooserModel, self).__init__(gobject.TYPE_STRING,
                                                   gobject.TYPE_PYOBJECT,
                                                   gobject.TYPE_STRING,
                                                   gobject.TYPE_STRING)

        self.set_sort_column_id(self.COLUMN_MARKUP, gtk.SORT_ASCENDING)

    def append_receiver(self, receiver, udi, device, product_name=None):
        '''
        Appends a receiver to this list-store.
        '''

        if product_name is None:
            args = receiver.vendor, receiver.product

        else:
            args = receiver.product, product_name

        args = tuple(map(gobject.markup_escape_text, args))
        markup = '%s <b>%s</b>' % args

        self.set(self.append(),
                 self.COLUMN_MARKUP,   markup,
                 self.COLUMN_RECEIVER, receiver,
                 self.COLUMN_UDI,      udi,
                 self.COLUMN_DEVICE,   device)

    def __len__(self):
        return self.iter_n_children(None)

class ReceiverChooserDialog(object):
    '''
    Dialog for choosing from auto-detected IR receivers.
    '''

    def __init__(self, builder):
        super(ReceiverChooserDialog, self).__init__()

        # initialize attributes
        self.__dialog        = builder.get_object('receiver_chooser_dialog')
        self.__button_accept = builder.get_object('receiver_chooser_accept')
        self.__receiver_view = builder.get_object('receiver_view')
        self.__receivers     = ReceiverChooserModel()

        # auto-connect signal handlers
        builder.connect_signals(self)

        # setup the tree view
        renderer = gtk.CellRendererText()
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn('', renderer, markup=0)

        self.__receiver_view.set_model(self.__receivers)
        self.__receiver_view.append_column(column)

        selection = self.__receiver_view.get_selection()
        selection.connect('changed', self._on_selection_changed)
        selection.set_mode(gtk.SELECTION_BROWSE)

    def reset(self):
        '''
        Restores the initial state of this dialog's widgets.
        '''

        self.__button_accept.set_sensitive(False)
        self.__receivers.clear()

    def show(self):
        '''
        Shows this dialog.
        '''

        self.__dialog.show()

    def append(self, receiver, udi, device, product_name=None):
        '''
        Appends another receiver to this chooser,
        and returns the current number of receivers shown.
        '''

        self.__receivers.append_receiver(receiver, udi, device, product_name)
        self.__receiver_view.set_cursor((0, ), None, True)

        return len(self.__receivers)

    # pylint: disable-msg=R0201,W0613
    def _on_receiver_view_row_activated(self, view, path, column):
        '''
        Handles activation of tree-view rows by closing the dialog
        with gtk.RESPONSE_ACCEPT.
        '''

        view.get_toplevel().response(gtk.RESPONSE_ACCEPT)

    def _on_selection_changed(self, selection):
        '''
        Activates the "Accept" button, when a receiver is selected.
        '''

        rows = selection.count_selected_rows()
        self.__button_accept.set_sensitive(rows > 0)

    def _on_delete_event(self, dialog, event):
        '''
        Prevent dialog destruction on ESC.
        '''

        dialog.hide()
        return True

    def __get_selected_receiver(self):
        '''
        Retrieves the currently selected receiver and its device node.
        '''

        selection = self.__receiver_view.get_selection()
        tree_model, tree_iter = selection.get_selected()

        return tree_model.get(tree_iter,
                              tree_model.COLUMN_RECEIVER,
                              tree_model.COLUMN_DEVICE)

    def __get_n_receivers(self):
        '''
        Retreives the current number of receivers.
        '''

        return len(self.__receivers)

    selected_receiver = property(__get_selected_receiver)
    n_receivers = property(__get_n_receivers)


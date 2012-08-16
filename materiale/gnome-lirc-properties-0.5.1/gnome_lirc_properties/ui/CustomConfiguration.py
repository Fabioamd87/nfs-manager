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
The dialog for customizing remote control settings.
'''

import dbus, logging, gobject, gtk

from gettext                         import gettext as _
from gnome_lirc_properties           import backend, config, lirc, model
from gnome_lirc_properties.ui.common import show_message, thread_callback
from StringIO                        import StringIO
from time                            import time

class CustomConfiguration(object):
    '''This window allows the user to detect each key individually.'''

    default_keys = model.DictionaryStore(
        values=dict([(c.key, c.display_name) for c in
                     lirc.KeyCodes.get_default_commands()]),
        value_type=gobject.TYPE_STRING)

    def __init__(self, builder):
        self.__remote = None

        # irrecord drivers:
        self.__detection_driver = None
        self.__learning_driver = None

        # Remember row of column that currently learned:
        self.__learning_timeout = 0
        self.__learning_row = None

        # setup widgets
        self.__setup_ui(builder)

    # pylint: disable-msg=W0201
    def __setup_ui(self, builder):
        '''Initialize widgets.'''

        self.__ui = builder
        self.__ui.connect_signals(self)

        # lookup major widgets:
        self.__dialog   = self.__ui.get_object('custom_configuration')
        self.__notebook = self.__ui.get_object('notebook')

        # lookup buttons:
        self.__button_ok            = self.__ui.get_object('button_ok')
        self.__button_detect_basics = self.__ui.get_object('button_detect_basics')
        self.__button_keys_learn    = self.__ui.get_object('button_keys_learn')
        self.__button_keys_remove   = self.__ui.get_object('button_keys_remove')
        self.__button_keys_clear    = self.__ui.get_object('button_keys_clear')
        self.__button_keys_add      = self.__ui.get_object('button_keys_add')

        # setup model page:
        self.__entry_vendor      = self.__ui.get_object('entry_vendor')
        self.__entry_product     = self.__ui.get_object('entry_product')
        self.__entry_contributor = self.__ui.get_object('entry_contributor')
        self.__usage_hint        = self.__ui.get_object('usage_hint')

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        size_group.add_widget(self.__entry_vendor)
        size_group.add_widget(self.__usage_hint)

        # setup remaining notebook pages:
        self.__setup_basics()
        self.__setup_keys()

        # apply stock icon to learn button
        image = gtk.image_new_from_stock(gtk.STOCK_MEDIA_RECORD,
                                         gtk.ICON_SIZE_BUTTON)
        self.__button_keys_learn.set_image(image)

    # pylint: disable-msg=W0201
    def __setup_basics(self):
        '''Initialize widgets of the "Basics" page.'''

        self.__page_basics               = self.__ui.get_object('page_basics')
        self.__treeview_basics           = self.__ui.get_object('treeview_basics')
        self.__progressbar_detect_basics = self.__ui.get_object('progressbar_detect_basics')

        treeview_columns = (
            gtk.TreeViewColumn(_('Property'), gtk.CellRendererText(), text=0),
            gtk.TreeViewColumn(_('Value'), gtk.CellRendererText(), text=1),
        )

        for column in treeview_columns:
            self.__treeview_basics.append_column(column)

        selection = self.__treeview_basics.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)

    # pylint: disable-msg=W0201
    def __setup_keys(self):
        '''Initialize widgets of the "Keys" page.'''

        self.__page_keys       = self.__ui.get_object('page_keys')
        self.__treeview_keys   = self.__ui.get_object('treeview_keys')
        self.__hbuttonbox_keys = self.__ui.get_object('hbuttonbox_keys')
        self.__label_keys_hint = self.__ui.get_object('label_keys_hint')
        self.__image_keys_hint = self.__ui.get_object('image_keys_hint')

        self.__keys_learning_hint = _(
            '<b>Learning new key code.</b>\n'
            'Press the button on your remote control which should emit this key-code.')
        self.__keys_default_hint = self.__label_keys_hint.get_label()

        # pylint: disable-msg=W0613
        def editing_started(cell, editable, path):
            '''
            Replace the human-friendly key name by the internal key-name,
            before editing a cell in the key-name column.
            '''

            keys_model = self.__treeview_keys.get_model()
            key, = keys_model.get(keys_model.get_iter(path),
                                  keys_model.COLUMN_KEY)

            editable.child.set_text(key)

        # pylint: disable-msg=W0613
        def edited(cell, path, new_name):
            '''Update the keys model, when editing of the key-name column has ended.'''

            keys_model = self.__treeview_keys.get_model()
            keys_iter = keys_model.get_iter(path)

            old_name, mapping = keys_model.get(keys_iter,
                                               keys_model.COLUMN_KEY,
                                               keys_model.COLUMN_VALUE)

            if old_name != new_name and not keys_model.has_key(new_name):
                keys_model.remove_iter(keys_iter)
                keys_model.update_key(new_name, mapping.code)
                self.select_key(new_name)

            self.__treeview_keys.grab_focus()

        keys_renderer = gtk.CellRendererCombo()
        keys_renderer.set_properties(editable=True, text_column=0,
                                     model=self.default_keys)

        keys_renderer.connect('edited', edited)
        keys_renderer.connect('editing-started', editing_started)

        text_renderer = gtk.CellRendererText()
        text_renderer.set_properties(xalign=0.5)

        treeview_columns = (
            gtk.TreeViewColumn(_('Name'), keys_renderer,
                               text=model.KeyCodeModel.COLUMN_DISPLAY_NAME),

            gtk.TreeViewColumn(_('Category'), text_renderer,
                               text=model.KeyCodeModel.COLUMN_CATEGORY),

            gtk.TreeViewColumn(_('State'), text_renderer,
                               markup=model.KeyCodeModel.COLUMN_STATE),
        )

        for column in treeview_columns:
            self.__treeview_keys.append_column(column)

        selection = self.__treeview_keys.get_selection()
        selection.connect('changed', self._on_treeview_keys_selection_changed)
        selection.set_mode(gtk.SELECTION_BROWSE)

    def __update_basics_model(self, properties):
        '''Update the entries stored in the basic properties model.'''

        if not properties:
            properties = dict()

        basics = dict([(key, ' '.join(value)) for key, value in properties.items()])
        tree_model_basics = model.DictionaryStore(basics, value_type=gobject.TYPE_STRING)
        self.__treeview_basics.set_model(tree_model_basics)

    def __apply_hardware(self, receiver, device, remote):
        '''
        Select some remote for configuration.
        Information about the receiver is needed for managing lircd.
        '''

        if not remote:
            remote = lirc.Remote()

        self.__receiver, self.__device = receiver, device
        self.__remote = remote

        # Update custom model page from remote
        self.vendor_name = remote.vendor or ''
        self.product_name = remote.product or ''
        self.contributor_name = remote.contributor or ''

        # Update basic configuration page from remote
        self.__update_basics_model(remote.properties)

        # Update keys page from remote
        tree_model = model.KeyCodeModel(remote.key_codes)
        self.__treeview_keys.set_model(tree_model)

        # Update widget sensitivity

        self._on_dialog_changed()

    def _on_learning_timeout(self):
        '''
        Timeout callback for animating the currently selected row,
        when learning key codes.
        '''

        if not self.__learning_row:
            # Abort animation, if now row is selected for learning:
            self.__learning_timeout = 0
            return False

        # Calculate color for blinking "Learning" text:

        p = abs(time() % 2 - 1)/2.0 + 0.5
        q = 1 - p

        style = self.__treeview_keys.get_style()

        text = style.text[gtk.STATE_SELECTED]
        text = [p * color for color in text.red, text.green, text.blue]

        base = style.base[gtk.STATE_SELECTED]
        base = [q * color for color in base.red, base.green, base.blue]

        # Apply blinking "Learning" text:

        args = [int((a + b)/256) for a, b in zip(text, base)]
        args.append(_('Learning'))

        text = '<span weight="bold" foreground="#%02x%02x%02x">%s</span>' % tuple(args)

        keys = self.__treeview_keys.get_model()
        keys.set_state(self.__learning_row.get_path(), text)

        # Continue animation:
        return True

    def __start_learning(self, path):
        '''Start learning of a remote control's key code.'''

        keys = self.__treeview_keys.get_model()

        if self.__learning_row:
            keys.set_state(self.__learning_row.get_path(), None)
        if not self.__learning_timeout:
            self.__learning_timeout = gobject.timeout_add(100, self._on_learning_timeout)

        self.__learning_row = gtk.TreeRowReference(keys, path)
        mapping, = keys.get(keys.get_iter(path), 1)

        configuration = self.__remote.configuration
        driver = self.__receiver.lirc_driver or ''
        device = self.__device or ''

        # pylint: disable-msg=W0613
        @thread_callback
        def report_success(result, sender=None):
            '''Handle success reported by the service backend.'''

            self.__learning_driver = None
            self.__stop_learning()

            hwdb = lirc.RemotesDatabase()
            hwdb.read(StringIO(result))
            remote = len(hwdb) and hwdb[0]

            if remote:
                self.__treeview_keys.get_model().update(remote.key_codes)

        # pylint: disable-msg=W0613
        @thread_callback
        def report_failure(message, sender=None):
            '''Handle failures reported by the service backend.'''

            show_message(self.__dialog, _('Learning of Key Code Failed'), message)

            self.__learning_driver = None
            self.__stop_learning()

        try:
            bus     = backend.get_service_bus()
            service = backend.get_service(bus)

            # Stop the lirc deamon, as some drivers (e.g. lirc_streamzap) do
            # not support concurrent device access:
            service.ManageLircDaemon('stop')

            driver  = service.LearnKeyCode(driver, device, configuration, [mapping.key])

            driver = bus.get_object(service.requested_bus_name, driver)
            driver = dbus.Interface(driver, backend.ExternalToolDriver.INTERFACE_NAME)

            self.__learning_driver = driver

            driver.connect_to_signal('ReportSuccess', report_success)
            driver.connect_to_signal('ReportFailure', report_failure)

            driver.Execute()

        except dbus.DBusException, ex:
            report_failure.callback(ex.message)

        self._on_dialog_changed()

    def __stop_learning(self):
        '''Stop learning of a remote control's key code.'''

        if self.__learning_driver:
            try:
                self.__learning_driver.Release()

            except dbus.DBusException, ex:
                logging.error('Error running learning driver Release')
                logging.error(ex)

            try:
                # restart the lirc deamon (we stopped it before learning):
                backend.get_service().ManageLircDaemon('start')

            except dbus.DBusException, ex:
                logging.error('Error restarting LIRC')
                logging.error(ex)

            self.__learning_driver = None

        if self.__learning_row:
            keys = self.__treeview_keys.get_model()
            keys.set_state(self.__learning_row.get_path(), None)
            self.__learning_row = None

        self._on_dialog_changed()

    # pylint: disable-msg=C0103,W0613
    def _on_treeview_keys_selection_changed(self, selection):
        '''Handle selection of row in the "keys" tree view.'''
        self._on_dialog_changed()
        self.__stop_learning()

    # pylint: disable-msg=W0613
    def _on_treeview_keys_row_activated(self, view, path, column):
        '''Handle activation of row in the "keys" tree view.'''
        self.__start_learning(path)

    def __retrieve_remote_name(self):
        '''Build the symbolic name of the currently edited remote.'''

        name = self.__remote and self.__remote.name

        if not name:
            pieces = [s.replace(' ', '-') for s in self.vendor_name, self.product_name]
            name = '_'.join(pieces)

        return name

    def _on_detect_button_clicked(self, button):
        '''Handle the "Detect" button's "clicked" signal.'''

        @thread_callback
        def report_failure(message):
            '''Handle failures reported by the service backend.'''

            self.__detection_driver = None
            self.__progressbar_detect_basics.hide()
            self.__button_detect_basics.set_sensitive(True)
            show_message(self.__dialog, _('Remote Configuration Failed'), message)

            if service:
                service.ManageLircDaemon('start')

        @thread_callback
        def report_success(result, sender=None):
            '''Handle success reported by the service backend.'''

            self.__detection_driver = None
            self.__progressbar_detect_basics.hide()
            self.__button_detect_basics.set_sensitive(True)

            hwdb = lirc.RemotesDatabase()
            hwdb.read(StringIO(result))

            remote = hwdb[0]
            remote.properties['name'] = [self.__retrieve_remote_name()]

            self.__remote.properties = remote.properties
            self.__update_basics_model(self.__remote.properties)

            if service:
                service.ManageLircDaemon('start')

        @thread_callback
        def report_progress(sender=None):
            '''Handle progress reported by the service backend.'''

            self.__progressbar_detect_basics.pulse()

        @thread_callback
        def request_action(message, details=None, sender=None):
            '''Forward actions requests from the service backend to the user.'''

            self.__progressbar_detect_basics.set_text(message)
            self.__progressbar_detect_basics.set_fraction(0)

            if details:
                # TODO: This dialog should probably have a cancel button.
                response_buttons = (
                    (gtk.RESPONSE_ACCEPT, _('_Start'), gtk.STOCK_EXECUTE),
                )

                show_message(self.__dialog, message, details,
                             message_type=gtk.MESSAGE_INFO,
                             buttons=response_buttons)

            driver.Proceed()

        bus, service, driver = None, None, None

        try:
            self.__stop_detection()

            bus     = backend.get_service_bus()
            service = backend.get_service(bus)

            driver = service.DetectParameters(self.__receiver.lirc_driver or '',
                                              self.__device or '')

            driver = bus.get_object(service.requested_bus_name, driver)
            driver = dbus.Interface(driver, backend.ExternalToolDriver.INTERFACE_NAME)

            driver.connect_to_signal('RequestAction',  request_action)
            driver.connect_to_signal('ReportProgress', report_progress)
            driver.connect_to_signal('ReportSuccess',  report_success)
            driver.connect_to_signal('ReportFailure',  report_failure)

            # TODO: Stop the key-listener, when we know that lircd is disabled.
            service.ManageLircDaemon('stop')

            self.__detection_driver = driver
            self.__detection_driver.Execute()

            self.__button_detect_basics.set_sensitive(False)
            self.__progressbar_detect_basics.show()

        except dbus.DBusException, ex:
            report_failure.callback(ex.message)
            self.__stop_detection()

    def __stop_detection(self):
        '''Stop the basic properties detection driver.'''

        try:
            if self.__detection_driver:
                self.__detection_driver.Release()

        except dbus.DBusException, ex:
            logging.error('Error running detection driver Release')
            logging.warning(ex)

        self.__detection_driver = None


    def _on_dialog_changed(self, widget = None):
        '''Handle major changes to the dialog.'''

        # Calculate completion state

        have_receiver = (None != self.__receiver)
        have_basics = bool(self.__treeview_basics.get_model())
        have_keys = bool(self.__treeview_keys.get_model())
        is_learning = self.__learning_row is not None

        model_complete = (bool(self.vendor_name) and bool(self.product_name))
        basics_complete = (model_complete and have_basics)
        keys_complete = (basics_complete and have_keys)

        selection = self.__treeview_keys.get_selection()
        keys_iter = selection.get_selected()[1]

        # Update state of global widgets:
        self.__button_ok.set_sensitive(model_complete)

        # Update state of model-page widgets:
        self.__usage_hint.set_property('visible', not model_complete)

        # Update state of basics-page widgets:
        self.__treeview_basics.set_sensitive(have_receiver)
        self.__button_detect_basics.set_sensitive(have_receiver)

        # Update state of keys-page widgets:
        self.__treeview_keys.set_sensitive(basics_complete and have_receiver)
        self.__hbuttonbox_keys.set_sensitive(basics_complete and have_receiver)

        self.__button_keys_add.set_sensitive(not is_learning)
        self.__button_keys_remove.set_sensitive(have_keys and not is_learning)
        self.__button_keys_clear.set_sensitive(have_keys and not is_learning)
        self.__button_keys_learn.set_sensitive(keys_iter is not None)
        self.__button_keys_learn.set_active(is_learning)

        self.__label_keys_hint.set_markup(is_learning and
                                          self.__keys_learning_hint or
                                          self.__keys_default_hint)

        self.__image_keys_hint.set_property('visible', is_learning)

    def select_key(self, key_name):
        '''Select the row of the specified key.'''

        keys_model = self.__treeview_keys.get_model()
        tree_iter = keys_model.find_iter(key_name)
        path = None

        if tree_iter:
            # Select the key...
            selection = self.__treeview_keys.get_selection()
            selection.select_iter(tree_iter)

            # ...and make sure that it's visible:
            path = keys_model.get_path(tree_iter)
            self.__treeview_keys.scroll_to_cell(path)


        return path

    # pylint: disable-msg=W0613
    def _on_button_keys_add_clicked(self, button):
        '''Handle the "Add" button's "clicked" signal.'''

        def find_next_key():
            '''Find the next unassigned key.'''

            # Figure out if one of the default keys is missing:

            for key in default_keys:
                if key not in current_keys:
                    return key

            # Otherwise generate a key name:

            i = 0
            while True:
                key = 'KEY_%d' % i

                if not key in current_keys:
                    return key

                i += 1

        selection = self.__treeview_keys.get_selection()
        keys_model, tree_iter = selection.get_selected()

        # pylint: disable-msg=W0612
        current_keys = [mapping.key.upper() for name, mapping in keys_model]
        default_keys = [command.key.upper() for command in
                        lirc.KeyCodes.get_default_commands()]

        if tree_iter:
            # See which key is selected and reorder the default_keys list,
            # that one of its successor will be suggested.
            selected_key, = keys_model.get(tree_iter, 0)

            try:
                i = default_keys.index(selected_key.upper())
                default_keys = default_keys[i+1:] + default_keys[:i+1]

            # pylint: disable-msg=W0704
            except ValueError:
                pass

        # Insert another key to the keys model:
        next_key = find_next_key()
        keys_model.update_key(next_key)
        path = self.select_key(next_key)

        self._on_dialog_changed()
        self.__start_learning(path)

    def _on_button_keys_remove_clicked(self, button):
        '''Handle the "Remove" button's "clicked" signal.'''

        selection = self.__treeview_keys.get_selection()
        keys_model, tree_iter = selection.get_selected()
        index, = keys_model.get_path(tree_iter)

        keys_model.remove_iter(tree_iter)

        path = min(index, len(keys_model) - 1),
        selection.select_path(path)
        self._on_dialog_changed()

    def _on_button_keys_learn_toggled(self, button):
        '''Handle the "Learn Key Code" button's "clicked" signal.'''

        if self.__button_keys_learn.get_active():
            selection = self.__treeview_keys.get_selection()
            keys_model, keys_iter = selection.get_selected()
            path = keys_model.get_path(keys_iter)
            self.__start_learning(path)

        else:
            self.__stop_learning()

    def _on_button_keys_clear_clicked(self, button):
        '''Handle the "Clear" button's "clicked" signal.'''

        self.__treeview_keys.get_model().clear()
        self._on_dialog_changed()

    def _on_close(self, dialog):
        '''Handle the dialog's "close" signal.'''

        self.__stop_detection()
        self.__stop_learning()

        # Prevent that pygtk destroys the dialog on ESC:
        dialog.hide()

        return True

    def _on_response(self, dialog, response):
        '''Handle the dialog's "response" signal.'''

        self.__stop_detection()
        self.__stop_learning()

        # Reset the progress back for detection
        self.__progressbar_detect_basics.hide()
        self.__button_detect_basics.set_sensitive(True)

        if gtk.RESPONSE_OK == response:
            try:
                service = backend.get_service()

                # Get the entered basic information, 
                # so it will be written to the configuration file: 
                self.__remote.contributor = self.contributor_name
                self.__remote.vendor = self.vendor_name
                self.__remote.product = self.product_name

                self.__remote.update_configuration(service)
                service.ManageLircDaemon('restart')

            except dbus.DBusException, ex:
                show_message(self.__dialog,
                             _('Cannot Save Custom Configuration'),
                             ex.message)

                dialog.stop_emission('response')

        elif response > 0:
            dialog.stop_emission('response')

    def run(self, receiver, device, remote):
        '''Show the dialog and return when the window is hidden.'''

        self.__apply_hardware(receiver, device, remote)
        self.__notebook.set_current_page(0)
        self.__entry_vendor.grab_focus()

        self.__dialog.run()
        self.__dialog.hide()

    # pylint: disable-msg=W0212
    vendor_name = property(
        lambda self: self.__entry_vendor.get_text().strip(),
        lambda self, value: self.__entry_vendor.set_text(value))
    product_name = property(
        lambda self: self.__entry_product.get_text().strip(),
        lambda self, value: self.__entry_product.set_text(value))
    contributor_name = property(
        lambda self: self.__entry_contributor.get_text().strip(),
        lambda self, value: self.__entry_contributor.set_text(value))


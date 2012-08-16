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
'''Custom GTK tree-models.'''

import gobject, gtk

from gettext import gettext as _
from gnome_lirc_properties import hardware, lirc

class GenericListStore(gtk.GenericTreeModel):
    '''Generic base class for implementing flat tree-models.'''

    class RowRef(object):
        '''Information for referencing a tree-model row.'''

        def __init__(self, index, key):
            self.__index = index
            self.__key = key

        # pylint: disable-msg=W0212
        path = property(lambda self: (self.__index, ))
        index = property(lambda self: self.__index)
        key = property(lambda self: self.__key)

    def __init__(self, *columns):
        gtk.GenericTreeModel.__init__(self)
        self.__columns = columns

    # pylint: disable-msg=R0201,C0111
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    def on_get_n_columns(self):
        return len(self.__columns)
    def on_get_column_type(self, index):
        return self.__columns[index]

    def on_get_iter(self, path):
        return self.on_iter_nth_child(None, path[0])
    def on_get_path(self, rowref):
        return (rowref.index, )

    def on_iter_children(self, parent):
        return self.on_iter_nth_child(parent, 0)
    def on_iter_has_child(self, rowref):
        return not rowref

    def on_iter_next(self, rowref):
        return self.on_iter_nth_child(None, rowref.index + 1)

class DictionaryStore(GenericListStore):
    '''Flat tree-model which uses a Python dictionary as backend.'''

    COLUMN_KEY = 0
    COLUMN_VALUE = 1

    def __init__(self, values=None, compare=None,
                 value_type=gobject.TYPE_PYOBJECT,
                 extra_columns=()):
        super(DictionaryStore, self).__init__(
            gobject.TYPE_STRING, value_type,
            *extra_columns)

        self.__values = dict()
        self.__keys = list()
        self.__compare = compare

        if values:
            self.update(values)

    def _create_path_list(self):
        '''Creates a list of tree-model paths for all keys of this model.'''

        return [(i, ) for i in range(len(self.__keys))]

    def clear(self):
        '''Removes all entries from this tree-model.'''

        rows = self._create_path_list()
        rows.reverse()

        self.__keys = list()
        self.__values.clear()
        self.invalidate_iters()

        for path in rows:
            self.row_deleted(path)

    def pop(self, key):
        '''Removes the entry referenced by key.'''

        tree_iter = self.find_iter(key)

        if tree_iter is not None:
            self.remove_iter(tree_iter)

    def remove_iter(self, tree_iter):
        '''Removes the entry referenced by tree_iter.'''

        rowref = self.get_user_data(tree_iter)

        self.__keys.remove(rowref.key)
        self.__values.pop(rowref.key)
        self.invalidate_iters()

        self.row_deleted(rowref.path)

    def update(self, values):
        '''Updates the tree-model with new values.'''

        old_keys = set(self.__keys)

        self.__values.update(values)
        self.__keys = list(self.__values.keys())
        self.__keys.sort(self.__compare)
        self.invalidate_iters()

        for path in self._create_path_list():
            tree_iter = self.get_iter(path)
            rowref = self.get_user_data(tree_iter)

            if rowref.key in old_keys:
                self.row_changed(path, tree_iter)

            else:
                self.row_inserted(path, tree_iter)

    def has_key(self, key):
        '''Checks if the tree-model contains a certain key.'''

        return self.__values.has_key(key)

    def find_iter(self, key):
        '''Tries to find the specified entry.'''

        try:
            index = self.__keys.index(key)
            rowref = GenericListStore.RowRef(index, key)
            return self.create_tree_iter(rowref)

        except ValueError:
            return None

    def __nonzero__(self):
        return len(self.__values) > 0

    def __len__(self):
        return len(self.__values)
    def __getitem__(self, key):
        return self.__values[key]
    def __iter__(self):
        return iter(self.__values.items())

    def keys(self):
        '''List of dictionary keys.'''
        return self.__values.keys()

    def items(self):
        '''List of key-value tuples.'''
        return self.__values.items()

    def values(self):
        '''List of dictionary values.'''
        return self.__values.values()

    def on_iter_n_children(self, rowref):
        '''Returns the number of children for the specified row.'''

        return not rowref and len(self.__values) or 0

    def on_iter_nth_child(self, parent, index):
        '''Retrieves the specified child node.'''

        if not parent and index < len(self.__keys):
            return self.RowRef(index, self.__keys[index])

        return None

    def on_get_value(self, rowref, column):
        '''Retrieves the value stored in the specified row and column.'''

        if self.COLUMN_KEY == column:
            return rowref.key
        if self.COLUMN_VALUE == column:
            return self.__values[rowref.key]

        return None

class ReceiverVendorList(DictionaryStore):
    '''Tree model containing all supported IR receiver vendors.'''

    __str_none = _('None')

    def __init__(self, hardware_manager=None):
        def compare_values(a, b):
            '''Compares two vendor list entries.'''

            if self.__str_none == a:
                return -1

            if self.__str_none == b:
                return +1

            return cmp(a, b)

        super(ReceiverVendorList, self).__init__(compare=compare_values)

        self.__linux_input_devices = DictionaryStore()
        self.update({_('Linux Input Device'): self.__linux_input_devices})

        if hardware_manager:
            hardware_manager.connect('receiver-added', self._on_receiver_added)
            hardware_manager.connect('receiver-removed', self._on_receiver_removed)

            for udi, receiver in hardware_manager.devinput_receivers.items():
                self._on_receiver_added(hardware_manager, receiver)

    def _on_receiver_added(self, sender, receiver):
        '''Merge new hot-plugable receiver.'''
        self.__linux_input_devices.update({receiver.product: receiver})

    def _on_receiver_removed(self, sender, receiver):
        '''Drop removed hot-plugable receiver.'''
        self.__linux_input_devices.pop(receiver.product)

    def load(self, database):
        '''Populates the tree-model from the specified hardware database.'''

        assert(isinstance(database, hardware.HardwareDatabase))

        vendors = dict()

        for sect in database.sections():
            vendor_name, product_name = [s.strip() for s in sect.split(':', 1)]
            products = vendors.get(vendor_name)

            if not products:
                vendors[vendor_name] = products = dict()

            properties = dict(database.items(sect),
                              vendor = vendor_name,
                              product = product_name)

            products[product_name] = lirc.Receiver(**properties)

        vendors = [
            (name, DictionaryStore(products))
            for name, products in vendors.items()
        ]

        empty_store = DictionaryStore({self.__str_none: None})
        empty_row = self.__str_none, empty_store
        vendors.append(empty_row)

        self.update(dict(vendors))

class RemoteVendorList(DictionaryStore):
    '''Tree model containing all supported IR remote vendors.'''

    def load(self, database):
        '''Populates the tree-model from the specified remotes database.'''

        assert(isinstance(database, lirc.RemotesDatabase))

        vendors = dict()

        for remote in database:
            vendor_name = remote.vendor or _('Unknown')
            product_name = remote.product or remote.name

            products = vendors.get(vendor_name)

            if not products:
                vendors[vendor_name] = products = dict()

            products[product_name] = remote

        vendors = [
            (name, DictionaryStore(products))
            for name, products in vendors.items()
        ]

        self.update(dict(vendors))

class KeyCodeModel(DictionaryStore):
    '''Custom tree-model for managing remote control keys.'''

    COLUMN_DISPLAY_NAME = 2
    COLUMN_CATEGORY = 3
    COLUMN_STATE = 4

    class KeyMapping(object):
        '''Meta information around some remote control key.'''

        def __init__(self, key, code = 0):
            self.__key = key
            self.__code = code
            self.__state = None

        def __get_state(self):
            '''Retrieves the state of this key mapping as human-readable text.'''

            if None != self.__state:
                return self.__state

            if self.__code:
                return _('Assigned')

            return _('Unassigned')

        def __set_state(self, state):
            '''Updates the state of this key mapping.'''

            self.__state = state

        def __cmp__(self, other):
            assert isinstance(other, KeyCodeModel.KeyMapping)

            return (
                cmp(self.display_name, other.display_name) or
                cmp(self.key,          other.key))

        # pylint: disable-msg=W0212
        code = property(lambda self: self.__code)
        key = property(lambda self: self.__key.upper())
        category = property(lambda self: lirc.KeyCodes.get_category(self.__key))
        display_name = property(lambda self: lirc.KeyCodes.get_display_name(self.__key))

        state = property(__get_state, __set_state)

    def __init__(self, key_codes):
        self.__key_codes = key_codes

        # pylint: disable-msg=C0103,C0111
        def compare_key_mappings(a, b):
            return cmp(self[a], self[b])

        columns = gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING
        super(KeyCodeModel, self).__init__(key_codes, extra_columns=columns,
                                           compare=compare_key_mappings)

    @classmethod
    def __map_key_codes(cls, key_codes):
        '''Maps raw key-codes to KeyMapping objects.'''

        return dict([
            (key.upper(), cls.KeyMapping(key, code))
            for key, code in key_codes.items() or []])

    def on_get_value(self, rowref, column):
        '''Retrieves the value stored in the specified row and column.'''

        if self.COLUMN_DISPLAY_NAME == column:
            return self[rowref.key].display_name
        if self.COLUMN_CATEGORY == column:
            return self[rowref.key].category
        if self.COLUMN_STATE == column:
            return self[rowref.key].state

        return super(KeyCodeModel, self).on_get_value(rowref, column)

    def set_state(self, path, state):
        '''Changes the state of the row referenced by path.'''

        tree_iter = self.get_iter(path)
        rowref = self.get_user_data(tree_iter)
        self[rowref.key].state = state

        self.row_changed(path, tree_iter)

    def remove_iter(self, tree_iter):
        '''Removes the entry referenced by tree_iter.'''

        rowref = self.get_user_data(tree_iter)
        self.__key_codes.pop(rowref.key)

        super(KeyCodeModel, self).remove_iter(tree_iter)

    def update(self, key_codes):
        '''Update the scan codes for several remote control keys.'''

        key_codes = dict(key_codes)
        self.__key_codes.update(key_codes)
        key_codes = self.__map_key_codes(key_codes)
        super(KeyCodeModel, self).update(key_codes)

    def update_key(self, key, code=0):
        '''Update the scan code for a certain remote control key.'''

        self.update([(key, code)])

    def count_keys(self, category):
        '''Counts the keys in the specified categories.'''

        count = 0

        for name in self.__key_codes.keys():
            if lirc.KeyCodes.get_category(name) == category:
                count += 1

        return count


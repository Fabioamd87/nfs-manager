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
LIRC specific classes.
'''

import errno, gobject, logging, os, re

from datetime              import datetime
from gettext               import gettext as _
from gnome_lirc_properties import config
from locale                import LC_TIME, setlocale
from StringIO              import StringIO
from socket                import AF_UNIX, socket, error as SocketError

class ParseError(Exception):
    '''
    Execption describing a parse error.
    '''
    @apply

    def message():
        def get(self):
            return self._message

        def set(self, value):
            self._message = value

        return property(get, set)

    def __init__(self, filename, lineno, msg = _('Malformed configuration file')):
        self.message = '%s:%d: %s' % (filename, lineno, msg)

class Receiver(object):
    '''
    Description of an IR receiver.
    '''

    def __init__(self, vendor, product, **properties):
        self.__vendor, self.__product = vendor, product
        self.__vendor_id = int(properties.get('vendor-id', '0'), 0)
        self.__product_id = int(properties.get('product-id', '0'), 0)
        self.__properties = dict(properties)

        self.__compatible_remotes = properties.get('compatible-remotes')
        
        if self.__compatible_remotes:
            self.__compatible_remotes = [
                name.strip() for name in
                self.__compatible_remotes.split(',')]

    def find_supplied_remote(self, remotes_db):
        '''
        Look up compatible remotes in the remotes db,
        and return the first one found as "supplied remote".
        '''

        remotes = self.__compatible_remotes or []
        remotes = map(remotes_db.get, remotes)
        remotes = filter(None, remotes)

        return remotes and remotes[0]

    def update_configuration(self, mechanism, device):
        '''
        Updates configuration files to use this kind of receiver.
        '''

        mechanism.WriteReceiverConfiguration(self.vendor, self.product,
                                             self.lirc_driver or 'default',
                                             device or '', self.kernel_module or '')

    def __str__(self):
        return '%s: %s' % (self.__vendor, self.__product)
    def __repr__(self):
        return '<Receiver: vendor=%s, product=%s>' % (self.__vendor, self.__product)

    def __getitem__(self, key):
        return self.__properties[key]

    # pylint: disable-msg=W0212
    vendor = property(lambda self: self.__vendor)
    vendor_id = property(lambda self: self.__vendor_id)

    product = property(lambda self: self.__product)
    product_id = property(lambda self: self.__product_id)

    device = property(lambda self: self.__properties.get('device'))
    device_nodes = property(lambda self: self.__properties.get('device-nodes'))
    kernel_module = property(lambda self: self.__properties.get('kernel-module'))
    lirc_driver = property(lambda self: self.__properties.get('lirc-driver', 'default'))
    compatible_remotes = property(lambda self: self.__compatible_remotes)

class Remote(object):
    """
    Description of an IR remote.
    """

    # pylint: disable-msg=R0913

    def __init__(self, database = None, filename = None,
                 vendor = None, product = None, contributor = None,
                 properties = list(), key_codes = dict()):

        self.__properties = dict(properties)
        self.__property_order = [item[0] for item in properties]
        self.__key_codes = key_codes
        self.__filename = filename
        self.__database = database

        self.__vendor = vendor
        self.__product = product
        self.__name = ' '.join(self.__properties.get('name'))
        self.__contributor = contributor

    def write(self, writer):
        '''
        Writes configuration file of this remote to writer.
        '''

        # Retrieve locale independent timestamp:
        locale = setlocale(LC_TIME, 'C')
        now = datetime.now().strftime('%c')
        setlocale(LC_TIME, locale)

        # Write comment header with meta information:
        print >> writer, '# LIRC configuration file for %s' % self.name
        print >> writer, '# Generated by GNOME LIRC properties on %s' % now
        print >> writer, '# from %s' % self.filename
        print >> writer, '#'

        if self.contributor:
            print >> writer, '# contributed by %s' % self.contributor
            print >> writer, '#'

        if self.vendor:
            print >> writer, '# brand: %s' % self.vendor
        if self.product:
            print >> writer, '# model no. of remote control: %s' % self.product
        if self.vendor or self.product:
            print >> writer, '#'

        # Write remote block

        ident = -max([len(key) for key in self.__property_order])

        print >> writer
        print >> writer, 'begin remote'

        for key in self.__property_order:
            args = ident, key, ' '.join(self.__properties[key])
            print >> writer, '  %*s  %s' % args

        # Write key codes

        print >> writer
        print >> writer, '  begin codes'

        key_codes = list(self.__key_codes.items())
        key_codes.sort(lambda a, b: cmp(a[0], b[0]))

        ident = -max([len(s) for s in self.__key_codes.keys() + ['']])

        for key, value in key_codes:
            print >> writer, '    %*s  %s' % (ident, key, value)

        print >> writer, '  end codes'
        print >> writer, 'end remote'

        return writer

    def __get_configuration(self):
        '''
        Retreives the configuration file of this remote as string.
        '''
        return self.write(StringIO()).getvalue()

    def __set_properties(self, value):
        '''
        Updates the basic properties of this remote.
        '''

        self.__properties = dict(value)
        self.__property_order = list(self.__properties.keys())
        self.__property_order.sort()

    def update_configuration(self, mechanism):
        '''
        Updates configuration files to use this remote.
        '''

        mechanism.WriteRemoteConfiguration(self.configuration)

    def __set_contributor(self, value):
        '''
        Updates the contributor property of this remote.
        '''
        
        self.__contributor = value

    def __set_vendor(self, value):
        '''
        Updates the vendor property of this remote.
        '''
        
        self.__vendor = value

    def __set_product(self, value):
        '''
        Updates the product property of this remote.
        '''
        
        self.__product = value

    def __repr__(self):
        return '<Remote: %s>' % self.__name

    # pylint: disable-msg=W0212
    name = property(lambda self: self.__name)
    product = property(lambda self: self.__product, __set_product)
    vendor = property(lambda self: self.__vendor, __set_vendor)
    contributor = property(lambda self: self.__contributor, __set_contributor)

    configuration = property(__get_configuration)

    database = property(lambda self: self.__database)
    filename = property(lambda self: self.__filename)
    key_codes = property(lambda self: self.__key_codes)
    properties = property(lambda self: self.__properties, __set_properties)

class RemotesDatabase(object):
    '''
    Reads and interprets an IR remote configuration file,
    such as /etc/lirc/lircd.conf or the ones at /usr/share/lirc/remotes.
    '''

    def __init__(self):
        super(RemotesDatabase, self).__init__()
        self.__remotes = dict()

    def clear(self):
        '''
        Removes all database entries.
        '''

        self.__remotes.clear()

    def load_folder(self, root=config.LIRC_REMOTES_DATABASE):
        '''
        Recursively reads all configuration files found in that folder.
        '''

        if not os.path.isdir(root):
            logging.warning('Cannot read remote database folder: %s', root)
            return False

        logging.info('Reading remote database from %s...', root)

        for path, subdirs, files in os.walk(root):
            # skip folders with meta information
            subdirs[:] = [name for name in subdirs
                          if not name in ('CVS', ) and
                             not name.startswith('.')]

            # extract path component after the root path for current folder:
            relative_path = path[len(root):]

            while os.path.isabs(relative_path):
                relative_path = relative_path[len(os.path.sep):]

            # read files in current folder:
            for name in files:
                if not name.startswith('.'):
                    self.read(reader=open(os.path.join(path, name)),
                              filename=os.path.join(relative_path, name),
                              database=root)

        return True

    def load(self, filename):
        '''
        Reads remote configuration from filename.
        '''

        self.read(open(filename),
                  database=os.path.dirname(filename),
                  filename=os.path.basename(filename))

    def read(self, reader, filename=None, database=None, replace=False):
        '''
        Reads remote configuration from reader.
        '''

        parser = RemotesParser()

        try:
            parser.read(reader, filename, database)

        except ParseError, ex:
            logging.error(ex.message)
            return False

        self.__update_remotes(parser.remotes, replace)

        return True

    def __update_remotes(self, remotes, replace=False):
        '''
        Updates the remotes dictionary.
        '''

        for remote in remotes:
            previous_remote = self.__remotes.get(remote.name)

            if not previous_remote or (replace and remote.database != previous_remote.database):
                self.__remotes[remote.name] = remote
                continue

            logging.warning('%s: Remote %s listed twice in %s and %s.',
                            remote.database, remote.name, remote.filename,
                            previous_remote.filename)

    def get(self, name, default=None):
        '''Looks up the remote matching name.'''

        return self.__remotes.get(name, default)

    def find(self, vendor, product, default=None):
        '''Tries to find the specified remote control.'''

        # Cope with Unknown vendors:
        # We store 'Unknown' (not translated) in the configuration file in backend.WriteRemoteConfiguration() if vendor is None:
        vendor_name = vendor
        if(vendor_name == 'Unknown'):
          vendor_name = None

        # Try looking at the remote.product
        # (the combo lists product.name if remote.product is None):
        for remote in self:
            #print ("RemotesDatabase.find(): remote.vendor=%s, remote_product=%s\n" % (remote.vendor, remote.product))
            if (remote.vendor == vendor_name and
                remote.product == product):
                return remote

        # Try looking at the remote.name
        # (the combo lists product.name if remote.product is None):
        for remote in self:
            #print ("RemotesDatabase.find(): remote.vendor=%s, remote_product=%s\n" % (remote.vendor, remote.product))
            if (remote.vendor == vendor_name and
                remote.name == product):
                return remote

        return default

    def __iter__(self):
        return iter(self.__remotes.values())
    def __len__(self):
        return len(self.__remotes)
    def __getitem__(self, i):
        return self.__remotes.values()[i]

class RemotesParser(object):
    '''
    Parser for remote control configuration files.
    '''

    __re_vendor = re.compile(r'^#\s+brand:\s*\b(.*)\b\s*$')
    __re_product = re.compile(r'^#\s+model\b[^:]*:\s*\b(.*)\b\s*$')
    __re_contributor = re.compile(r'^#\s+contributed by\s+\b(.*)\b\s*$')
    __re_block = re.compile(r'^\s*(begin|end)\s+\b(.*)\b\s*$')
    __re_key_value = re.compile(r'^\s*(\S+)\s+\b(.*)\b\s*$')

    def __init__(self):
        self.__blocks = list()
        self.__remotes = list()

        self.__current_line = 0
        self.__filename = None
        self.__database = None

        self.__next_remote()

    def __begin_block(self, name):
        '''
        Track a new block beginning.
        '''

        self.__blocks.append(name)

    def __end_block(self, name):
        '''
        Track the current block ending.
        '''

        if len(self.__blocks) and (name == self.current_block):
            self.__blocks = self.__blocks[:-1]
            return True

        return False

    def __next_remote(self):
        '''
        Reset all gathered remote information.
        '''

        # pylint: disable-msg=W0201
        self.__key_codes, self.__properties = list(), list()
        self.__vendor, self.__product = None, None
        self.__contributor = None

    def __parse_block_statements(self, line):
        '''
        Tries to parse the next line as block changing statement (begin/end).
        '''

        # Check if current line contains a block statement:
        match = self.__re_block.match(line)

        if not match:
            return False

        # Evaluate block statement:
        token, name = match.groups()

        if 'begin' == token:
            self.__begin_block(name)
            return True

        assert 'end' == token

        if self.__end_block(name):
            if 'remote' == name:
                remote = Remote(self.__database, self.__filename,
                                self.__vendor, self.__product, self.__contributor,
                                self.__properties, dict(self.__key_codes))

                self.__remotes.append(remote)
                self.__next_remote()

            return True

        raise ParseError(self.__filename, self.current_line)

    def __parse_remote_block_statements(self, line):
        '''
        Parse a statement within a "remote" block.
        '''

        # Drop comments:
        comment = line.find('#')

        if comment >= 0:
            line = line[:comment]

        # Tokenize line:
        match = self.__re_key_value.match(line)

        if not match:
            return False

        key, value = match.groups()

        # Handle tokens as required by current block:
        if 'codes' == self.current_block:
            self.__key_codes.append((key, value))
            return True

        if 'remote' == self.current_block:
            self.__properties.append((key, value.split()))
            return True

    def __parse_comments(self, line):
        '''
        Try to extract meta information from comments.
        '''

        match = self.__re_vendor.match(line)

        if match:
            self.__vendor = match.group(1)
            return True

        match = self.__re_product.match(line)

        if match:
            self.__product = match.group(1)
            return True

        match = self.__re_contributor.match(line)

        if match:
            self.__contributor = match.group(1)
            return True

        return False

    def read(self, reader, filename=None, database=None):
        '''
        Parses the configuration found in reader.
        '''

        if not filename:
            # StringIO instances don't have a name attribute.
            # Therefore use getattr to avoid AttributeErrors.
            filename = getattr(reader, 'name', str(reader.__class__))

        self.__filename = filename
        self.__database = database

        self.__current_line = 0

        for line in reader:
            self.__current_line += 1

            if self.__parse_block_statements(line):
                continue
            if ('remote' == self.toplevel_block and
                self.__parse_remote_block_statements(line)):
                continue

            self.__parse_comments(line)
 
    def __repr__(self):
        return repr(vars(self))

    # pylint: disable-msg=W0212
    remotes = property(lambda self: self.__remotes)
    current_line = property(lambda self: self.__current_line)
    current_block = property(lambda self: len(self.__blocks) and self.__blocks[-1])
    toplevel_block = property(lambda self: len(self.__blocks) and self.__blocks[0])

class KeyCodeCategory(object):
    '''
    Container for various key-code categories.
    '''

    DEFAULT = _('Default Namespace')

def create_commands_table():
    '''
    Create a dict mapping the command name to full details,
    including the key name, the command name, and the human-readable translated display name.
    This is used to
    - create a .lircrc config file mapping all the keys to commands.
    - discover human-readable names for commands.
    '''

    #TODO: Add other keys (and alternatives key names):
    commands_by_category = [
        (KeyCodeCategory.DEFAULT, (
            ('BTN_LEFT',           'move_up_key',        _('Move Up')),
            ('BTN_MODE',           'move_up_key',        _('Move Up')),
            ('BTN_RIGHT',          'move_up_key',        _('Move Up')),
            ('KEY_0',              '0_key',              _('0')),
            ('KEY_1',              '1_key',              _('1')),
            ('KEY_2',              '2_key',              _('2')),
            ('KEY_3',              '3_key',              _('3')),
            ('KEY_4',              '4_key',              _('4')),
            ('KEY_5',              '5_key',              _('5')),
            ('KEY_6',              '6_key',              _('6')),
            ('KEY_7',              '7_key',              _('7')),
            ('KEY_8',              '8_key',              _('8')),
            ('KEY_9',              '9_key',              _('9')),
            ('KEY_A',              'a_key',              _('A')),
            ('KEY_AGAIN',          'again_key',          _('Again')),
            ('KEY_ANGLE',          'angle_key',          _('Angle')),
            ('KEY_AUDIO',          'audio_key',          _('Audio')),
            ('KEY_AUX',            'aux_key',            _('Auxiliary')),
            ('KEY_B',              'b_key',              _('B')),
            ('KEY_BACK',           'back_key',           _('Back')),
            ('KEY_BACKSPACE',      'backspace_key',      _('Backspace')),
            ('KEY_BLUE',           'blue_key',           _('Blue')),
            ('KEY_BOOKMARKS',      'bookmarks_key',      _('Bookmarks')),
            ('KEY_C',              'c_key',              _('C')),
            ('KEY_CAMERA',         'camera_key',         _('Camera')),
            ('KEY_CANCEL',         'cancel_key',         _('Cancel')),
            ('KEY_CD',             'cd_key',             _('CD')),
            ('KEY_CHANNELDOWN',    'channel_down_key',   _('Channel Down')),
            ('KEY_CHANNELUP',      'channel_up_key',     _('Channel Up')),
            ('KEY_CLEAR',          'clear_key',          _('Clear')),
            ('KEY_CLOSE',          'close_key',          _('Close')),
            ('KEY_CONFIG',         'config_key',         _('Configuration')),
            ('KEY_D',              'd_key',              _('D')),
            ('KEY_DELETE',         'delete_key',         _('Delete')),
            ('KEY_DIRECTORY',      'directory_key',      _('Directory')),
            ('KEY_DOT',            'dot_key',            _('Dot')),
            ('KEY_DOWN',           'down_key',           _('Down')),
            ('KEY_DVD',            'dvd_key',            _('DVD')),
            ('KEY_E',              'e_key',              _('E')),
            ('KEY_EJECTCD',        'eject_cd_key',       _('Eject CD')),
            ('KEY_END',            'end_key',            _('End')),
            ('KEY_ENTER',          'enter_key',          _('Enter')),
            ('KEY_EPG',            'epg_key',            _('EPG')),
            ('KEY_ESC',            'esc_key',            _('Escape')),
            ('KEY_EXIT',           'exit_key',           _('Exit')),
            ('KEY_F',              'f_key',              _('F')),
            ('KEY_F1',             'f1_key',             _('F1')),
            ('KEY_F2',             'f2_key',             _('F2')),
            ('KEY_F3',             'f3_key',             _('F3')),
            ('KEY_F4',             'f4_key',             _('F4')),
            ('KEY_FASTFORWARD',    'fast_forward_key',   _('Fast Forward')),
            ('KEY_FORWARD',        'forward_key',        _('Forward')),
            ('KEY_G',              'g_key',              _('G')),
            ('KEY_GREEN',          'green_key',          _('Green')),
            ('KEY_H',              'h_key',              _('H')),
            ('KEY_HELP',           'help_key',           _('Help')),
            ('KEY_HOME',           'home_key',           _('Home')),
            ('KEY_INFO',           'info_key',           _('Information')),
            ('KEY_KPASTERISK',     'kp_asteristk_key',   _('Asterisk')),
            ('KEY_KPMINUS',        'kp_minus_key',       _('Minus')),
            ('KEY_KPPLUS',         'kp_plus_key',        _('Plus')),
            ('KEY_L',              'l_key',              _('L')),
            ('KEY_LANGUAGE',       'language_key',       _('Language')),
            ('KEY_LEFT',           'left_key',           _('Left')),
            ('KEY_LIST',           'list_key',           _('List')),
            ('KEY_M',              'm_key',              _('M')),
            ('KEY_MAIL',           'mail_key',           _('Mail')),
            ('KEY_MAX',            'max_key',            _('Maximum')),
            ('KEY_MEDIA',          'media_key',          _('Media')),
            ('KEY_MENU',           'menu_key',           _('Menu')),
            ('KEY_MODE',           'mode_key',           _('Mode')),
            ('KEY_MP3',            'mp3_key',            _('MP3')),
            ('KEY_MUTE',           'mute_key',           _('Mute')),
            ('KEY_NEXT',           'next_key',           _('Next')),
            ('KEY_NEXTSONG',       'next_key',           _('Next')),
            ('KEY_OK',             'ok_key',             _('OK')),
            ('KEY_OPEN',           'open_key',           _('Open')),
            ('KEY_OPTION',         'option_key',         _('Options')),
            ('KEY_PAGEDOWN',       'page_down_key',      _('Page Down')),
            ('KEY_PAGEUP',         'page_up_key',        _('Page Up')),
            ('KEY_PAUSE',          'pause_key',          _('Pause')),
            ('KEY_PC',             'pc_key',             _('PC')),
            ('KEY_PHONE',          'phone_key',          _('Phone')),
            ('KEY_PLAY',           'play_key',           _('Play')),
            ('KEY_PLAYPAUSE',      'play_pause_key',     _('Pause')),
            ('KEY_PLUS',           'plus_key',           _('Plus')),
            ('KEY_POWER',          'power_key',          _('Power')),
            ('KEY_PREVIOUS',       'previous_key',       _('Previous')),
            ('KEY_PREVIOUSSONG',   'previous_key',       _('Previous')),
            ('KEY_R',              'r_key',              _('R')),
            ('KEY_RADIO',          'radio_key',          _('Radio')),
            ('KEY_RECORD',         'record_key',         _('Record')),
            ('KEY_RED',            'red_key',            _('Red')),
            ('KEY_REWIND',         'rewind_key',         _('Rewind')),
            ('KEY_RIGHT',          'right_key',          _('Right')),
            ('KEY_S',              's_key',              _('S')),
            ('KEY_SELECT',         'select_key',         _('Select')),
            ('KEY_SETUP',          'setup_key',          _('Setup')),
            ('KEY_SLASH',          'slash_key',          _('Slash')),
            ('KEY_SLEEP',          'sleep_key',          _('Sleep')),
            ('KEY_SLOW',           'slow_key',           _('Slow')),
            ('KEY_SPACE',          'space_key',          _('Space')),
            ('KEY_STOP',           'stop_key',           _('Stop')),
            ('KEY_SUBTITLE',       'subtitle_key',       _('Subtitle')),
            ('KEY_T',              't_key',              _('T')),
            ('KEY_TAB',            'tab_key',            _('Tab')),
            ('KEY_TEXT',           'text_key',           _('Text')),
            ('KEY_TIME',           'time_key',           _('Time')),
            ('KEY_TITLE',          'title_key',          _('Title')),
            ('KEY_TV',             'tv_key',             _('TV')),
            ('KEY_UNDO',           'undo_key',           _('Undo')),
            ('KEY_UP',             'up_key',             _('Up')),
            ('KEY_VCR',            'vcr_key',            _('VCR')),
            ('KEY_VIDEO',          'video_key',          _('Video')),
            ('KEY_VOLUMEDOWN',     'volume_down_key',    _('Volume Down')),
            ('KEY_VOLUMEUP',       'volume_up_key',      _('Volume Up')),
            ('KEY_WWW',            'www_key',            _('WWW')),
            ('KEY_YELLOW',         'yellow_key',         _('Yellow')),
            ('KEY_ZOOM',           'zoom_key',           _('Zoom')),
        )),

    ]

    class Command(object):
        '''
        Description of a remote control command.
        '''

        def __init__(self, key, name, category, display_name):
            self.__key = key
            self.__name = name
            self.__category = category
            self.__display_name = display_name

        # pylint: disable-msg=W0212
        key = property(lambda self: self.__key)
        name = property(lambda self: self.__name)
        category = property(lambda self: self.__category)
        display_name = property(lambda self: self.__display_name)

    for i, category in enumerate(commands_by_category):
        category_name, command_list = category

        commands_by_category[i] = [
            (key, Command(key, name, category_name, display_name))
            for key, name, display_name in command_list]

    commands = reduce(lambda a, b: a + b, commands_by_category)
    return dict(commands), [row[1] for row in commands_by_category[0]]

class KeyCodes(object):
    '''
    Facilites for retreiving information about remote control key codes.
    '''

    __commands, __default_commands = create_commands_table()

    @classmethod
    def get_default_commands(cls):
        '''
        Query all commons in the default namespace.
        '''
        return cls.__default_commands

    @classmethod
    def get_display_name(cls, key):
        '''
        Get a (translated) human-readable name for a remote control command/key.
        For instance return "Play/Pause" for the "toggle_play_pause_key" command.

        @param command: The command name
        @result A string.
        '''

        command = cls.__commands.get(key.upper())

        if command:
            return command.display_name

        return key.replace('_', ' ')

    @classmethod
    def get_category(cls, key):
        '''
        Get the human-readable category name for a remote control command/key.
        '''

        command = cls.__commands.get(key.upper())

        if command:
            return command.category

        return _('Custom Key Code')

class KeyListener(gobject.GObject):
    '''
    Watches remote control key presses reported by lircd.
    '''

    __gsignals__ = {
        'key-pressed': (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_INT,
             gobject.TYPE_STRING, gobject.TYPE_INT64)),

        'changed': (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            tuple()),
    }

    def __init__(self, socket_name=config.LIRCD_SOCKET):
        # pylint: disable-msg=E1002
        super(KeyListener, self).__init__()

        self.__running = False
        self.__socket_name = socket_name
        self.__reconnect_source = 0
        self.__socket_source = 0
        self.__socket = None
        self.__buffer = ''

    def start(self):
        '''Starts listening.'''

        self.__running = True

        if not self.__connect():
            self.__reconnect()

    def stop(self):
        '''Stops listening.'''

        self.__running = False
        self.__disconnect()

    def __on_io_event(self, fd, condition):
        '''Handle I/O events on the lircd socket.'''

        logging.info('I/O event on lirc socket %d: %d', fd, condition)

        if condition & gobject.IO_IN:
            logging.info('reading from lirc socket %d...', fd)

            try:
              BUFFER_SIZE = 128
              packet = self.__socket and self.__socket.recv(BUFFER_SIZE)
            except SocketError, ex:
              logging.error('__on_io_event(): socket.recv() threw exception reading from lirc socket: %s', ex.message)
              packet = ''

            logging.info('...%d bytes received.', len(packet))
            self.__buffer += packet

            while True:
                eol = self.__buffer.find('\n')

                if eol < 0:
                    break

                packet = self.__buffer[:eol]
                self.__buffer = self.__buffer[eol + 1:]

                logging.info('processing packet: %r', packet)

                try:
                    code, repeat, name, remote = packet.split()
                    repeat = int(repeat, 16)
                    code = long(code, 16)

                    # pylint: disable-msg=E1101
                    self.emit('key-pressed', remote, repeat, name, code)

                # pylint: disable-msg=W0704
                except ValueError:
                    pass

        if condition & gobject.IO_HUP:
            if self.__running:
                def restart():
                    if self.__running:
                        self.start()

                    return False

                gobject.timeout_add(1000, restart)

            else:
                self.__disconnect()

            return False

        return True

    def __connect(self):
        '''Connects to the lircd socket.'''

        self.__disconnect()

        logging.info('trying to connect to lircd...')

        self.__socket = None
        self.__buffer = ''

        try:
            self.__socket = socket(AF_UNIX)

            self.__socket_source = (
                gobject.io_add_watch(self.__socket.fileno(),
                                     gobject.IO_IN | gobject.IO_HUP,
                                     self.__on_io_event))

            self.__socket.connect(self.__socket_name)

            logging.info('listening on %s (fd=%d, source=%d)...',
                         self.__socket_name, self.__socket.fileno(),
                         self.__socket_source)

            # pylint: disable-msg=E1101
            self.emit('changed')

            return True

        except SocketError, ex:
            if ex[0] not in (errno.ENOENT, errno.ECONNREFUSED):
                # pychecker says "Object (ex) has no attribute (message)", and that's not true.
                logging.error('Cannot connect to %s: %s', self.__socket_name, ex.message)

            self.__disconnect()
            return False

    def __disconnect(self):
        '''Disconnects from the lircd socket.'''

        self.__buffer = ''

        if self.__socket_source:
            logging.info('disconnecting source: %d', self.__socket_source)
            gobject.source_remove(self.__socket_source)
            self.__socket_source = 0

        if self.__socket:
            logging.info('closing socket: %d', self.__socket.fileno())
            self.__socket.close()
            self.__socket = None

        # pylint: disable-msg=E1101
        self.emit('changed')

    def __reconnect(self):
        '''Tries to reconnects to the lircd socket.'''

        if not self.__reconnect_source:
            self.__reconnect_source = gobject.timeout_add(5000, self._on_reconnect)

    def _on_reconnect(self):
        '''Called regularly when the key listener tries to reconnect.'''

        if self.__connect():
            self.__reconnect_source = 0
            return False

        return True

    # pylint: disable-msg=W0212,W1001
    connected = property(lambda self: None != self.__socket)

class HardwareConfParser(object):
    '''
    Parse the (Debian/Ubuntu-specific) /etc/lirc/hardware.conf file.

    Ideally, the standard RawConfigParser could do this,
    but that does not work when there are no section headings.
    '''

    def __init__(self, filename):
        self.__values = dict()

        for line in open(filename, 'r'):
            tokens = [t.strip() for t in line.split('=', 1)]

            if len(tokens) < 2:
                continue

            key, value = tokens

            value = value.strip('"') # Remove quotes
            value = ''.join(value.split('\\')) # Remove escaping
            self.__values[key] = value

    def __getitem__(self, key):
        try:
            return self.__values[key]

        except KeyError:
            # Try old Gutsy keys:
            if key.startswith('RECEIVER_'):
                return self.__getitem__(key[9:])
            if key.startswith('REMOTE_'):
                return self.__getitem__(key[7:])

            # Ok, that key really isn't there.
            raise

    def get(self, key, default=None):
        '''
        Retreives the value for key, or default when the key doesn't exist.
        '''

        try:
            return self[key]

        except KeyError:
            return default

def find_remote_config():
    '''Finds the location our customized lircd.conf file.'''

    return config.LIRC_REMOTE_CONF

def check_hardware_settings(selected_remote):
    '''Check if the hardware settings are sane.'''

    remote_config = find_remote_config()

    if not os.path.exists(remote_config):
        return True

    if not re.search(
        r'^\s*include\s+<%s>\s*$' % re.escape(config.LIRC_REMOTE_CONF),
        open(config.LIRC_DAEMON_CONF).read(), re.MULTILINE):
        return False

    parser = RemotesParser()
    parser.read(open(remote_config))

    for remote in parser.remotes:
        if remote is None:
            return False

        if selected_remote is None:
            return False

        if (remote.vendor == selected_remote.vendor and
            remote.product == selected_remote.product):
            return True

    return False

if '__main__' == __name__:
    print find_remote_config()

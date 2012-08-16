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
'''Facilities for handling the D-BUS driven configuration backend.'''

import dbus, dbus.service, gobject, logging, shutil
import errno, os, os.path, re, pty, signal, tempfile

from gettext               import gettext as _
from gnome_lirc_properties import config, lirc
from gnome_lirc_properties import shellquote as ShellQuote
from StringIO              import StringIO

# Modern flavors of dbus bindings have that symbol in dbus.lowlevel,
# for old flavours the internal _dbus_bindings module must be used.

try:
    # pylint: disable-msg=E0611
    from dbus.lowlevel import HANDLER_RESULT_NOT_YET_HANDLED

except ImportError:
    from _dbus_bindings import HANDLER_RESULT_NOT_YET_HANDLED

class AccessDeniedException(dbus.DBusException):
    '''This exception is raised when some operation is not permitted.'''

    _dbus_error_name = 'org.gnome.LircProperties.AccessDeniedException'

class UnsupportedException(dbus.DBusException):
    '''This exception is raised when some operation is not supported.'''

    _dbus_error_name = 'org.gnome.LircProperties.UnsupportedException'

class UsageError(dbus.DBusException):
    '''This exception is raised when some operation was not used properly.'''

    _dbus_error_name = 'org.gnome.LircProperties.UsageError'

class PolicyKitService(dbus.service.Object):
    '''A D-BUS service that uses PolicyKit for authorization.'''

    def _check_permission(self, sender, action=config.POLICY_KIT_ACTION):
        '''
        Verifies if the specified action is permitted, and raises
        an AccessDeniedException if not.

        The caller should use ObtainAuthorization() to get permission.
        '''

        try:
            if sender:
                kit = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
                kit = dbus.Interface(kit, 'org.freedesktop.PolicyKit1.Authority')

                # Note that we don't use CheckAuthorization with bus name
                # details because we have no ways to get the PID of the
                # front-end, so we're left with checking that its bus name
                # is authorised instead
                # See http://bugzilla.gnome.org/show_bug.cgi?id=540912
                (granted, _, details) = kit.CheckAuthorization(
                                ('system-bus-name', {'name': sender}),
                                action, {}, dbus.UInt32(1), '', timeout=600)
                logging.info('authorization of system bus name \'%s\': %r', sender, granted)

                if not granted:
                    raise AccessDeniedException('Session not authorized by PolicyKit')

        except AccessDeniedException:
            raise

        except dbus.DBusException, ex:
            raise AccessDeniedException(ex.message)

class ExternalToolDriver(PolicyKitService):
    '''
    A D-BUS service which mainly is implemented
    as wrapper around some external program.
    '''

    # pylint: disable-msg=C0103,E0602

    INTERFACE_NAME = 'org.gnome.LircProperties.ExternalToolDriver'

    def __init__(self, connection, path='/'):
        super(ExternalToolDriver, self).__init__(connection, path)

        self.__line_buffer = ''
        self.__pid = -1
        self.__fd = -1
        self._hup_expected = False

    def _spawn_external_tool(self):
        '''Launches the external tool backing this service.'''

        pid, fd = pty.fork()

        if 0 == pid:
            self._on_run_external_tool()
            assert False # should not be reached

        os.waitpid(pid, os.P_NOWAIT)
        return pid, fd

    def __io_handler(self, fd, condition):
        '''Handles I/O events related to the backing external tool.'''

        if condition & gobject.IO_IN:
            # Read next chunk for the file descriptor and buffer it:
            chunk = os.read(fd, 4096)
            self._on_next_chunk(chunk)
            self.__line_buffer += chunk

            # Extract complete lines from buffer:
            while True:
                linebreak = self.__line_buffer.find('\n')

                # Abort, since the next line isn't complete yet:
                if linebreak < 0:
                    break

                # Extract next line and normalize it:
                line = self.__line_buffer[:linebreak].rstrip()
                self.__line_buffer = self.__line_buffer[linebreak + 1:]

                # Handle next line:
                self._on_next_line(line)

        if condition & gobject.IO_HUP:
            # Shutdown the service, when the backing tool terminates:
            self._on_hangup()
            return False

        # Keep the handler alive:
        return True

    def _send_response(self, response='\n'):
        '''Sends a response, by default just a line feed, to the external tool.'''

        os.write(self.__fd, response)

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', out_signature='',
                         sender_keyword='sender')
    def Execute(self, sender=None):
        '''Requests the service to launch the backing tool.'''

        self._check_permission(sender)

        self.__line_buffer = ''
        self.__pid, self.__fd = self._spawn_external_tool()

        if -1 != self.__fd:
            self._hup_expected = False
            gobject.io_add_watch(self.__fd,
                                 gobject.IO_IN | gobject.IO_HUP,
                                 self.__io_handler)

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', out_signature='',
                         sender_keyword='sender')
    def Proceed(self, sender=None):
        '''Requests the service to send a line feed to the backing tool.'''

        self._check_permission(sender)
        self._send_response('\n')

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', out_signature='',
                         sender_keyword='sender')
    def Release(self, sender=None):
        '''Releases the service and shuts down the backing tool, when still alive.'''

        self._check_permission(sender)

        try:
            if -1 != os.waitpid(self.__pid, os.P_NOWAIT):
                print 'Terminating child process %d...' % self.__pid
                # Kill irrecord and its children and wait for left-overs
                # FIXME use self.__pid not -self.__pid when irrecord is fixed
                # https://bugzilla.redhat.com/show_bug.cgi?id=593704
                os.kill(-self.__pid, signal.SIGTERM)
                os.waitpid(self.__pid, os.P_WAIT)

        except OSError, ex:
            if ex.errno != errno.ESRCH:
                print 'Cannot terminate process %d: %s' % (self.__pid, ex.message)

        self.__pid = 0
        self.remove_from_connection()

    @dbus.service.signal(dbus_interface=INTERFACE_NAME, signature='')
    def ReportProgress(self):
        '''Signals that the backing tool reported some progress.'''

    @dbus.service.signal(dbus_interface=INTERFACE_NAME, signature='s')
    def ReportSuccess(self, message):
        '''Signals that the backing tool reported sucess.'''

    @dbus.service.signal(dbus_interface=INTERFACE_NAME, signature='s')
    def ReportFailure(self, message):
        '''Signals that the backing tool reported failure.'''

    @dbus.service.signal(dbus_interface=INTERFACE_NAME, signature='ss')
    def RequestAction(self, title, details):
        '''Signals that the backing tool requests some action.'''

    def _on_run_external_tool(self):
        '''Executes the external tool.'''
    def _on_next_chunk(self, chunk):
        '''Processes the next chunk of output from the external tool.'''
    def _on_next_line(self, line):
        '''Processes the next line of output from the external tool.'''
    def _on_hangup(self):
        '''Handles termination of the external tool.'''

    # pylint: disable-msg=W0212
    _pid = property(lambda self: self.__pid)

class IrRecordDriver(ExternalToolDriver):
    '''D-BUS service that runs irrecord.'''

    # pylint: disable-msg=C0103

    # Following strings are some known error messages of irrecord 0.5,
    # as shipped with Ubuntu 7.10 on 2008-02-13:

    _errors = {
        'could not init hardware': _('Could not initialize hardware.'),
        'gap not found, can\'t continue': _('No key presses recognized. Gap not found.'),
        'no data for 10 secs, aborting': _('No key presses recognized. Aborting.'),
    }

    # Following strings indicate state changes in irrecord 0.5,
    # as shipped with Ubuntu 7.10 on 2008-02-13:

    _token_intro_text       = 'This program will record the signals'
    _token_hold_one_button  = 'Hold down an arbitrary button.'
    _token_random_buttons   = 'Now start pressing buttons on your remote control.'
    _token_next_key         = 'Please enter the name for the next button'
    _token_wait_toggle_mask = 'If you can\'t see any dots appear'
    _token_finished         = 'Successfully written config file.'
    _token_almost_finished  = 'Creating config file in raw mode.' # Shown when _token_finished should not be expected.

    # Last instance index for automatic object path creation:
    __last_instance = 0

    # pylint: disable-msg=R0913
    def __init__(self, connection, driver, device,
                 filename='lircd.conf.learning', path=None):
        assert not os.path.isabs(filename)

        if not path:
            IrRecordDriver.__last_instance += 1
            path = '/IrRecordDriver%d' % self.__last_instance

        self._workdir = tempfile.mkdtemp(prefix='gnome-lirc-properties-')
        self._cmdargs = [config.LIRC_IRRECORD, '--driver=%s' % driver]
        self._filename = filename

        if device:
            self._cmdargs.append('--device=%s' % ShellQuote.shellquote(device))
        if filename:
            self._cmdargs.append(filename)

        super(IrRecordDriver, self).__init__(connection, path)
        logging.info("__init__.IrRecordDriver(): irrecord cmdargs=%s", self._cmdargs)

    def _on_run_external_tool(self):
        '''Enters to the working directory and executes irrecord.'''

        os.chdir(self._workdir)
        self._prepare_workdir()

        args, env = self._cmdargs, {'LC_ALL': 'C'}
        print 'running %s in %s...' % (args[0], self._workdir)
        print 'arguments: %r' % args[1:]

        os.execve(args[0], filter(None, args), env)

    def _prepare_workdir(self):
        '''Virtual method for preparation of the working directory.'''

    def _cleanup_workdir(self):
        '''Virtual method for cleaning up the working directory.'''

        print 'cleaning up %s...' % self._workdir

        for name in os.listdir(self._workdir):
            os.unlink(os.path.join(self._workdir, name))

    def _on_hangup(self):
        '''Shutdown the driver, when irrecord terminates unexpectedly.'''

        if(self._hup_expected):
            # This was expected. It's a success:
            filename = os.path.join(self._workdir, self._filename)
            configuration = open(filename).read()
            self.ReportSuccess(configuration)
            self.Release()

        if list(self.locations): #self.locations is in the dbus base class. This check prevents a shutdown when the dbus service should be kept alive.
            # irrecord stopped when we were expecting more interaction:
            self.ReportFailure(_('Custom remote control configuration aborted unexpectedly.'))
            self.Release()

    def _find_error_messages(self, line):
        '''Tries to identify error messages in line and reports them.'''

        for token, message in self._errors.items():
            if line.find(token) >= 0:
                self.ReportFailure(message)
                self.Release()
                return True

        return False

    def __del__(self):
        self._cleanup_workdir()
        os.rmdir(self._workdir)

class DetectParametersDriver(IrRecordDriver):
    '''D-BUS service that runs irrecord for detecting basic remote properties.'''

    def __init__(self, connection, driver, device):
        super(DetectParametersDriver, self).__init__(connection, driver, device)
        self.__report_progress = False
        self._hup_expected = False

    def _prepare_workdir(self):
        '''Removes the configuration file from working directory when needed.'''

        if os.path.exists(self._filename):
            os.unlink(self._filename)

    def _on_next_line(self, line):
        '''Processes the next line of irrecord output.'''

        # pylint: disable-msg=R0911

        print '%d:%s' % (self._pid, line)

        # Identify known error messages:

        if self._find_error_messages(line):
            return

        # Try to catch state changes:

        if line.startswith(self._token_intro_text):
            self._send_response()
            return

        if line.startswith(self._token_hold_one_button):
            self.RequestAction(_('Hold down any remote control button.'), '')
            return

        if line.startswith(self._token_random_buttons):
            # TODO: The talk of "steps" here does not make much sense
            # in terms of a GTK+ progress bar.

            self.RequestAction(
                _('Press random buttons on your remote control.'),
                _('When you press the Start button, it is very important that you press many different buttons and hold them down for approximately one second. Each button should move the progress bar by at least one step, but in no case by more than ten steps.'))

            return

        if line.startswith(self._token_next_key):
            self._send_response()
            return

        if line.startswith(self._token_wait_toggle_mask):
            self.RequestAction(
                _('Press a button repeatedly as fast as possible.'),
                _('Make sure you keep pressing the <b>same</b> button and that you <b>do not hold</b> the button down.\nWait a little between button presses if you cannot see any progress.'))

            return

        if line.startswith(self._token_finished):
            filename = os.path.join(self._workdir, self._filename)
            configuration = open(filename).read()
            self.ReportSuccess(configuration)
            self.Release()
            return

        if line.startswith(self._token_almost_finished):
            # For some remotes (such as the XBox replacement remote, 
            # with the StreamZap receiver, there is no additional output after 
            # pressing Enter to stop the key-code learning, 
            # so _token_finished is never seen,
            # but in that case we see this message instead beforehand.
            self._hup_expected = True
            return

    def _on_next_chunk(self, chunk):
        '''
        Identifies progress indications in the next chunk of irrecord output,
        and reports them.
        '''

        if '.' == chunk:
            self.ReportProgress()

class LearnKeyCodeDriver(IrRecordDriver):
    '''D-BUS service that runs irrecord for detecting key-codes.'''

    # pylint: disable-msg=R0913
    def __init__(self, connection, driver, device, configuration, keys):
        super(LearnKeyCodeDriver, self).__init__(connection, driver, device)
        self.__keys, self.__configuration = keys, configuration

    def _prepare_workdir(self):
        '''Writes the supplied configuration file into the  working directory.'''

        open(self._filename, 'w').write(self.__configuration)

    def _on_next_line(self, line):
        '''Processes the next line of irrecord output.'''

        print '%d:%s' % (self._pid, line)

        # Identify known error messages:

        if self._find_error_messages(line):
            return

        # Try to catch state changes:

        if line.startswith(self._token_intro_text):
            self._send_response()
            return

        if line.startswith(self._token_next_key):
            if not self.__keys:
                self._send_response()
                return

            self._send_response('%s\n' % self.__keys.pop(0))
            return

        if line.startswith(self._token_finished):
            configuration = self._find_configuration()

            if configuration:
                self.ReportSuccess(configuration)

            else:
                self.ReportFailure(_('Cannot find recorded key codes'))

            self.Release()
            return

    def _find_configuration(self):
        '''Finds the configuration file generated by irrecord.'''

        for suffix in '.new', '.conf', '':
            filename = os.path.join(self._workdir, self._filename + suffix)

            if os.path.isfile(filename):
                return open(filename).read()

        return None

    def _spawn_external_tool(self):
        '''Runs irrecord.'''
        return super(LearnKeyCodeDriver, self)._spawn_external_tool()

class BackendService(PolicyKitService):
    '''A D-Bus service that PolicyKit controls access to.'''

    # pylint: disable-msg=C0103,E0602

    INTERFACE_NAME = 'org.gnome.LircProperties.Mechanism'
    SERVICE_NAME   = 'org.gnome.LircProperties.Mechanism'
    IDLE_TIMEOUT   =  300

    # These are extra fields set by our GUI:

    __re_receiver_directive = re.compile(r'^\s*RECEIVER_(VENDOR|MODEL)=')

    if config.STARTUP_STYLE is 'fedora':
        __re_remote_directive = re.compile(r'^\s*(LIRC_DRIVER|LIRC_DEVICE|MODULES|' +
                                           r'LIRCD_OPTIONS|LIRCD_CONF|VENDOR|MODEL)=')
    else:
        # These are used by the Debian/Ubuntu packages, as of 2008-02-12.
        # The "REMOTE_" prefix is made optional, since it only was introduced
        # with lirc 0.8.3~pre1-0ubuntu4 of Hardy Heron.
        __re_remote_directive = re.compile(r'^\s*(?:REMOTE_)?(DRIVER|DEVICE|MODULES|' +
                                           r'LIRCD_ARGS|LIRCD_CONF|VENDOR|MODEL)=')
    __re_start_lircd      = re.compile(r'^\s*START_LIRCD=')

    def __init__(self, connection=None, path='/'):
        if connection is None:
            connection = get_service_bus()

        super(BackendService, self).__init__(connection, path)

        self.__name = dbus.service.BusName(self.SERVICE_NAME, connection)
        self.__loop = gobject.MainLoop()
        self.__timeout = 0

        connection.add_message_filter(self.__message_filter)

    def __message_filter(self, connection, message):
        '''
        D-BUS message filter that keeps the service alive,
        as long as it receives message.
        '''

        if self.__timeout:
            self.__start_idle_timeout()

        return HANDLER_RESULT_NOT_YET_HANDLED

    def __start_idle_timeout(self):
        '''Restarts the timeout for terminating the service when idle.'''

        if self.__timeout:
            gobject.source_remove(self.__timeout)

        self.__timeout = gobject.timeout_add(self.IDLE_TIMEOUT * 1000,
                                             self.__timeout_cb)

    def __timeout_cb(self):
        '''Timeout callback that terminates the service when idle.'''

        # Keep service alive, as long as additional objects are exported:
        if self.connection.list_exported_child_objects('/'):
            return True

        print 'Terminating %s due to inactivity.' % self.SERVICE_NAME
        self.__loop.quit()

        return False

    def run(self):
        '''Creates a GLib main loop for keeping the service alive.'''

        print 'Running %s.' % self.SERVICE_NAME
        print 'Terminating it after %d seconds of inactivity.' % self.IDLE_TIMEOUT

        self.__start_idle_timeout()
        self.__loop.run()

    def _write_hardware_configuration(self,
                                      remote_values=dict(),
                                      receiver_values=dict(),
                                      start_lircd=None):
        '''Updates lirc's hardware.conf file on Debian/Ubuntu.'''

        if start_lircd is not None:
            start_lircd = str(bool(start_lircd)).lower()

        oldfile = config.LIRC_HARDWARE_CONF
        newfile = '%s.tmp' % oldfile

        if not os.path.isfile(oldfile):
            raise UnsupportedException('Cannot find %s script' % oldfile)

        logging.info('Updating %s...', oldfile)
        logging.info('- receiver_values: %r', receiver_values)
        logging.info('- remote_values: %r', remote_values)

        output = file(newfile, 'w')
        for line in file(oldfile, 'r'):

            # Identify directives starting with REMOTE_ and replacing their values with ours.
            # Remove entry from the dict on match, so we know what was written.
            match = self.__re_remote_directive.match(line)
            value = match and remote_values.pop(match.group(1), None)

            if value is not None:
                logging.info('- writing %s"%s"', match.group(0), value)
		if value == "":
                    print >> output, ('%s"%s"' % (match.group(0), value))
                else:
                    print >> output, ('%s"%s"' % (match.group(0), ShellQuote.shellquote(value)))
                continue

            # Identify directives starting with RECEIVER_ and replacing their values with ours.
            # Remove entry from the dict on match, so we know what was written.
            match = self.__re_receiver_directive.match(line)
            value = match and receiver_values.pop(match.group(1), None)

            if value is not None:
                logging.info('- writing %s"%s"', match.group(0), value)
		if value == "":
                    print >> output, ('%s"%s"' % (match.group(0), value))
	        else:
                    print >> output, ('%s"%s"' % (match.group(0), ShellQuote.shellquote(value)))
                continue

            if config.STARTUP_STYLE is not 'fedora':
                # Deal with the START_LIRCD line:

                match = self.__re_start_lircd.match(line)

                if match:
                    # pychecker says "Using a conditional statement with a constant value (true)",
                    # which is ridicilous, considering Python 2.4 doesn't have conditional statements
                    # yet (PEP 308, aka. 'true_value if condition else false_value') and the expression
                    # below ('condition and true_value or false_value') is the recommended equivalent.
                    value = (start_lircd is None) and 'true' or start_lircd
                    start_lircd = None

                    print >> output, (match.group(0) + ShellQuote.shellquote(value))
                    continue

            output.write(line)

        # Write out any values that were not already in the file,
        # and therefore just replaced:

        if remote_values:
            print >> output, '\n# Remote settings required by gnome-lirc-properties'
        for key, value in remote_values.items():
            if config.STARTUP_STYLE is not 'fedora':
                print >> output, ('REMOTE_%s="%s"' % (key, ShellQuote.shellquote(value)))
            else:
                print >> output, ('%s="%s"' % (key, ShellQuote.shellquote(value)))

        if receiver_values:
            print >> output, '\n# Receiver settings required by gnome-lirc-properties'
        for key, value in receiver_values.items():
            print >> output, ('RECEIVER_%s="%s"' % (key, ShellQuote.shellquote(value)))

        if start_lircd is not None and config.STARTUP_STYLE is not 'fedora':
            print >> output, '\n# Daemon settings required by gnome-lirc-properties'
            print >> output, ('START_LIRCD=%s' % start_lircd)

        if config.STARTUP_STYLE is 'fedora':
            value = (start_lircd is None) and 'true' or start_lircd
            start_lircd = None
            if 'true' == value:
                args = '/sbin/chkconfig', 'lirc', 'on'
            else:
                args = '/sbin/chkconfig', 'lirc', 'off'
            os.spawnv(os.P_WAIT, args[0], args)

        # Replace old file with new contents:

        os.unlink(oldfile)
        os.rename(newfile, oldfile)

    # pylint: disable-msg=R0913
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='sssss', out_signature='',
                         sender_keyword='sender')
    def WriteReceiverConfiguration(self, vendor, product,
                                   driver, device, modules,
                                   sender=None):
        '''
        Update the /etc/lirc/hardware.conf file,
        so that lircd is started as specified.
        '''

        self._check_permission(sender)

        if config.STARTUP_STYLE is 'fedora':
            remote_values = {
                'LIRC_DRIVER': driver,
                'LIRC_DEVICE': device,
                'MODULES': modules,
                'LIRCD_OPTIONS': '',
                'LIRCD_CONF': '',
            }
        else:
            remote_values = {
                'DRIVER': driver,
                'DEVICE': device,
                'MODULES': modules,
                'LIRCD_ARGS': '',
                'LIRCD_CONF': '',
            }

        receiver_values = {
            'VENDOR': vendor,
            'MODEL': product,
        }

        self._write_hardware_configuration(remote_values, receiver_values)

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='s', out_signature='',
                         sender_keyword='sender')
    def WriteRemoteConfiguration(self, contents, sender=None):
        '''
        Write the contents to the system lircd.conf file.
        PolicyKit will not allow this function to be called without sudo/root
        access, and will ask the user to authenticate if necessary, when
        the application calls PolicyKit's ObtainAuthentication().
        '''

        self._check_permission(sender)

        if not contents:
            raise UsageError('Bad IR remote configuration file')

        # Parse contents:

        hwdb = lirc.RemotesDatabase()
        hwdb.read(StringIO(contents))
        remote = len(hwdb) and hwdb[0]

        # Update hardware.conf with choosen remote:

        if remote:
            values = {
                'VENDOR': remote.vendor or 'Unknown', # Note; We do not translate Unknown here, though we do in the UI.
                'MODEL': remote.product or remote.name
            }

            self._write_hardware_configuration(remote_values=values)

        # Write remote configuration:
        filename = lirc.find_remote_config()

        self.__write_include_statement(filename)

        print contents

        print 'Updating %s...' % filename
        file(filename, 'w').write(contents)

    @staticmethod
    def __write_include_statement(redirect):
        '''Write include statement to central lircd.conf file.'''

        # read central lirc configuration file file:
        try:
            contents = open(config.LIRC_DAEMON_CONF).read()

        except IOError:
            contents = ''

        # drop entire configuration file, if it still contains embedded
        # configuration files - for instance from Gutsy:
        pattern = r'^\s*begin\s+remote\s*$'
        pattern = re.compile(pattern, re.MULTILINE)
        match   = pattern.search(contents)

        if match:
            contents = ''

        # find existing include statement:
        include_statement = 'include <%s>\n' % redirect
        pattern = r'^\s*(#.*)?include\s+<%s>\s*$' % re.escape(redirect)
        pattern = re.compile(pattern, re.MULTILINE)
        match   = pattern.search(contents)

        if match is None:
            # no statement found, create entirely new file:
            print 'Dropping whole configuration file'

            if not contents:
                contents  = '# This configuration has been automatically generated\n'
                contents += '# by the GNOME LIRC Properties control panel.\n'
                contents += '#\n'
                contents += '# Feel free to add any custom remotes to the configuration\n'
                contents += '# via additional include directives or below the existing\n'
                contents += '# include directives from your selected remote and/or\n'
                contents += '# transmitter.\n'
                contents += '#\n'

            contents += '\n'
            contents += '# Configuration selected with GNOME LIRC Properties\n'
            contents += include_statement

        elif match.group(1):
            print 'Found directive, updating it'
            head = contents[:match.start()]
            tail = contents[match.end():]
            contents = (head + include_statement + tail)

        else:
            contents = None

        if contents:
            open(config.LIRC_DAEMON_CONF, 'w').write(contents)

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', out_signature='',
                         sender_keyword='sender')
    def ManageLircDaemon(self, action, sender=None):
        '''Starts the LIRC daemon.'''

        permitted_actions = [ 'enable', 'disable', 'stop', 'start', 'restart' ]

        self._check_permission(sender)

        print 'Managing lircd: %s...' % action

	if action not in permitted_actions:
	    raise AccessDeniedException

        if 'enable' == action:
            if config.STARTUP_STYLE is 'fedora':
                args = '/sbin/chkconfig', 'lirc', 'on'
                os.spawnv(os.P_WAIT, args[0], args)
            else:
                self._write_hardware_configuration(start_lircd=True)

        elif 'disable' == action:
            if config.STARTUP_STYLE is 'fedora':
                args = '/sbin/chkconfig', 'lirc', 'off'
                os.spawnv(os.P_WAIT, args[0], args)
            else:
                self._write_hardware_configuration(start_lircd=False)

        else:
            args = '/etc/init.d/lirc', action
            os.spawnv(os.P_WAIT, args[0], args)

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='ss', out_signature='o',
                         sender_keyword='sender')
    def DetectParameters(self, driver, device, sender=None):
        '''Detects parameters of the IR remote by running irrecord.'''

        self._check_permission(sender)

        return DetectParametersDriver(self.connection, driver, device)

    # pylint: disable-msg=R0913
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='sssas', out_signature='o',
                         sender_keyword='sender')
    def LearnKeyCode(self, driver, device, configuration, keys, sender=None):
        '''Learn the scan code of some IR remote key by running irrecord.'''

        self._check_permission(sender)

        return LearnKeyCodeDriver(self.connection,
                                  driver, device,
                                  configuration,
                                  keys)

def get_service_bus():
    '''Retrieves a reference to the D-BUS system bus.'''

    return dbus.SystemBus()

def get_service(bus=None):
    '''Retrieves a reference to the D-BUS driven configuration service.'''

    if not bus:
        bus = get_service_bus()

    service = bus.get_object(BackendService.SERVICE_NAME, '/')
    service = dbus.Interface(service, BackendService.INTERFACE_NAME)

    return service

if __name__ == '__main__':
    # Support full tracing when --debug switch is passed:

    from sys import argv

    if '--debug' in argv or '-d' in argv:
        logging.getLogger().setLevel(logging.NOTSET)

    # Integrate DBus with GLib main loops.

    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    # Run the service.

    BackendService().run()


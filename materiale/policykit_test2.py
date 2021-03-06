import dbus

class Backend(dbus.service.Object):
    '''Backend manager.

    This encapsulates all services of the backend and manages all handlers. It
    is implemented as a dbus.service.Object, so that it can be called through
    D-BUS as well (on the /DeviceDriver object path).
    '''
    DBUS_INTERFACE_NAME = 'com.test'

    def __init__(self, handler_dir=None, detect=True):
        '''Initialize backend (no hardware/driver detection).

        In order to be fast and not block client side applications for very
        long, detect can be set to False; in that case this constructor does
        not detect hardware and drivers, and client-side applications must call
        detect() or db_init() at program start.
        '''
        self.handler_dir = handler_dir
        self.handler_pool = {}
        self.driver_dbs = None
        self.hardware = None

        # cached D-BUS interfaces for _check_polkit_privilege()
        self.dbus_info = None
        self.polkit = None
        self.main_loop = None

        self.enforce_polkit = True
        self._package_operation_in_progress = False
    
    @dbus.service.method(DBUS_INTERFACE_NAME,
        in_signature='', out_signature='', sender_keyword='sender',
        connection_keyword='conn')
    def test(self, sender=None, conn=None):
        '''Detect available hardware and handlers.

        This method can take pretty long, so it should be called asynchronously
        with a large (or indefinite) timeout, and client UIs should display a
        bouncing progress bar (if appropriate). If the backend is already
        initialized, this returns immediately.

        This must be called once at client-side program start. If the Backend
        object is initialized with argument "detect=True", this happens
        automatically. If the client just wants to perform a search_driver()
        operation on remote driver DBs on already detected hardware, it can
        only call db_init() instead.
        '''
        self._reset_timeout()
        self._check_polkit_privilege(sender, conn, 'com.ubuntu.devicedriver.info')

    def _check_polkit_privilege(self, sender, conn, privilege):
            '''Verify that sender has a given PolicyKit privilege.

            sender is the sender's (private) D-BUS name, such as ":1:42"
            (sender_keyword in @dbus.service.methods). conn is
            the dbus.Connection object (connection_keyword in
            @dbus.service.methods). privilege is the PolicyKit privilege string.

            This method returns if the caller is privileged, and otherwise throws a
            PermissionDeniedByPolicy exception.
            '''
            if sender is None and conn is None:
                # called locally, not through D-BUS
                return
            if not self.enforce_polkit:
                # that happens for testing purposes when running on the session
                # bus, and it does not make sense to restrict operations here
                return

            # get peer PID
            if self.dbus_info is None:
                self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                    '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
            pid = self.dbus_info.GetConnectionUnixProcessID(sender)
            
            # query PolicyKit
            if self.polkit is None:
                self.polkit = dbus.Interface(dbus.SystemBus().get_object(
                    'org.freedesktop.PolicyKit1',
                    '/org/freedesktop/PolicyKit1/Authority', False),
                    'org.freedesktop.PolicyKit1.Authority')
            try:
                # we don't need is_challenge return here, since we call with AllowUserInteraction
                (is_auth, _, details) = self.polkit.CheckAuthorization(
                        ('unix-process', {'pid': dbus.UInt32(pid, variant_level=1),
                            'start-time': dbus.UInt64(0, variant_level=1)}), 
                        privilege, {'': ''}, dbus.UInt32(1), '', timeout=600)
            except dbus.DBusException as e:
                if e._dbus_error_name == 'org.freedesktop.DBus.Error.ServiceUnknown':
                    # polkitd timed out, connect again
                    self.polkit = None
                    return self._check_polkit_privilege(sender, conn, privilege)
                else:
                    raise

            if not is_auth:
                logging.debug('_check_polkit_privilege: sender %s on connection %s pid %i is not authorized for %s: %s' %
                        (sender, conn, pid, privilege, str(details)))
                raise PermissionDeniedByPolicy(privilege)
if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    myservice = Backend()
    print('starting service')
    Gtk.main()
    bus = dbus.SessionBus()
    _check_polkit_privilege('sender', 'conn', 'com.nfsmanager.write')

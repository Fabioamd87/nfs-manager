#!/usr/bin/python

from gi.repository import GObject
import os
import time
import subprocess

import dbus
import dbus.service
import dbus.mainloop.glib

class DemoException(dbus.DBusException):
    _dbus_error_name = 'org.nfsmanager.DemoException'

class PermissionDeniedByPolicy(dbus.DBusException):
    _dbus_error_name = 'com.ubuntu.DeviceDriver.PermissionDeniedByPolicy'

class SomeObject(dbus.service.Object):
    
    def __init__(self, conn=None, object_path=None, bus_name=None):
        dbus.service.Object.__init__(self,conn,object_path,bus_name)
        
        # the following variables are used by _check_polkit_privilege
        self.dbus_info = None
        self.polkit = None
        self.enforce_polkit = True
        
    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='s', out_signature='as',
                         sender_keyword='sender', connection_keyword='conn')
    def HelloWorld(self, hello_message, sender=None, conn=None):
        """Print hello_message and log it in /tmp/example-service-log, 
        then return a list"""
        self._check_polkit_privilege(sender, conn, 'org.nfsmanager.hi')
        print((str(hello_message)))
        SomeObject._log_in_file("/tmp/example-service-log", str(hello_message))
        return ["Hello", " from example-service.py", "with unique name",
                bus.get_unique_name()]
    
    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='sss', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def Mount(self, address, path, mountpoint, sender=None, conn=None):
        print('mounting ',address+':'+path,' in ', mountpoint)
        subprocess.check_output(['mount' , address + ':' + path , mountpoint])
        return True

    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='s', out_signature='b',
                         sender_keyword='sender', connection_keyword='conn')
    def Umount(self, mountpoint, sender=None, conn=None):
        print('umounting ', mountpoint)
        subprocess.check_output(['umount' , mountpoint])
        return True

    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def RaiseException(self, sender=None, conn=None):
        raise DemoException('The RaiseException method does what you might '
                            'expect')

    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='', out_signature='(ss)',
                         sender_keyword='sender', connection_keyword='conn')
    def GetTuple(self, sender=None, conn=None):
        return ("Hello Tuple", " from example-service.py")

    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='', out_signature='a{ss}',
                         sender_keyword='sender', connection_keyword='conn')
    def GetDict(self, sender=None, conn=None):
        return {"first": "Hello Dict", "second": " from example-service.py"}

    @dbus.service.method("org.nfsmanager.Interface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def Exit(self, sender=None, conn=None):
        mainloop.quit()
    
    @classmethod
    def _log_in_file(klass, filename, string):
        date = time.asctime(time.localtime())
        ff = open(filename, "a")
        ff.write("%s : %s\n" %(date,str(string)))
        ff.close()
        

    def _check_polkit_privilege(self, sender, conn, privilege):
        # from jockey
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
            SomeObject._log_in_file('/tmp/example-service-log','_check_polkit_privilege: sender %s on connection %s pid %i is not authorized for %s: %s' %
                    (sender, conn, pid, privilege, str(details)))
            raise PermissionDeniedByPolicy(privilege)


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    bus = dbus.SystemBus()
    name = dbus.service.BusName("org.nfsmanager", bus)
    object = SomeObject(bus, '/NFSManager')

    mainloop = GObject.MainLoop()
    print("Running example service.")
    mainloop.run()

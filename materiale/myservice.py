#!/usr/bin/env python

# myservice.py
# simple python-dbus service that exposes 1 method called hello()

from gi.repository import GObject, Gio, Polkit #python3 
import os, sys

import dbus
import dbus.service
import dbus.mainloop.glib
 
class MyDBUSService(dbus.service.Object):
    def __init__(self, conn=None, object_path=None, bus_name=None):
        dbus.service.Object.__init__(self,conn,object_path,bus_name)
        
    def on_tensec_timeout(self, loop):
        print("Ten seconds have passed. Now exiting.")
        loop.quit()
        return False

    def do_cancel(self, cancellable):
        print("Timer has expired; cancelling authorization check")
        cancellable.cancel()
        return False

    def check_authorization_cb(self, authority, res, loop):
        try:
            result = authority.check_authorization_finish(res)
            if result.get_is_authorized():
                print("Authorized")
                self.writefile()
            elif result.get_is_challenge():
                print("Challenge")
            else:
                print("Not authorized")
        except GObject.GError as error:
             print("Error checking authorization: %s" % error.message)
            
        print("Authorization check has been cancelled "
              "and the dialog should now be hidden.\n"
              "This process will exit in ten seconds.")
        GObject.timeout_add(10000, self.on_tensec_timeout, loop)

    @dbus.service.method(dbus_interface='org.nfsmanager', out_signature='s', out_signature='', sender_keyword='sender', connection_keyword='conn')
    def hello(self, sender=None, conn=None):
        #print('start')
        return "hello world, I am"+str(os.getuid())
    
    @dbus.service.method(dbus_interface='org.nfsmanager')
    def write(self):
        #ho notato che quando questo metodo viene eseguito come root non funziona
        action_id = 'org.nfsmanager.write'
        mainloop = GObject.MainLoop()
        authority = Polkit.Authority.get()
        subject = Polkit.UnixProcess.new(os.getppid())
        cancellable = Gio.Cancellable()
        GObject.timeout_add(10 * 1000, self.do_cancel, cancellable)

        authority.check_authorization(subject,
            action_id,
            None,
            Polkit.CheckAuthorizationFlags.ALLOW_USER_INTERACTION,
            cancellable,
            self.check_authorization_cb,
            mainloop)

    @dbus.service.method(dbus_interface='org.nfsmanager')
    def writefile(self):
        f = open('/etc/test','a')
        f.write('line')
        f.close()

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    name = dbus.service.BusName("org.nfsmanager", bus)
    object = MyDBUSService(bus, '/NFSManager')

    mainloop = GObject.MainLoop()
    print('starting service')
    mainloop.run()

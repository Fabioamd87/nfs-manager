#!/usr/bin/env python

import sys
from traceback import print_exc

import dbus

def main():
    bus = dbus.SystemBus()

    try:
        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")

        # you can either specify the dbus_interface in each call...
        hello_reply_list = remote_object.HelloWorld("Hello from example-client.py!",
            dbus_interface = "org.nfsmanager.Interface")
    except dbus.DBusException:
        print_exc()
        sys.exit(1)

    print (hello_reply_list)

    # ... or create an Interface wrapper for the remote object
    iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")

    hello_reply_tuple = iface.GetTuple()

    print(hello_reply_tuple)

    hello_reply_dict = iface.GetDict()

    print(hello_reply_dict)

    # D-Bus exceptions are mapped to Python exceptions
    try:
        iface.RaiseException()
    except dbus.DBusException as e:
        print(str(e))

    # introspection is automatically supported
    print(remote_object.Introspect(dbus_interface="org.freedesktop.DBus.Introspectable"))

    iface.Mount('192.168.1.4','/media','/mnt')

    if sys.argv[1:] == ['--exit-service']:
        iface.Exit()
    
    print("example-client terminated successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()

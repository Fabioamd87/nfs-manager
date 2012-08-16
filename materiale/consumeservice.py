#!/usr/bin/env python
 
import dbus
 
bus = dbus.SystemBus()

helloservice = bus.get_object('org.nfsmanager', '/NFSManager') #('busname','objectname')
iface = dbus.Interface(helloservice, dbus_interface='org.nfsmanager')
#hello = helloservice.get_dbus_method('hello', 'org.nfsmanager.actions')
print(iface.hello())
#iface.write()

#writeservice = bus.get_object('org.fabio.services', '/org/fabio/writeservice')
#write = writeservice.get_dbus_method('write', 'org.fabio.writeservice')
#write('test')

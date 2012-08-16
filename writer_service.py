import dbus
import dbus.service
import dbus.mainloop.glib

class Writer(dbus.service.Object):
    def __init__(self, conn=None, object_path=None, bus_name=None):
        dbus.service.Object.__init__(self,conn,object_path,bus_name)
        
        # the following variables are used by _check_polkit_privilege
        self.dbus_info = None
        self.polkit = None
        self.enforce_polkit = True

import dbus, avahi, gobject
import dbus.service
from dbus.mainloop.qt import DBusQtMainLoop
DBusQtMainLoop( set_as_default = True )

from data import NfsMountShare

class nfs_browser( dbus.service.Object ):
    def __init__( self, client ):

        self.client = client

        # prepare avahi
        self.bus = dbus.SystemBus()
        self.server = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, '/' ), 'org.freedesktop.Avahi.Server' )

        # nfs3 scanning
        self.sbrowser = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, self.server.ServiceBrowserNew( avahi.IF_UNSPEC, avahi.PROTO_INET, "_nfs._tcp", 'local', dbus.UInt32( 0 ) ) ), avahi.DBUS_INTERFACE_SERVICE_BROWSER )
        self.sbrowser.connect_to_signal( "ItemNew", self.newItem )
        #self.sbrowser.connect_to_signal( "ItemRemove", self.removeItem ) serve??

        # nfs4 scanning
        self.s4browser = dbus.Interface( self.bus.get_object( avahi.DBUS_NAME, self.server.ServiceBrowserNew( avahi.IF_UNSPEC, avahi.PROTO_INET, "_nfs4._tcp", 'local', dbus.UInt32( 0 ) ) ), avahi.DBUS_INTERFACE_SERVICE_BROWSER )
        self.s4browser.connect_to_signal( "ItemNew", self.newItem )
        #self.s4browser.connect_to_signal( "ItemRemove", self.removeItem ) serve??

    def newItem( self, interface, protocol, name, stype, domain, flags ):
        args = self.server.ResolveService( interface, protocol, name, stype, domain, avahi.PROTO_INET, dbus.UInt32( 0 ) )
        #this line gave me DBusException: org.freedesktop.Avahi.TimeoutError: Timeout reached
        txt = ''
        for i in args[9][0]:
            txt = "%s%s" % ( txt, i )

        if( stype == "_nfs4._tcp" ):
            version = "4"
        else:
            version = "3"

        name = str( name )
        host = str( args[5] )
        address = str( args[7] )
        port = str( args[8] )
        path = txt[5:]
        
        print('trovata partizione montabile')
        
        data = NfsMountShare(host, address,path,'/media/nfs/')
        
        self.client.add_line('mountline', data)

class mounter( dbus.service.Object ):
    def __init__(self):
        self.bus = dbus.SystemBus()
        proxy = self.bus.get_object("org.freedesktop.UDisks.Device", "/org/freedesktop/UDisks")
        iface = dbus.Interface(proxy, 'org.freedesktop.UDisks.Device')

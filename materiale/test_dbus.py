import dbus

def long2ip (l):    
    """
    from python-iptools,
    Convert a network byte order 32-bit integer to a dotted quad ip address.
    """
    MAX_IP = 0xffffffff
    MIN_IP = 0x0
    
    if MAX_IP < l or l < 0:
        raise TypeError("expected int between 0 and %d inclusive" % MAX_IP)
    a = l>>24 & 255
    b = l>>16 & 255
    c = l>>8 & 255
    d = l & 255

    ip = str(d)+'.'+str(c)+'.'+str(b)+'.'+str(a)

    return ip

bus = dbus.SystemBus()
proxy = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
iface = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager')
devices = iface.GetDevices()

for dev in devices:
    proxy = bus.get_object('org.freedesktop.NetworkManager', dev)
    iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
    longip = iface.Get('org.freedesktop.NetworkManager.Device','Ip4Address')
    status = iface.Get('org.freedesktop.NetworkManager.Device','State')
    if status == 100:
        print(long2ip(longip))

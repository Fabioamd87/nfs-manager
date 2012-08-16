import dbus
bus = dbus.SystemBus()
proxy = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
iface = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager')
print(iface.GetDevices())

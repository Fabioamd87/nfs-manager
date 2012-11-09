import os
import subprocess
import dbus

from xml.parsers.expat import ExpatError
from xml.dom import minidom

#from data import NfsMountShare

def CheckStatus(address):
    try:
        pingable = subprocess.check_call(["ping","-c1",address])
        return True
    except subprocess.CalledProcessError:
        print(pingable.returncode) #dovrebbe ritornare l'errore
        return False

def RemoveFromExports(share):
    bus = dbus.SystemBus()
    remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
    iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
    if iface.RemoveShare(share):
        print('removed ' +share+ ' from /etc/exmports')
        return True
    else:
        return False

def RemoveAvahiFile(target):
    files = os.listdir('/etc/avahi/services')
    for f in files:
        print('opening', f)
        try:
            try:
                Doc = minidom.parse('/etc/avahi/services/'+f)
                Element = Doc.getElementsByTagName('txt-record')
                if Element:            
                    share = Element[0].firstChild.data
                    share = share.split('=')
                    share = share[1]
                    if share == target:
                        print('founded shares in avahi files')
                        bus = dbus.SystemBus()
                        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
                        iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
                        if iface.RemoveAvahiFile(f):
                            print('removed '+share+ ' from avahi file')
                            return True
                        else:
                            return False
            except IOError:
                print('skip directories')        
        except ExpatError:
            print('file bad formatted')


def GetData(data):
    print('reading data...')
    data = str(data)
    splitted = data.split(' ')
    address_and_path = splitted[0].split(':')
    
    address = address_and_path[0]
    path = address_and_path[1]
    mountpoint = splitted[2]
    result = NfsMountShare(None, address, path, mountpoint)

    return result

def GetIP():
    bus = dbus.SystemBus()
    proxy = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
    iface = dbus.Interface(proxy, dbus_interface='org.freedesktop.NetworkManager')
    devices = iface.GetDevices()

    result = []

    for dev in devices:
        proxy = bus.get_object('org.freedesktop.NetworkManager', dev)
        iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
        longip = iface.Get('org.freedesktop.NetworkManager.Device','Ip4Address')
        status = iface.Get('org.freedesktop.NetworkManager.Device','State')
        if status == 100:
            ip = (long2ip(longip))
            result.append(ip)
        return result
    

def ReadShared():
    f = open("/etc/exports","r")
    for line in f:
        line = line.split(' ')
        result = []
        if line[0][0] == '#':
            pass    
        else:
            share = line[0]
            ip_and_opt = line[1].split('(')
            ip_and_mask = ip_and_opt[0]
            ip_and_mask = ip_and_mask.split('/')
            ip = ip_and_mask[0]
            mask = ip_and_mask[1]
            opt = ip_and_opt[1]
            opt = opt.strip(')')
            opt = opt.split(',')
            data = [share, ip, mask, opt]
            result.append(data)
    f.close()
    return result

def CheckIp(address):
    print('check if IP is well formed...')
    n = address.split('.')
    if len(n) is not 4:
        return False
    for i in n:
        i = int(i)
        if (i < 1):
            print('<1')
            return False
        if (i > 255):
            print('>255')
            return False
    return True

def CheckAlreadyMounted(address, path):
        
        mounts = ListMountPoints()
        if address+':'+path in mounts:
            return True
        else:
            return False

def ListMountPoints():
    
    l = subprocess.check_output(['mount'])
    l = l.split()

    n=0
    result = ['']
    for element in l:
        result.append(l[n])
        n=n+6
        if (n >= len(l)):
            break
    return result

def CaptureMountedNfs():
    """questa funzione ritorna una tupla con tutte le partizioni nfs gia' montate
    funziona anche se tra le partizioni montate cen'e' una con gli spazi"""
        
    l = subprocess.check_output(['mount'])
    mount_rows = l.split(b'\n')
    mount_rows.pop(len(mount_rows)-1) #rimuovo l'ultimo elemento, (lista vuota)
    l = l.split()

    single_element=[]
    list_fstab=[]
    nfs_row=[]
    
    n = len(mount_rows)
    for row in mount_rows:
        #sbagliato dividere per spazio nel caso una cartella contiene spazi
        str_row = str(row,'utf-8') #il for fa diventare row tipo byte
        single_line = str_row.split(' ')
        typepos = single_line.index('type')
        
        if single_line[typepos+1] == 'nfs' or single_line[typepos+1] == 'nfs4':
            nfs_row.append(str_row)
    return nfs_row
    
def CalculateNetaddress(address, netmask):
    address = address.split('.')
    netmask = netmask.split('.')

    binaddress = []
    for a in address:
        x = int(a)
        b = bin(x)
        print(b)
        x = str(b)
        x = x[2:]
        print(len(x))
        if len(x) <8:
            print('minore di 8')
            x = x.zfill(8) #string
            print(x) 
            x = int(x)
            print(x)
            x = bin(x)
            binaddress.append(x[2:])
        else:
            binaddress.append(b[2:])
    print(binaddress)

import subprocess

from data import NfsMountShare

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

def ListMountPoints(self):
    
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
        str_row = str(row) #il for fa diventare row tipo byte    
        single_line = str_row.split(' ')
        typepos = single_line.index('type')
        
        if single_line[typepos+1] == 'nfs' or single_line[typepos+1] == 'nfs4':
            nfs_row.append(row)
        
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

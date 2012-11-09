import os, sys
import dbus
import subprocess

import PyQt4
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL, pyqtSignal, QFile, QRect

from nfsmanager import Functions

class Client(QtGui.QWidget):

    def __init__(self, config, win_parent = None):
        QtGui.QWidget.__init__(self, win_parent)

        self.config = config
        self.paths_mounted = [] #Already mounted paths
        
        self.vbox = QtGui.QVBoxLayout()

        description = QtGui.QLabel("Aggiungi una mountline e inserisci, nell'ordine, indirizzo sorgente e desinazione")
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(description)
        self.vbox.addLayout(self.hbox)
        
        if os.name == 'posix':
            self.add_mounted()
            
        self.setLayout(self.vbox)
    
    def add_line(self, mount_type='mountline', data=None):
    
        if data:
            if data.path in self.paths_mounted:
                print('already mounted')
                return
            if data.address == self.config.get_address():
                print('not showing our share')
                return
            self.paths_mounted.append(data.path)
        else:
            print('adding line with no data')

        line=MountLine(data)

        if mount_type is 'mountline':
            
            if self.config.get_host_mode == 'hostname': #default visualize ip
                line.set_address(data.host)
            line.view.umount_button.setDisabled(True)

        if mount_type is 'umountline':

            line.view.mount_button.setDisabled(True)
            line.view.select_button.setDisabled(True)
        
        self.vbox.addLayout(line.view)

    def add_mounted(self):
        nfs_share = Functions.CaptureMountedNfs()
        n = len(nfs_share)
        if n>0:
            for i in range(n):
                data = Functions.GetData(nfs_share[i])
                self.add_line('umountline', data)

class Server(QtGui.QWidget):
    def __init__(self, config, win_parent = None):
        QtGui.QWidget.__init__(self, win_parent)
        
        self.config = config
        self.filename = 'share-0.service' #variabile usata per condividere
        self.description = QtGui.QLabel("Seleziona le cartelle da condividere, di default verra' condivisa sull'intera rete.")
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)
        self.vbox.addWidget(self.description)
        shareline = ShareLine(None, True, True, False)
        shareline.shareSignal.connect(self.read_and_share)
        shareline.removeSignal.connect(self.read_and_remove)
        self.vbox.addLayout(shareline)
        self.read_exports()

    def read_exports(self):
        
        shares = Functions.ReadShared()
        for share in shares:
            shareline = ShareLine(share, False, False, True)
            shareline.removeSignal.connect(self.read_and_remove)
            self.vbox.addLayout(shareline)

    def read_and_share(self, data):
        sharepath = data.sharepath
        if sharepath == '':
            print('empty share')
            return
        if not sharepath[0] == '/':
            print('share must start with /')
            return
        if not os.path.isdir(sharepath):
            print("directory doesn't exist")
            return
        if not self.write_in_exports(sharepath):
            return
        self.create_avahi_file(sharepath)
        data.shareline.select_button.setDisabled(True)
        data.shareline.share_button.setDisabled(True)
        data.shareline.remove_button.setDisabled(False)
        shareline = ShareLine(None, True, True, False)
        shareline.shareSignal.connect(self.read_and_share)
        shareline.removeSignal.connect(self.read_and_remove)
        self.vbox.addLayout(shareline)

    def read_and_remove(self, data):
        print('received remove signal')
        sharepath = data.sharepath #non mi piace molto
        if not RemoveFromExports(sharepath):
            return
        if not RemoveAvahiFile(sharepath):
            print("can't find .service file in avahi folder")
            return
        data.shareline.destroy()

    def write_in_exports(self, share):
        netaddress = self.config.get_netaddress()
        line = share + ' ' + netaddress + '/255.255.255.0(rw,no_subtree_check,insecure) \n' #make customizable

        #controllo se gia e' condiviso share
        f = open("/etc/exports","r")
        for l in f:
            l = l.split(' ')
            if l[0]==share:
                print('already shared')
                f.close()
                return
        f.close()
        
        bus = dbus.SystemBus()
        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
        iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
        if iface.AddShare(line):
            print('added', share,'in /etc/exports')
            return True
        else:
            return False

    def create_avahi_file(self, share):
        n=0
        services_filename = os.listdir('/etc/avahi/services')
        while self.filename in services_filename:
            self.filename = self.filename[0:6]+str(n)+'.service' #increase share number
            n+=1
    
        bus = dbus.SystemBus()
        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
        iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
        iface.CreateAvahiFile(self.filename, share)

        print('created', self.filename, 'avahi file in /etc/avahi/services/')
        return True

class Preferences(QtGui.QWidget):
    def __init__(self, config, win_parent = None):
        QtGui.QWidget.__init__(self, win_parent)

        self.config = config
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)

        self.hbox1 = QtGui.QHBoxLayout()
        self.address_label = QtGui.QLabel('inserisci il tuo indirizzo')
        self.address = QtGui.QLineEdit()
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        sizePolicy.setHeightForWidth(self.address.sizePolicy().hasHeightForWidth())
        self.address.setSizePolicy(sizePolicy)
        self.hbox1.addWidget(self.address_label)
        self.hbox1.addWidget(self.address)

        self.hbox2 = QtGui.QHBoxLayout()
        self.netmask_label = QtGui.QLabel('inserisci la netmask')
        self.netmask = QtGui.QLineEdit()
        sizePolicy.setHeightForWidth(self.netmask.sizePolicy().hasHeightForWidth())
        self.netmask.setSizePolicy(sizePolicy)
        self.hbox2.addWidget(self.netmask_label)
        self.hbox2.addWidget(self.netmask)
        
        self.hbox3 = QtGui.QHBoxLayout()
        self.netaddress_label = QtGui.QLabel("inserisci l'indirizzo di rete")
        self.netaddress = QtGui.QLineEdit()
        sizePolicy.setHeightForWidth(self.netaddress.sizePolicy().hasHeightForWidth())
        self.netaddress.setSizePolicy(sizePolicy)
        self.hbox3.addWidget(self.netaddress_label)
        self.hbox3.addWidget(self.netaddress)

        self.hbox4 = QtGui.QHBoxLayout()
        self.de_auth_label = QtGui.QLabel('metodo di autenticazione? (gksu/kdesudo)')
        self.de_auth = QtGui.QLineEdit()
        sizePolicy.setHeightForWidth(self.de_auth.sizePolicy().hasHeightForWidth())
        self.de_auth.setSizePolicy(sizePolicy)
        self.hbox4.addWidget(self.de_auth_label)
        self.hbox4.addWidget(self.de_auth)

        self.hbox5 = QtGui.QHBoxLayout()
        self.host_mode_label = QtGui.QLabel('cosa mostrare? (ip/hostname)')
        self.host_mode = QtGui.QLineEdit()
        sizePolicy.setHeightForWidth(self.host_mode.sizePolicy().hasHeightForWidth())
        self.host_mode.setSizePolicy(sizePolicy)
        self.hbox5.addWidget(self.host_mode_label)
        self.hbox5.addWidget(self.host_mode)


        self.hbox6 = QtGui.QHBoxLayout()
        self.empty_label = QtGui.QLabel()
        self.save_button = QtGui.QPushButton('salva')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.save_button.sizePolicy().hasHeightForWidth())
        self.save_button.setSizePolicy(sizePolicy)
        self.hbox6.addWidget(self.empty_label)
        self.hbox6.addWidget(self.save_button)

        QObject.connect(self.save_button,
            SIGNAL("clicked()"),
            self.save)

        self.vbox.addLayout(self.hbox1)
        self.vbox.addLayout(self.hbox2)
        self.vbox.addLayout(self.hbox3)
        self.vbox.addLayout(self.hbox4)
        self.vbox.addLayout(self.hbox5)
        self.vbox.addLayout(self.hbox6)
        self.load()

    def load(self):
        self.address.setText(self.config.get_address())
        self.netmask.setText(self.config.get_netmask())
        self.netaddress.setText(self.config.get_netaddress())
        self.de_auth.setText(self.config.get_de_auth())
        self.host_mode.setText(self.config.get_host_mode())#combobox o come si chiama lui

    def save(self):
        address = str(self.address.text())
        self.config.set_address(address)

        de_auth = str(self.de_auth.text())
        self.config.set_de_auth(de_auth)

        host_mode = str(self.host_mode.text())
        self.config.set_host_mode(host_mode)

class MountLine(QObject):
    def __init__(self, data=None):        
        QObject.__init__(self)
        
        self.view = MountLineWidget()

        if data:
            self.host = data.host
            self.address = data.address
            self.path = data.path
            self.mountpoint = data.mountpoint
            self.view.fill_widgets(self.address, self.path, self.mountpoint)

        QObject.connect(self.view.mount_button,
            SIGNAL("clicked()"),
            self.read_and_mount)
        
        QObject.connect(self.view.umount_button,
            SIGNAL("clicked()"),
            lambda:self.read_and_umount())

    def set_address(self, address):
        self.address = address
        self.view.address_label.setText(address)
        
    def read_and_mount(self):
        self.address = self.view.get_address()
        self.path = self.view.get_path()
        self.mountpoint = self.view.get_mountpoint()
        
        if self.address=='':
            return
        if self.path=='':
            return
        if self.mountpoint=='':
            return

        #mount, unire le funzioni?
        if self.mount(self.address, self.path, self.mountpoint):
            self.view.set_umountable()

    def mount(self, address, path, mountpoint):
        
        #controllare che address sia un ip
        if not Functions.CheckIp(address):
            print('address not an ip!')
            return

        active = Functions.CheckStatus(address)
        mounted = Functions.CheckAlreadyMounted(address,path)
        
        if not active:
            print('not active!')
            return

        if mounted:
            print('already mounted!')
            return

        bus = dbus.SystemBus()
        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
        iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
        return iface.Mount(address, path, mountpoint)
            
    def read_and_umount(self):

        self.address = self.view.get_address()
        self.path = self.view.get_path()
        self.mountpoint = self.view.get_mountpoint()
        
        if self.umount(self.mountpoint):
            self.view.set_mountable()
    
    def umount(self, mountpoint):

        bus = dbus.SystemBus()
        remote_object = bus.get_object("org.nfsmanager", "/NFSManager")
        iface = dbus.Interface(remote_object, "org.nfsmanager.Interface")
        return iface.Umount(mountpoint)

class ShareObject(object):
    def __init__(self, shareline, share):
        self.shareline = shareline
        self.sharepath = share

class ShareLine(QtGui.QHBoxLayout):

    shareSignal = pyqtSignal(ShareObject)
    removeSignal = pyqtSignal(ShareObject)

    def __init__(self, data = None, select= True, share= True, remove= True):
        QtGui.QHBoxLayout.__init__(self)
        super(ShareLine, self).__init__(None)

        self.path_label = QtGui.QLineEdit() #must end with /
        if data:
            self.path_label.setText(data[0])
        self.select_button = QtGui.QPushButton("Scegli")
        if not select:
            self.select_button.setDisabled(True)
        self.share_button = QtGui.QPushButton("Condividi")
        if not share:
            self.share_button.setDisabled(True)
        self.remove_button = QtGui.QPushButton("Rimuovi")
        if not remove:
            self.remove_button.setDisabled(True)
        self.preference_button = QtGui.QPushButton("Proprietà")

        self.addWidget(self.path_label)
        self.addWidget(self.select_button)
        self.addWidget(self.share_button)
        self.addWidget(self.remove_button)
        self.addWidget(self.preference_button)

        QObject.connect(self.share_button,
            SIGNAL("clicked()"),
            self.on_share_clicked)

        QObject.connect(self.select_button
            ,SIGNAL("clicked()")
            ,self.on_select_clicked)

        QObject.connect(self.remove_button
            ,SIGNAL("clicked()")
            ,self.on_remove_clicked)

    def on_share_clicked(self):
        #legge al volo ed emette
        sharepath = self.path_label.text() 
        sharepath = str(sharepath)
        data = ShareObject(self, sharepath)
        self.shareSignal.emit(data)

    def on_select_clicked(self):
        path = QtGui.QFileDialog.getExistingDirectory()
        self.path_label.setText(path)
    
    def on_remove_clicked(self):
        sharepath = self.path_label.text()
        sharepath = str(sharepath)
        data = ShareObject(self, sharepath)
        self.removeSignal.emit(data)

    def destroy(self):        
        self.path_label.deleteLater()
        self.select_button.deleteLater()
        self.share_button.deleteLater()
        self.remove_button.deleteLater()
        self.deleteLater()

class MountLineWidget(QtGui.QHBoxLayout):    
    def __init__(self):
        QtGui.QHBoxLayout.__init__(self)
        
        self.address_label = QtGui.QLineEdit()
        self.path_label = QtGui.QLineEdit()
        self.mountpoint_label = QtGui.QLineEdit()
        self.select_button = QtGui.QPushButton("Scegli")
        self.mount_button = QtGui.QPushButton("Monta")
        self.umount_button = QtGui.QPushButton("Smonta")
        self.addWidget(self.address_label)
        self.addWidget(self.path_label)
        self.addWidget(self.mountpoint_label)
        self.addWidget(self.select_button)
        self.addWidget(self.mount_button)
        self.addWidget(self.umount_button)

        QObject.connect(self.select_button
            ,SIGNAL("clicked()")
            ,self.on_select_clicked)

    def on_select_clicked(self):
        mountpoint = QtGui.QFileDialog.getExistingDirectory()
        self.mountpoint_label.setText(mountpoint)

    def fill_widgets(self, address, path, mountpoint):
        self.address_label.setText(address)
        self.path_label.setText(path)
        self.mountpoint_label.setText(mountpoint)

    def destroy(self):        
        self.address_label.deleteLater()
        self.path_label.deleteLater()
        self.mountpoint_label.deleteLater()
        self.mount_button.deleteLater()
        self.umount_button.deleteLater()
        self.deleteLater()

    def empty_widgets(self):        
        self.address_label.setText('')
        self.path_label.setText('')
        self.mountpoint_label.setText('')

    def set_mountable(self):
        self.umount_button.setDisabled(True)
        self.mount_button.setDisabled(False)        

    def set_umountable(self):
        self.umount_button.setDisabled(False)
        self.mount_button.setDisabled(True)

    def get_address(self):
        address = self.address_label.text()
        address = str(address)
        return address
    
    def get_path(self):
        path = self.path_label.text()
        path = str(path)
        return path

    def get_mountpoint(self):
        mountpoint = self.mountpoint_label.text()
        mountpoint = str(mountpoint)
        return mountpoint

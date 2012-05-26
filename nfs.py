#!/usr/bin/env python

import os
import sys
import subprocess

import PyQt4
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL, pyqtSignal, QFile, QRect

from functions import get_data, is_ip, capture_mounted_nfs
from data import NfsMountShare
from gui import ShareLine, MountLineWidget
from preferences import Config
from browser import nfs_browser, mounter

class Client(QtGui.QWidget):

    def __init__(self, config, win_parent = None):
        QtGui.QWidget.__init__(self, win_parent)

        self.config = config
        self.paths_mounted = [] #Already mounted paths
        
        self.vbox = QtGui.QVBoxLayout()

        self.add_line_button = QtGui.QPushButton('add line')

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self.add_line_button.sizePolicy().hasHeightForWidth())
        self.add_line_button.setSizePolicy(sizePolicy)

        self.vbox.addWidget(self.add_line_button)

        QObject.connect(self.add_line_button,
            SIGNAL("clicked()"),
            lambda: self.add_line('mountline'))

        description = QtGui.QLabel("Inserisci, nell'ordine, indirizzo sorgente e desinazione")
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(description)
        self.vbox.addLayout(self.hbox)

        self.add_line('mountline')
        self.add_mounted()
        self.setLayout(self.vbox)
    
    def add_line(self, mount_type, data=None):
    
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

        if mount_type is 'mountline':
            line=MountLine(data)
            if self.config.get_host_mode == 'hostname': #default visualize ip
                line.set_address(data.host)
            line.view.umount_button.setDisabled(True)
            self.vbox.addLayout(line.view)

        if mount_type is 'umountline':
            line=MountLine(data)
            line.view.mount_button.setDisabled(True)
            line.view.select_button.setDisabled(True)
            self.vbox.addLayout(line.view)

    def add_mounted(self):
        nfs_share = capture_mounted_nfs()
        n = len(nfs_share)
        if n>0:
            for i in range(n):
                data = get_data(nfs_share[i])
                self.add_line('umountline', data)

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

class Server(QtGui.QWidget):
    def __init__(self, config, win_parent = None):
        QtGui.QWidget.__init__(self, win_parent)
        self.read_avahi_services_filename()
        self.filename = 'share-0.service'
        self.config = config       
        self.description = QtGui.QLabel("Seleziona le cartelle da condividere, di default verra' condivisa sull'intera rete.")
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)
        self.vbox.addWidget(self.description)
        self.add_line()
        self.read_exports()

    def add_line(self, share = None):
        shareline = ShareLine(share)       
        shareline.shareSignal.connect(self.read_and_share)
        self.vbox.addLayout(shareline)

    def read_and_share(self, data):
        share = data.share #non mi piace molto
        if not self.write_exports(share):
            return
        self.create_avahi_file(share)
        self.add_line()

    def read_exports(self):
        f = open("/etc/exports","r")
        for l in f:
            l = l.split(' ')
            if l[0][0] == '#':
                pass
            else:
                self.add_line(l[0])
        f.close()

    def write_exports(self, share):
        netaddress = self.config.get_netaddress()
        line = share + ' ' + netaddress + '/255.255.255.0(rw,no_subtree_check,insecure) \n' #make customizable

        #controllo se gia e condiviso share
        f = open("/etc/exports","r")
        for l in f:
            l = l.split(' ')
            if l[0]==share:
                print('already shared')
                f.close()
                return
        f.close()
        #scrivo su file        
        f = open("/etc/exports","a")
        
        #try:
        f.write(line)
        f.close()
        print('shared:',share)
        return True
        #except:
        #    print('cannot share this folder, maybe you need to be root...')

    def create_avahi_file(self, share):
        n=0
        while self.filename in self.services_filename:
            self.filename = self.filename[0:6]+str(n)+'.service'
            n+=1
        f = open("/etc/avahi/services/"+self.filename,"a")         
        f.write('<?xml version="1.0" standalone="no"?> \n')
        f.write('<!DOCTYPE service-group SYSTEM "avahi-service.dtd"> \n')
        f.write('<service-group> \n')
        f.write('  <name>Zephyrus Shared Music</name> \n')
        f.write('  <service> \n')
        f.write('    <type>_nfs._tcp</type> \n')
        f.write('    <port>2049</port> \n')
        f.write('    <txt-record>path='+share+'</txt-record> \n')
        f.write('  </service> \n')
        f.write('</service-group>')
        f.close()
        print('created', self.filename, 'avahi file')
        self.read_avahi_services_filename()

    def read_avahi_services_filename(self):
        self.services_filename = os.listdir('/etc/avahi/services')

class MountLine(QObject):
    def __init__(self, data=None):        
        QObject.__init__(self)
        
        self.view = MountLineWidget()
        self.config = Config()
        self.authcommand = self.config.get_de_auth()

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
        
        print(self.mountpoint)
        if self.address=='':
            return
        if self.path=='':
            return
        if self.mountpoint=='':
            return

        #mount    
        if self.mount(self.address, self.path, self.mountpoint):
            self.view.set_umountable()

    def mount(self, address, path, mountpoint):
        
        #controllare che address sia un ip
        if not is_ip(address):
            print('address not an ip')
            return

        active = self.check_status(address)
        mounted = self.check_already_mounted(address,path)
        
        if not active:
            print('not active')
            return

        if mounted:
            print('already mounted')
            return
        cmdline = self.authcommand + ' mount ' + address + ':' + path + ' ' + mountpoint
        print(cmdline)
        try:
            print(subprocess.check_output([self.authcommand,' mount ' , address + ':' + path , mountpoint]))
            print('mounted')
            return True
        except:
            print('not mounted')
            return False
            
    def check_status(self,address):
        
        try:
            pingable = subprocess.check_call(["ping","-c1",address])
            return True
        except subprocess.CalledProcessError:
            print(pingable.returncode) #dovrebbe ritornare l'errore
            return False
            
    def check_already_mounted(self, address, path):
        
        mounts = self.list_mount_points()
        if address+':'+path in mounts:
            return True
        else:
            return False

    def list_mount_points(self):
        
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

    def read_and_umount(self):

        self.address = self.view.get_address()
        self.path = self.view.get_path()
        self.mountpoint = self.view.get_mountpoint()
        
        if self.umount(self.mountpoint):
            self.view.set_mountable()
    
    def umount(self,mp):

        try:
            result = subprocess.check_output([self.authcommand,'umount ',mp])
            print('umounted')
            return True
        except:
            print('error umounting')
            return False
    
def main():
    app = QtGui.QApplication(sys.argv)

    config = Config()
    client = Client(config)
    server = Server(config)
    preferences = Preferences(config)
    
    mount_tab = QtGui.QTabWidget()    
    mount_tab.setWindowTitle('NFS Mounter')
    mount_tab.addTab(client, 'Mount')
    mount_tab.addTab(server, 'Manage')
    mount_tab.addTab(preferences, 'Preferences')
    nfs = nfs_browser(client)
    main_window = QtGui.QMainWindow()
    main_window.setCentralWidget(mount_tab)
    main_window.show()
    app.exec_()
    
main()

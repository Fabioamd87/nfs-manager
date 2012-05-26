#!/usr/bin/env python

import PyQt4
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL, pyqtSignal, QFile, QRect

class ShareObject(object):
    def __init__(self, share):
        self.share = share

    def printMessage(self):
        print(self.share)

class ShareLine(QtGui.QHBoxLayout):

    shareSignal = pyqtSignal(ShareObject)

    def __init__(self, share = None):
        QtGui.QHBoxLayout.__init__(self)
        super(ShareLine, self).__init__(None) #cosa fa?

        self.path_label = QtGui.QLineEdit() #must end with /
        if share:
            self.path_label.setText(share)
        self.select_button = QtGui.QPushButton("Scegli")
        self.share_button = QtGui.QPushButton("Condividi")
        self.remove_button = QtGui.QPushButton("Rimuovi")
        self.addWidget(self.path_label)
        self.addWidget(self.select_button)
        self.addWidget(self.share_button)
        self.addWidget(self.remove_button)

        QObject.connect(self.share_button,
            SIGNAL("clicked()"),
            self.on_share_click)

        QObject.connect(self.select_button
            ,SIGNAL("clicked()")
            ,self.on_select_clicked)

    def on_share_click(self):
        share = self.path_label.text() #legge al volo ed emette
        share = str(share)
        data = ShareObject(share)
        self.shareSignal.emit(data)

    def on_select_clicked(self):
        path = QtGui.QFileDialog.getExistingDirectory()
        self.path_label.setText(path)

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

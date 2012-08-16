#!/usr/bin/env python

import os
import sys
import subprocess

import PyQt4
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL, pyqtSignal

class MountTab(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self, None)
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)
        self.button = QtGui.QPushButton("Hello World")
        self.vbox.addWidget(self.button)
        
def main():

    # Create the QApplication
    app = QtGui.QApplication(sys.argv)
    #create controller
    main_window = MountTab()

    mount_tab = QtGui.QTabWidget()
    mount_tab.addTab(main_window, 'string')

    mount_tab.show()
    #listen nfs share with avahi
    # Enter the main loop
    app.exec_()
    
main()

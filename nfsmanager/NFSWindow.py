import os, sys

from PyQt4.QtGui import QMainWindow, QTabWidget, QSystemTrayIcon, QIcon, qApp
from PyQt4.QtCore import QObject, SIGNAL

from nfsmanager import GUIElement
from nfsmanager.Config import Config
from nfsmanager.Browser import NfsBrowser
from nfsmanager_lib import Ui_MainWindow

class TrayIcon(QSystemTrayIcon):
    """creo la tray aggiungendo un segnale al click"""
    def __init__(self):
        QSystemTrayIcon.__init__(self)

    def clicked(self):
        self.activated(QSystemTrayIcon.Trigger)

class NFSWindow(QMainWindow, Ui_MainWindow):
    """creo una MainGUI modificando il tasto chiudi"""
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        trayicon = QIcon(os.path.join(sys.path[0],'data/tray.png'))
        self.tray = TrayIcon()
        self.tray.setIcon(trayicon)
        self.tray.setParent(self)
        self.tray.setContextMenu(self.menuMenu)
        self.tray.show()

        self.config = Config()
        self.client = GUIElement.Client(self.config)
        if os.name == 'posix':
            self.server = GUIElement.Server(self.config)
        self.preferences = GUIElement.Preferences(self.config)
        
        mount_tab = QTabWidget()    
        mount_tab.setWindowTitle('NFS Mounter')
        mount_tab.addTab(self.client, 'Mount')
        if os.name == 'posix':
            mount_tab.addTab(self.server, 'Share')
        mount_tab.addTab(self.preferences, 'Preferences')

        if os.name == 'posix':
            nfs = NfsBrowser(self.client)
        
        self.setCentralWidget(mount_tab)

        self.actionAdd.connect(self.actionAdd, SIGNAL("triggered()"), self.client.add_line)
        self.tray.connect(self.tray,  SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.on_tray_clicked)
        self.actionExit.connect(self.actionExit, SIGNAL('triggered()'), self.on_actionExit_clicked)

    def on_tray_clicked(self,r):
        if r == 3:
            if self.isActiveWindow():
                self.hide()
            else:                 
                self.show()

    def on_actionAdd_clicked(self):
        pass

    def on_actionExit_clicked(self):
        print('Exiting...')
        qApp.quit()

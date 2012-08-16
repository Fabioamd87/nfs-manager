from nfsmanager import NFSWindow, GUIElement

from PyQt4 import QtCore, QtGui

def main():
    'constructor for your class instances'
    #parse_options()

    # Run the application.
    print('avvio l''applicazione')
    import sys
    app = QtGui.QApplication(sys.argv)

    window = NFSWindow.NFSWindow()
    window.show()

    sys.exit(app.exec_())

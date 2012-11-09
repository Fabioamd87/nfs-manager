import sys

sys.path.append('/usr/share/nfsmanager')
from nfsmanager import NFSWindow

from PyQt4 import QtGui

def main():

    # Run the application.
    print("starting application")
    import sys
    app = QtGui.QApplication(sys.argv)

    window = NFSWindow.NFSWindow()
    window.show()

    sys.exit(app.exec_())

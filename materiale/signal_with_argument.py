import sys
from PyQt4.QtCore import pyqtSignal, QObject

class NativePythonObject(object):
    def __init__(self, message):
        self.message = message

    def printMessage(self):
        print(self.message)
        sys.exit()

class SignalEmitter(QObject):
    theSignal = pyqtSignal(NativePythonObject) #che gli passa? non ci va self? eredita?

    def __init__(self, toBeSent, parent=None):
        super(SignalEmitter, self).__init__(parent) #cosa fa?
        self.toBeSent = toBeSent

    def emitSignal(self):
        self.theSignal.emit(toBeSent) # non ci andrebbe self? altrimenti perche' glielo passa nel costruttore se poi lo prende dal main?

class ClassWithSlot(object):
    def __init__(self, signalEmitter):
        self.signalEmitter = signalEmitter
        self.signalEmitter.theSignal.connect(self.theSlot)

    def theSlot(self, ourNativePythonType): #riceve come argomento l'oggetto e ne invoca un metodo
        ourNativePythonType.printMessage()

if __name__ == "__main__":
    toBeSent = NativePythonObject("Hello World")
    signalEmitter = SignalEmitter(toBeSent)
    classWithSlot = ClassWithSlot(signalEmitter)
    signalEmitter.emitSignal()

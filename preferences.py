import sys
import os.path

if sys.version > '3':
    PY3 = True
else:
    PY3 = False

if PY3:
    import configparser 
else:
    import ConfigParser as configparser #for python2

class Config():
    def __init__(self):
        self.parser = configparser.SafeConfigParser()
        if not os.path.exists("preferences.ini"):
            self.create_config()

    def create_config(self):
        #se il programma viene eseguito in una cartella diversa il file verra creato li, MALE.
        self.parser.add_section('local')
        self.parser.set('local', 'ip', '192.168.1.5')
        self.parser.set('local', 'netmask', '255.255.255.0')
        self.parser.set('local', 'netaddress', '192.168.1.0')
        self.parser.set('local', 'show', 'ip') #or hostname
        self.parser.set('local', 'DE_authentication', 'pkexec') #or kdesudo
        f = open('preferences.ini', 'w')
        self.parser.write(f)
        f.close()

    def write(self):
        f = open('preferences.ini', 'w')
        self.parser.write(f)
        f.close()

    def get_address(self):
        self.parser.read('preferences.ini')
        return self.parser.get('local', 'ip')

    def get_netmask(self):
        self.parser.read('preferences.ini')
        return self.parser.get('local', 'netmask')

    def get_netaddress(self):
        self.parser.read('preferences.ini')
        return self.parser.get('local', 'netaddress')

    def get_de_auth(self):
        self.parser.read('preferences.ini')
        return self.parser.get('local', 'DE_authentication')

    def get_host_mode(self):
        self.parser.read('preferences.ini')
        return self.parser.get('local', 'show')

    def set_address(self, address):
        self.parser.read('preferences.ini')
        self.parser.set('local', 'ip', address)
        self.write()

    def set_mask(self, netmask):
        self.parser.read('preferences.ini')
        self.parser.set('local', 'netmask', netmask)
        self.write()

    def set_netaddress(self, netaddress):
        self.parser.read('preferences.ini')
        self.parser.set('local', 'netaddress', netaddress)
        self.write()

    def set_de_auth(self, de_auth):
        self.parser.read('preferences.ini')
        self.parser.set('local', 'DE_authentication', de_auth)
        self.write()

    def set_host_mode(self, host_mode):
        self.parser.read('preferences.ini')
        self.parser.set('local', 'show', host_mode)
        self.write()

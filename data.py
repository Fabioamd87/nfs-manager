#!/usr/bin/env python

class NfsMountShare(object):
    def __init__( self, host=None, address=None, path=None, mp=None):
        self.host = host
        self.address = address       
        self.path = path        
        self.mountpoint = mp
        #self.name = name
        #self.port = port
        #self.version = version
    
    def show(self):
        print self.host
        print self.address
        print self.path
        print self.mountpoint

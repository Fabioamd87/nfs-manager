#!/usr/bin/python

import pygtk
pygtk.require('2.0')
import gtk

import dbus
import os

class TestWindow:
    def on_button_clicked(self, widget, data=None):

	#Call the D-Bus method to request PolicyKit authorization:

        session_bus = dbus.SessionBus()
        policykit = session_bus.get_object('org.freedesktop.PolicyKit.AuthenticationAgent', '/', "org.gnome.PolicyKit.AuthorizationManager.SingleInstance")
        if(policykit == None):
           print("Error: Could not get PolicyKit D-Bus Interface\n")

        gdkwindow = self.window.window
        xid = gdkwindow.xid

        print("Calling ObtainAuthorization...")

        #This complains that no ObtainAuthorization(ssi) exists:
        #granted = policykit.ObtainAuthorization("test_action_id", xid, os.getpid())

        #TODO: Neither of the async callbacks are called, and how could the return value be useful if it is async?
        # Note: Other code (such as gnome-panel) seems to use ShowDialog instead of ObtainAuthorization, though
        # ShowDialog is apparently deprecated (I don't know when), but that also has no effect.
        granted = policykit.ObtainAuthorization("test_action_id", xid, os.getpid(), reply_handler=self.__handleAuthReply, error_handler=self.__handleAuthError)

        print("...Finished.")

        print("granted=", granted)

    def __handleAuthReply(self, granted):
        print("handleAuthReply: granted\n")

    def __handleAuthError(self, exception):
        print("handleAuthError: not granted: %s\n" % exception)

    def on_delete_event(self, widget, event, data=None):
        # Close the window:
        return False

    def on_destroy(self, widget, data=None):
        gtk.main_quit()

    def show(self):
       self.window.show()

    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.on_delete_event)
        self.window.connect("destroy", self.on_destroy)

        self.button = gtk.Button("Obtain Authorization")
        self.button.connect("clicked", self.on_button_clicked, None)
        self.window.add(self.button)
        self.button.show()

window = TestWindow()
window.show()
gtk.main()

#!/usr/bin/python

# (from jockey)
# (c) 2008 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# (from python-dbus-docs)
# Copyright (C) 2004-2006 Red Hat Inc. <http://www.redhat.com/>
# Copyright (C) 2005-2007 Collabora Ltd. <http://www.collabora.co.uk/>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# This file was modified by David D. Lowe in 2009.
# To the extent possible under law, David D. Lowe has waived all 
# copyright and related or neighboring rights to his modifications to
# this file under this license: http://creativecommons.org/publicdomain/zero/1.0/

"""This file was heavily modified from example-service distributed
with the Debian package: python-dbus-doc, and jockey distributed with
the package: jockey-common
It is an example DBus system service which checks for PolicyKit's
authorisation before responding to any requests"""

from gi.repository import GObject
import os
import time

import dbus
import dbus.service
import dbus.mainloop.glib

class DemoException(dbus.DBusException):
    _dbus_error_name = 'com.example.DemoException'

class PermissionDeniedByPolicy(dbus.DBusException):
    _dbus_error_name = 'com.ubuntu.DeviceDriver.PermissionDeniedByPolicy'

class SomeObject(dbus.service.Object):
    
    def __init__(self, conn=None, object_path=None, bus_name=None):
        dbus.service.Object.__init__(self,conn,object_path,bus_name)
        
        # the following variables are used by _check_polkit_privilege
        self.dbus_info = None
        self.polkit = None
        self.enforce_polkit = True
        
    @dbus.service.method("com.example.SampleInterface",
                         in_signature='s', out_signature='as',
                         sender_keyword='sender', connection_keyword='conn')
    def HelloWorld(self, hello_message, sender=None, conn=None):
        """Print hello_message and log it in /tmp/example-service-log, 
        then return a list"""
        self._check_polkit_privilege(sender, conn, 'com.example.sampleservice.hi')
        print((str(hello_message)))
        SomeObject._log_in_file("/tmp/example-service-log", str(hello_message))
        return ["Hello", " from example-service.py", "with unique name",
                bus.get_unique_name()]

    @dbus.service.method("com.example.SampleInterface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def RaiseException(self, sender=None, conn=None):
        raise DemoException('The RaiseException method does what you might '
                            'expect')

    @dbus.service.method("com.example.SampleInterface",
                         in_signature='', out_signature='(ss)',
                         sender_keyword='sender', connection_keyword='conn')
    def GetTuple(self, sender=None, conn=None):
        return ("Hello Tuple", " from example-service.py")

    @dbus.service.method("com.example.SampleInterface",
                         in_signature='', out_signature='a{ss}',
                         sender_keyword='sender', connection_keyword='conn')
    def GetDict(self, sender=None, conn=None):
        return {"first": "Hello Dict", "second": " from example-service.py"}

    @dbus.service.method("com.example.SampleInterface",
                         in_signature='', out_signature='',
                         sender_keyword='sender', connection_keyword='conn')
    def Exit(self, sender=None, conn=None):
        mainloop.quit()
    
    @classmethod
    def _log_in_file(klass, filename, string):
        date = time.asctime(time.localtime())
        ff = open(filename, "a")
        ff.write("%s : %s\n" %(date,str(string)))
        ff.close()
        

    def _check_polkit_privilege(self, sender, conn, privilege):
        # from jockey
        '''Verify that sender has a given PolicyKit privilege.

        sender is the sender's (private) D-BUS name, such as ":1:42"
        (sender_keyword in @dbus.service.methods). conn is
        the dbus.Connection object (connection_keyword in
        @dbus.service.methods). privilege is the PolicyKit privilege string.

        This method returns if the caller is privileged, and otherwise throws a
        PermissionDeniedByPolicy exception.
        '''
        if sender is None and conn is None:
            # called locally, not through D-BUS
            return
        if not self.enforce_polkit:
            # that happens for testing purposes when running on the session
            # bus, and it does not make sense to restrict operations here
            return

        # get peer PID
        if self.dbus_info is None:
            self.dbus_info = dbus.Interface(conn.get_object('org.freedesktop.DBus',
                '/org/freedesktop/DBus/Bus', False), 'org.freedesktop.DBus')
        pid = self.dbus_info.GetConnectionUnixProcessID(sender)
        
        # query PolicyKit
        if self.polkit is None:
            self.polkit = dbus.Interface(dbus.SystemBus().get_object(
                'org.freedesktop.PolicyKit1',
                '/org/freedesktop/PolicyKit1/Authority', False),
                'org.freedesktop.PolicyKit1.Authority')
        try:
            # we don't need is_challenge return here, since we call with AllowUserInteraction
            (is_auth, _, details) = self.polkit.CheckAuthorization(
                    ('unix-process', {'pid': dbus.UInt32(pid, variant_level=1),
                    'start-time': dbus.UInt64(0, variant_level=1)}), 
                    privilege, {'': ''}, dbus.UInt32(1), '', timeout=600)
        except dbus.DBusException as e:
            if e._dbus_error_name == 'org.freedesktop.DBus.Error.ServiceUnknown':
                # polkitd timed out, connect again
                self.polkit = None
                return self._check_polkit_privilege(sender, conn, privilege)
            else:
                raise

        if not is_auth:
            SomeObject._log_in_file('/tmp/example-service-log','_check_polkit_privilege: sender %s on connection %s pid %i is not authorized for %s: %s' %
                    (sender, conn, pid, privilege, str(details)))
            raise PermissionDeniedByPolicy(privilege)


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    bus = dbus.SystemBus()
    name = dbus.service.BusName("com.example.SampleService", bus)
    object = SomeObject(bus, '/SomeObject')

    mainloop = GObject.MainLoop()
    print("Running example service.")
    mainloop.run()

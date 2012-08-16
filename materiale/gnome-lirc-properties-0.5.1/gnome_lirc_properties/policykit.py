# Infrared Remote Control Properties for GNOME
# Copyright (C) 2008 Fluendo Embedded S.L. (www.fluendo.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
'''
PolicyKit related services.
'''

import dbus, logging, os

from gnome_lirc_properties import config

class PolicyKitAuthentication(object):
    '''
    Obtains sudo/root access,
    asking the user for authentication if necessary,
    using PolicyKit
    '''

    def is_authorized(self, action_id=config.POLICY_KIT_ACTION):
        '''
        Ask PolicyKit whether we are already authorized.
        '''

        if not config.ENABLE_POLICY_KIT:
            return True

        # Check whether the process is authorized:
        pid = os.getpid()
        (is_auth, _, details) = self.policy_kit.CheckAuthorization(
			('unix-process', {'pid': dbus.UInt32(pid, variant_level=1), 'start-time':dbus.UInt64(0,variant_level=1)}),
			action_id, {}, dbus.UInt32(0), '', timeout=600)
        logging.debug('%s: authorized=%r', action_id, is_auth)

        return bool(is_auth)

    def obtain_authorization(self, widget, action_id=config.POLICY_KIT_ACTION):
        '''
        Try to obtain authorization for the specified action.
        '''

        if not config.ENABLE_POLICY_KIT:
            return True

        pid = os.getpid()
        (granted, _, details) = self.policy_kit.CheckAuthorization(
			('unix-process', {'pid': dbus.UInt32(pid, variant_level=1), 'start-time':dbus.UInt64(0,variant_level=1)}),
			action_id, {}, dbus.UInt32(1), '', timeout=600)

        logging.debug('%s: granted=%r', action_id, granted)

        return bool(granted)

    def __get_policy_kit(self):
        '''Retrieve the D-Bus interface of PolicyKit.'''

        # retreiving the interface raises DBusException on error:
        service = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        return dbus.Interface(service, 'org.freedesktop.PolicyKit1.Authority')

    policy_kit = property(__get_policy_kit)

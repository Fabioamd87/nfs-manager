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
User interface related services.
'''

# publish common functions
# pylint: disable-msg=W0401
from gnome_lirc_properties.ui.common                  import *

# publish dialog classes
from gnome_lirc_properties.ui.CustomConfiguration     import CustomConfiguration
from gnome_lirc_properties.ui.ReceiverChooserDialog   import ReceiverChooserDialog
from gnome_lirc_properties.ui.RemoteControlProperties import RemoteControlProperties

# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Copyright (C) 2010 Артём Попов <artfwo@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.

# FIXME:
# org.freedesktop.PolicyKit1 (cheat at distutils-extra)

import gobject
import gtk
import appindicator

import locale
import dbus

from indicator_cpufreq import cpufreq
from indicator_cpufreq.indicator_cpufreqconfig import get_data_file, get_icon_path

import gettext
from gettext import gettext as _
#gettext.textdomain('indicator-cpufreq')

def readable_frequency(f):
    return _("%s GHz") % locale.format(_("%.2f"), f / 1.0e6)

governor_names = {
    'conservative': _("Conservative"),
    'ondemand': _("Ondemand"),
    #'userspace': _("Userspace"),
    'powersave': _("Powersave"),
    'performance': _("Performance"),
}

def readable_governor(g):
    if governor_names.has_key(g):
        return governor_names[g]
    else:
        return g

class MyIndicator(appindicator.Indicator):
    def __init__(self):
        appindicator.Indicator.__init__(self, "indicator-cpufreq",
            "indicator-cpufreq",
            appindicator.CATEGORY_HARDWARE)
        self.set_status(appindicator.STATUS_ACTIVE)
        
        self.set_icon_theme_path("/usr/share/icons")
        #self.set_icon(get_data_file('media', 'indicator-cpufreq.png'))
        self.set_icon('indicator-cpufreq')
        
        menu = gtk.Menu()
        self.select_items = {}
        group = None
        
        maxcpu = 0
        while cpufreq.cpu_exists(maxcpu) == 0:
            maxcpu += 1
        self.cpus = range(maxcpu)
        
        # frequency menu items
        freqs = cpufreq.get_available_frequencies(self.cpus[0])
        for freq in freqs:
            menu_item = gtk.RadioMenuItem(group, readable_frequency(freq))
            if group is None:
                group = menu_item
            menu.append(menu_item)
            menu_item.connect("activate", self.select_activated, 'frequency', freq)
            self.select_items[freq] = menu_item

        menu.append(gtk.SeparatorMenuItem())

        # governor menu items
        governors = cpufreq.get_available_governors(self.cpus[0])
        for governor in governors:
            if governor == 'userspace':
                continue
            menu_item = gtk.RadioMenuItem(group, readable_governor(governor))
            menu.append(menu_item)
            menu_item.connect('activate', self.select_activated, 'governor', governor)
            self.select_items[governor] = menu_item
        
        menu.show_all()
        
        self.set_menu(menu)
        self.update_ui()
        gobject.timeout_add(1500, self.poll_timeout)
    
    def poll_timeout(self):
        self.update_ui()
        return True
    
    def update_ui(self):
        for i in self.select_items.values():
            i.handler_block_by_func(self.select_activated)
        
        fmin, fmax, governor = cpufreq.get_policy(self.cpus[0])
        # use the highest freq among cores for display
        freq = max([cpufreq.get_freq_kernel(cpu) for cpu in self.cpus])
        
        ratio = min([25, 50, 75, 100], key=lambda x: abs(x - (float(freq) / fmax * 100)))
        if freq < fmax and ratio == 100:
            ratio = 75
        
        #self.set_icon(get_data_file('media', 'indicator-cpufreq-%d.png' % ratio))
        self.set_icon('indicator-cpufreq-%d' % ratio)
        
        if governor == 'userspace':
            self.select_items[freq].set_active(True)
        else:
            self.select_items[governor].set_active(True)
        
        for i in self.select_items.values():
            i.handler_unblock_by_func(self.select_activated)
       
        #self.props.label = readable_frequency(freq)
    
    def select_activated(self, menuitem, select, value):
        if menuitem.active:
            bus = dbus.SystemBus()
            proxy = bus.get_object("com.ubuntu.IndicatorCpufreqSelector", "/Selector", introspect=False)
            cpus = [dbus.UInt32(cpu) for cpu in self.cpus]
            if select == 'frequency':
                proxy.SetFrequency(cpus, dbus.UInt32(value),
                    dbus_interface='com.ubuntu.IndicatorCpufreqSelector')
            else:
                proxy.SetGovernor(cpus, value,
                    dbus_interface='com.ubuntu.IndicatorCpufreqSelector')
    
    def can_set(self):
        pass

gobject.type_register(MyIndicator)

if __name__ == "__main__":
    ind = MyIndicator()
    gtk.main()


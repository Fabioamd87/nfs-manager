#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
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
### END LICENSE

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

import os
import sys

try:
    import DistUtilsExtra.auto
except ImportError:
    print >> sys.stderr, 'To build indicator-cpufreq you need https://launchpad.net/python-distutils-extra'
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', 'needs DistUtilsExtra.auto >= 2.18'

def update_data_path(prefix, oldvalue=None):

    try:
        fin = file('indicator_cpufreq/indicator_cpufreqconfig.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__indicator_cpufreq_data_directory__':
                # update to prefix, store oldvalue
                if not oldvalue:
                    oldvalue = fields[1]
                    line = "%s = '%s'\n" % (fields[0], prefix)
                else: # restore oldvalue
                    line = "%s = %s" % (fields[0], oldvalue)
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find indicator_cpufreq/indicator_cpufreqconfig.py")
        sys.exit(1)
    return oldvalue


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        previous_value = update_data_path(self.prefix + '/share/indicator-cpufreq/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_data_path(self.prefix, previous_value)


        
##################################################################################
###################### YOU SHOULD MODIFY ONLY WHAT IS BELOW ######################
##################################################################################

import glob

DistUtilsExtra.auto.setup(
    name='indicator-cpufreq',
    version='0.1.4',
    license='GPL-3',
    author='Артём Попов',
    author_email='artfwo@gmail.com',
    description='CPU frequency scaling indicator',
    long_description='Indicator applet for displaying and changing CPU frequency on-the-fly.',
    url='https://launchpad.net/indicator-cpufreq',
    cmdclass={'install': InstallAndUpdateDataDirectory},
    # FIXME: install icons as data_files until we resolve it with quickly
    data_files=[
        ('share/icons/ubuntu-mono-dark/status/22',
            glob.glob('icons/ubuntu-mono-dark/*')),
        ('share/icons/ubuntu-mono-light/status/22',
            glob.glob('icons/ubuntu-mono-light/*')),
#        ('/var/lib/polkit-1/localauthority/10-vendor.d',
#            ['indicator-cpufreq.pkla']),
    ]
)

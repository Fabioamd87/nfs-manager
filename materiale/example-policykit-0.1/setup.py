#!/usr/bin/env python
# 2009 David D Lowe
# To the extent possible under law, David D. Lowe has waived all copyright and related or neighboring rights to this file.
# License: http://creativecommons.org/publicdomain/zero/1.0/

from distutils.core import setup
from distutils.command.install import install
from distutils.core import Command
import sys

def main():
    
    install.sub_commands.append(('install_dbus_service',None))
        
    setup( name="example-policykit",
    version="0.1", 
    description="Example Python, DBus and PolicyKit code",
    author="David D Lowe",
    license="GPL v2",
    data_files=[('/usr/share/dbus-1/system-services/', ['com.example.SampleService.service']),
                ('/usr/share/polkit-1/actions', ['com.example.sampleservice.policy']),
                ('/etc/dbus-1/system.d/', ['com.example.SampleService.conf'])],
    scripts=['nfs-client.py','nfs-service.py'],
    cmdclass={"install_dbus_service": install_dbus_service})

class install_dbus_service(Command):
    description = "Install DBus .service file, modifying it so that it points to the correct script"
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        install_bin = self.get_finalized_command('install_scripts')
        script_install_dir = install_bin.install_dir
        output = ""
        ff = open("/usr/share/dbus-1/system-services/com.example.SampleService.service","r")
        for line in ff.readlines():
            if line.strip()[:5] == "Exec=":
                line = line.replace("/usr/bin", script_install_dir)
            output += line
        ff.close()
        ff = open("/usr/share/dbus-1/system-services/com.example.SampleService.service","w")
        ff.write(output)
        ff.close()
    

if __name__ == "__main__":
    main()

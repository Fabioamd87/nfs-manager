#!/usr/bin/env python
# 2009 David D Lowe
# To the extent possible under law, David D. Lowe has waived all copyright and related or neighboring rights to this file.
# License: http://creativecommons.org/publicdomain/zero/1.0/

from distutils.core import setup
    
setup(name="nfsmanager",
    version="0.1",
    description="mount NFS directories",
    author="Fabio Sasso",
    license="GPL v2",
    packages = ['nfsmanager'],
    scripts = ['bin/nfsmanager']
)

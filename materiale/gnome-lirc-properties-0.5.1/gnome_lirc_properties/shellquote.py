# Copyright 2005 Lars Wirzenius (liw@iki.fi)
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


"""Quote a word for the Unix sh shell

This module contains the function shellquote, which quotes a string
so that it can be safely passed to the shell as an argument, e.g.,
via os.system or os.popen.

Lars Wirzenius <liw@iki.fi>
"""


import unittest

safechars = ("abcdefghijklmnopqrstuvwxyz" +
             "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
             "0123456789" +
             ",.-_!%/=+:")

def shellquote(str):
    if str == "":
        return "''"

    result = []
    for c in str:
        if c == "'":
            result.append("\"'\"")
        elif c in safechars:
            result.append(c)
        else:
            result.append("\\" + c)
    return "".join(result)


class ShellQuoteTests(unittest.TestCase):

    def testEmpty(self):
        self.failUnlessEqual(shellquote(""), "''")

    def testSimple(self):
        self.failUnlessEqual(shellquote("abc"), "abc")

    def testSpace(self):
        self.failUnlessEqual(shellquote("abc def"), "abc\\ def")

    def testApostrophe(self):
        self.failUnlessEqual(shellquote("abc'def"), "abc\"'\"def")

    def testQuotes(self):
        self.failUnlessEqual(shellquote("abc\"def"), "abc\\\"def")


if __name__ == "__main__":
    unittest.main()

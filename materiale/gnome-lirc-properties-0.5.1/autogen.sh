#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.

PKG_NAME=gnome-lirc-properties
REQUIRED_AUTOMAKE_VERSION=1.10

if ! (test -f "$srcdir/configure.ac" &&
      test -f "$srcdir/bin/gnome-lirc-properties.in" &&
      test -f "$srcdir/data/gnome-lirc-properties.ui" &&
      test -f "$srcdir/data/gnome-lirc-properties.desktop.in.in")
then
 echo "$srcdir doesn't look like source directory for $PKG_NAME" >&2
 exit 1
fi

if [ -f /etc/fedora-release ] ; then
	. gnome-autogen.sh --disable-conf-check --with-lirc-confdir=/etc/lirc/ --with-remotes-database=/usr/share/lirc-remotes/ "$@"
else
	. gnome-autogen.sh "$@"
fi


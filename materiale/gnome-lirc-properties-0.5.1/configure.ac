AC_INIT([gnome-lirc-properties], [0.5.1],
        [http://git.gnome.org/browse/gnome-lirc-properties/])

# tar-ustar asks it to use a sensible tar format that can handle long filenames
AM_INIT_AUTOMAKE([1.9 tar-ustar dist-bzip2 no-dist-gzip])

# Enable silent build when available (Automake 1.11)
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])

dnl check for programs ===

AM_PROG_CC_C_O
AM_PATH_PYTHON(2.5)
IT_PROG_INTLTOOL([0.35.0])

dnl localization support ===

GETTEXT_PACKAGE="$PACKAGE"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE],
                   ["$GETTEXT_PACKAGE"],
                   [The gettext package])
AM_GLIB_GNU_GETTEXT

dnl initialize GNOME help ===

GNOME_DOC_INIT()

dnl check for glib-2.0 for the lirc-generate-linux-input helper
PKG_CHECK_MODULES(GLIB, glib-2.0)

dnl check for PolicyKit ===

AC_ARG_ENABLE([policy-kit],
              [  --disable-policy-kit     don't use PolicyKit for gaining privileges])

if test "$enable_policy_kit" != no
then
  PKG_CHECK_MODULES([POLICY_KIT], [polkit-backend-1])
  ENABLE_POLICY_KIT=True
  enable_policy_kit=yes
else
  ENABLE_POLICY_KIT=False
fi

AC_SUBST([ENABLE_POLICY_KIT])

POLICY_KIT_ACTION="org.gnome.lirc-properties.mechanism.configure"
AC_SUBST([POLICY_KIT_ACTION])

dnl check for new enough lirc ===

AC_PATH_PROG([LIRCD], [lircd])

HAVE_LIRCD="yes"
if test -z $LIRCD ; then
  HAVE_LIRCD="no"
else
  LIRCD_VERSION=`lircd --version|head -n 1|sed 's/^lircd //'|sed 's/ (.*)//'`
  LIRCD_MAJOR=`echo $LIRCD_VERSION | cut -d. -f1 | sed 's/[[a-zA-Z\-]].*//g'`
  LIRCD_MINOR=`echo $LIRCD_VERSION | cut -d. -f2 | sed 's/[[a-zA-Z\-]].*//g'`
  LIRCD_MICRO=`echo $LIRCD_VERSION | cut -d. -f3 | sed 's/[[a-zA-Z\-]].*//g'`
  if [[ "$LIRCD_MAJOR" -eq "0" ]] && \
	  [[ "$LIRCD_MINOR" -lt "8" ]]; then
	  AC_MSG_WARN([lircd >= 0.8.4 is required, you have $LIRCD_VERSION])
	  HAVE_LIRCD="no"
  elif [[ "$LIRCD_MAJOR" -eq "0" ]] && \
	  [[ "$LIRCD_MINOR" -eq "8" ]] && \
	  [[ "$LIRCD_MICRO" -lt "6" ]]; then
	  AC_MSG_WARN([lircd >= 0.8.6 is required, you have $LIRCD_VERSION])
	  HAVE_LIRCD="no"
  fi
fi

AC_MSG_CHECKING([new enough lircd daemon])
if test x"$HAVE_LIRCD" != xyes ;
then
  AC_MSG_ERROR([no])
else
  AC_MSG_RESULT([yes])
fi

dnl support custom LIRC folders ===

expand_vars() {
  value=`test "$prefix" == NONE && prefix="$ac_default_prefix"; eval "echo \"$1\""`
  test "$value" != "$1" && expand_vars "$value" || echo "$value"
}

if test -f /etc/fedora-release ; then
	lirc_confdir="/etc/lirc"
	remotes_database="/usr/share/lirc-remotes"
	lircd_socket="/var/run/lirc/lircd"
	lirc_hardware_conf="/etc/sysconfig/lirc"
	startup_style="fedora"
else
	lirc_confdir="$sysconfdir/lirc"
	remotes_database="$datadir/lirc/remotes"
	lircd_socket="/dev/lircd"
	lirc_hardware_conf="$lirc_confdir/hardware.conf"
	startup_style="debian"
fi

AC_ARG_WITH([lirc_confdir],
            AS_HELP_STRING([--with-lirc-confdir],
                           [Configuration folder of LIRC, e.g. $sysconfdir/lirc]),
            [], [with_lirc_confdir=`expand_vars "$lirc_confdir"`])

AC_ARG_WITH([remotes_database],
            AS_HELP_STRING([--with-remotes-database],
                           [Path of the system's LIRC remote database, e.g. $datadir/lirc/remotes]),
            [], [with_remotes_database=`expand_vars "$remotes_database"`])

AC_ARG_WITH([lircd_socket],
            AS_HELP_STRING([--with-lircd-socket],
                           [Path of the system's LIRCD socket, e.g. /dev/lircd]),
            [], [with_lircd_socket=`expand_vars "$lircd_socket"`])

AC_ARG_WITH([lirc_conf],
            AS_HELP_STRING([--with-lirc-conf],
			   [Path of the system's lirc configuration file, e.g. /etc/lirc/hardware.conf]),
            [], [with_lirc_hardware_conf=`expand_vars "$lirc_hardware_conf"`])

AC_ARG_WITH([startup_style],
            AS_HELP_STRING([--with-startup-style],
			   [Whether to use Fedora or Debian style startup (either debian, or fedora)]),
            [], [with_startup_style=`expand_vars "$startup_style"`])

if test x$with_startup_style != xfedora -a x$startup_style != xdebian ; then
	AC_MSG_ERROR([Startup style must be one of debian or fedora])
fi

AC_SUBST([with_lirc_confdir])
AC_SUBST([with_remotes_database])
AC_SUBST([with_lircd_socket])
AC_SUBST([with_lirc_hardware_conf])
AC_SUBST([with_startup_style])

AC_MSG_CHECKING([configured LIRC configuration folder])

AC_ARG_ENABLE([confdir-check],
              AS_HELP_STRING([--disable-confdir-check],
                             [don't check for the lircd.conf path])])

if test "x$enable_confdir_check" = xyes
  then if test -f "$with_lirc_confdir/lircd.conf"
    then
      AC_MSG_RESULT([$with_lirc_confdir])
    else
      AC_MSG_RESULT([no])
      if test ! -f /etc/fedora-release ; then
        AC_MSG_ERROR([Cannot find lircd.conf in $with_lirc_confdir.])
      fi
    fi
  else
    AC_MSG_RESULT([$with_lirc_confdir])
fi

AC_MSG_CHECKING([configured LIRC remotes database])

if test -d "$with_remotes_database"
then
  AC_MSG_RESULT([$with_remotes_database])
else
  AC_MSG_RESULT([no])
  AC_MSG_ERROR([Configured remotes database does not exist: $with_remotes_database])
fi

AC_MSG_CHECKING([configured LIRCD socket])
AC_MSG_RESULT([$with_lircd_socket])

dnl find irrecord ===

AC_PATH_PROG([LIRC_IRRECORD], [irrecord])
AC_ARG_VAR([LIRC_IRRECORD], [path of the irrecord program])
AC_SUBST([LIRC_IRRECORD])

dnl find name of input device layer driver

AC_ARG_WITH([devinput_driver],
            AS_HELP_STRING([--with-devinput-driver],
                           [The name of the Linux Input Device driver.]),
            [], [devinput_driver="`lircd --driver=help 2>&1 | sed -ne 's:^\s*\(dev/\?input\)\s*$:\1:p'`"])

AC_SUBST([devinput_driver])

dnl generate files ===

AC_CONFIG_FILES([Makefile
                 bin/Makefile
                 data/Makefile
                 data/gnome-lirc-properties.desktop.in
                 data/org.gnome.lirc-properties.mechanism.policy
                 data/org.gnome.LircProperties.Mechanism.service
                 data/icons/Makefile
                 data/icons/16x16/Makefile
                 data/icons/22x22/Makefile
                 data/icons/24x24/Makefile
                 data/icons/scalable/Makefile
                 gnome_lirc_properties/Makefile
                 gnome_lirc_properties/config.py
                 gnome_lirc_properties/ui/Makefile
                 help/Makefile
                 po/Makefile.in])
AC_CONFIG_FILES([bin/gnome-lirc-properties],
                [chmod +x bin/gnome-lirc-properties])

AC_OUTPUT()

dnl print configuration status ===

AC_MSG_NOTICE([=====================================================================])
AC_MSG_NOTICE([  PolicyKit support: $enable_policy_kit])
AC_MSG_NOTICE([  Remotes database: $with_remotes_database])
AC_MSG_NOTICE([  IR record tool: $LIRC_IRRECORD])
AC_MSG_NOTICE([  LIRC configuration directory: $with_lirc_confdir])
AC_MSG_NOTICE([  LIRC configuration file: $with_lirc_hardware_conf])
AC_MSG_NOTICE([  LIRCd socket: $with_lircd_socket])
AC_MSG_NOTICE([  Startup style: $with_startup_style])
AC_MSG_NOTICE([=====================================================================])


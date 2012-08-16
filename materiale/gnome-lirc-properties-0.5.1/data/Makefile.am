SUBDIRS = icons

# Most distros will probably want to use --sysconfdir=/etc,
# because that is what most distros have configured D-Bus to use.
dbusconfdir = $(sysconfdir)/dbus-1/system.d
dbusconf_DATA = org.gnome.LircProperties.Mechanism.conf

policykitpolicydir = $(datadir)/polkit-1/actions
policykitpolicy_in_files = org.gnome.lirc-properties.mechanism.policy.in
policykitpolicy_DATA = org.gnome.lirc-properties.mechanism.policy

# The .service file is generated from a .service.in file
# so that the install location can be inserted.
servicedir = $(datadir)/dbus-1/system-services
service_in_files = org.gnome.LircProperties.Mechanism.service.in
service_DATA = org.gnome.LircProperties.Mechanism.service

# The .desktop file is generated from a .desktop.in file
# so that intltool can take care of localization.
desktopdir = $(datadir)/applications
desktop_in_files = gnome-lirc-properties.desktop.in
desktop_DATA = gnome-lirc-properties.desktop

# Blacklist and whitelist of input devices
fdidir = $(datadir)/hal/fdi/policy/10osvendor
fdi_DATA = 20-x11-remotes.fdi

noinst_PROGRAMS = lirc-generate-linux-input
lirc_generate_linux_input_SOURCES = lirc-generate-linux-input.c
lirc_generate_linux_input_CFLAGS = $(GLIB_CFLAGS)
lirc_generate_linux_input_LDADD = $(GLIB_LIBS)

resourcesdir = $(pkgdatadir)

linux-input-layer-lircd.conf: lirc-generate-linux-input /usr/include/linux/input.h
	$(AM_V_GEN) $(builddir)/lirc-generate-linux-input > $@

resources_DATA = \
	gnome-lirc-properties.ui \
	gnome-lirc-properties-custom-config.ui \
	gnome-lirc-properties-receiver.ui \
	linux-input-layer-lircd.conf \
	receivers.conf

EXTRA_DIST = \
	overrides.conf \
	$(dbusconf_DATA) \
	$(desktop_in_files) \
	$(policykitpolicy_in_files) \
	$(resources_DATA) \
	$(service_in_files) \
	$(fdi_DATA)

DISTCLEANFILES = \
	linux-input-layer-lircd.conf \
	$(desktop_DATA) \
	$(policykitpolicy_DATA) \
	$(service_DATA)

@INTLTOOL_DESKTOP_RULE@

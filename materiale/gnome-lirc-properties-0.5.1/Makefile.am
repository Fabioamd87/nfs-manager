SUBDIRS = bin data gnome_lirc_properties help po
man1_MANS = man/gnome-lirc-properties.1

EXTRA_DIST = \
        autogen.sh \
	gnome-doc-utils.make \
	man/gnome-lirc-properties.1

DISTCLEANFILES = \
	intltool-extract \
	intltool-merge \
	intltool-update

DISTCHECK_CONFIGURE_FLAGS = \
	--disable-scrollkeeper

# Build ChangeLog from GIT history
ChangeLog:
	@if test -f $(top_srcdir)/.git/HEAD; then \
		git log --stat --after="Thu Sep 10 18:00:37 2009" > $@; \
	fi

dist: ChangeLog

.PHONY: ChangeLog


bin_SCRIPTS = gnome-lirc-properties

noinst_PROGRAMS = lirc-fixup-keys
lirc_fixup_keys_SOURCES = lirc-fixup-keys.c
lirc_fixup_keys_CFLAGS = $(GLIB_CFLAGS)
lirc_fixup_keys_LDADD = $(GLIB_LIBS)

lirc-fixup-upstream: lirc-fixup-keys nns_full.txt
	if test -d lirc; then \
		rm -rf lirc; \
	fi
	cvs -z8 -d:pserver:anonymous@lirc.cvs.sourceforge.net:/cvsroot/lirc co lirc
	cd lirc && git init && git add --ignore-errors . && git commit -m "lirc snapshot"
	./lirc-fixup-keys nns_full.txt lirc/remotes/
	cd lirc && git diff > ../lirc-fixup-keys.patch

lirc-check-keys: lirc-fixup-keys nns_full.txt
	lirc-fixup-keys -d lirc/remotes/

EXTRA_DIST =					\
	lirc-receiver-list			\
	todo-list				\
	nns_full.txt

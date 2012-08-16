# License: GPL v2 or later
# Copyright Red Hat Inc. 2008

PKGNAME=python-slip

SCM_REMOTEREPO_RE = ^ssh://(.*@)?git.fedorahosted.org/git/$(PKGNAME).git$
SCM_REMOTE_BRANCH = 0.2.x
UPLOAD_URL = ssh://fedorahosted.org/$(PKGNAME)

PY_SOURCES = $(wildcard slip/*.py slip/dbus/*.py slip/gtk/*.py)

all:	py-build
	
include rpmspec_rules.mk
include py_rules.mk
include git_rules.mk
include upload_rules.mk

install:	py-install

clean:	py-clean

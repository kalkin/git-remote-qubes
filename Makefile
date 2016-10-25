BINDIR=/usr/bin
SYSCONFDIR=/etc
DESTDIR=
PROGNAME=git-remote-qubes
SITELIBDIR=`python2 -c 'import distutils.sysconfig; print distutils.sysconfig.get_python_lib()'`

OBJLIST=$(shell find src/gitremotequbes -name '*.py' | sed 's/.py$$/.pyc/')
SUBSTLIST=etc/qubes-rpc/ruddo.Git

all: $(OBJLIST) $(SUBSTLIST) bin/git-*-qubes

src/gitremotequbes/%.pyc: src/gitremotequbes/%.py
	@if [ -z "$(SITELIBDIR)" ] ; then echo Error: you need python 2 on your system >&2 ; exit 1 ; fi
	python -m compileall src/gitremotequbes/

etc/%: etc/%.in
	cat $< | sed 's|@BINDIR@|$(BINDIR)|g' > $@

clean:
	rm -rfv $(OBJLIST) $(SUBSTLIST)
	find -name '*~' -print0 | xargs -0 rm -fv
	rm -fv *.tar.gz *.rpm

dist: clean
	DIR=$(PROGNAME)-`awk '/^Version:/ {print $$2}' $(PROGNAME).spec` && FILENAME=$$DIR.tar.gz && tar cvzf "$$FILENAME" --exclude "$$FILENAME" --exclude .git --exclude .gitignore -X .gitignore --transform="s|^|$$DIR/|" --show-transformed *

rpm: dist
	T=`mktemp -d` && rpmbuild --define "_topdir $$T" -ta $(PROGNAME)-`awk '/^Version:/ {print $$2}' $(PROGNAME).spec`.tar.gz || { rm -rf "$$T"; exit 1; } && mv "$$T"/RPMS/*/* "$$T"/SRPMS/* . || { rm -rf "$$T"; exit 1; } && rm -rf "$$T"

srpm: dist
	T=`mktemp -d` && rpmbuild --define "_topdir $$T" -ts $(PROGNAME)-`awk '/^Version:/ {print $$2}' $(PROGNAME).spec`.tar.gz || { rm -rf "$$T"; exit 1; } && mv "$$T"/SRPMS/* . || { rm -rf "$$T"; exit 1; } && rm -rf "$$T"

install-vm: all
	install -Dm 644 src/gitremotequbes/*.py src/gitremotequbes/*.pyc -t $(DESTDIR)/$(SITELIBDIR)/gitremotequbes/
	install -Dm 755 bin/git-*-qubes -t $(DESTDIR)/$(BINDIR)/
	install -Dm 755 etc/qubes-rpc/ruddo.Git -t $(DESTDIR)/$(SYSCONFDIR)/qubes-rpc/
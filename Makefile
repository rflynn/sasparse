# vim: set ts=8 noet:

test: venv/bin/nosetests
	-@# if/when tests crash or are killed they may leave coverage tmpfiles behind
	-@$(RM) .coverage.*
	venv/bin/nosetests

venv/bin/nosetests: venv

venv: requirements.txt
	[ -d venv ] || { virtualenv -p python3 venv || python3 -m venv venv; }
	venv/bin/pip install -r requirements.txt
	@touch venv

clean:

distclean: clean
	$(RM) -r venv/

venvpypy: Makefile
	[ -d venvpypy ] || { virtualenv --python="$$(which pypy3)" venvpypy || pypy3 -m venv venvpypy; }
	venvpypy/bin/pip install -r requirements.txt
	@touch venvpypy

.PHONY: install clean distclean

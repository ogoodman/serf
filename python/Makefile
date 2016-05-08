doc:
	epydoc serf

test:
	nosetests -s --exe

test-coverage:
	mkdir -p coverage
	nosetests --exe --with-coverage --cover-package=serf --cover-html --cover-html-dir=coverage

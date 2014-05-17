doc:
	epydoc serf

test:
	nosetests --exe

test-coverage:
	mkdir -p coverage
	nosetests --exe --with-coverage --cover-package=serf --cover-html --cover-html-dir=coverage

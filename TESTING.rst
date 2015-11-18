===================================
Lovely Elasticsearch Database Tests
===================================

Installation
============

Initial Step
------------

This initial step is only needed the first time after cloning the
repository::

    $ python bootstrap.py -v 2.3.1

Build the sandboxed environment using buildout::

    $ bin/buildout -N


Run the tests
=============

Start the test runner with this command::

    $ bin/test
=============================
Lovely Elasticsearch Database
=============================

Package that provides tools to manage Elasticsearch database objects with
Python classes.

Installation
============

Initial Step
------------

This initial step is only needed the first time after cloning the
repository::

    $ python bootstrap.py -v 2.3.1

Build the sandboxed environment using buildout::

    $ bin/buildout -N


Usage
=====

Add dependency
--------------

In your application, add this package as dependency (in the requires list of
your ``setup.py`` file for Lovely bootstrapped projects).

Use the elasticsearch pool
--------------------------

After app initialization first initialize the elasticsearch pool. Provide
a list of hosts and a dictionary with elasticsearch settings::

    >>> from lovely.esdb.connection import createESPool
    >>> createESPool(['localhost:9200'], {"cluster.name": "some_name"})

After that the get_es method returns an elasticsearch client::

    >>> es_client = get_es()

Document
--------

Create your classes inherited from ``Document``::

    >>> from lovely.esdb.models.document import Document
    >>> class MyDocument(Document):
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     name = Property(default=u'')

Create instances with properties set::

    >>> doc = MyDocument(id="1", name="John Doe")

Save document to elasticseach::

    >>> doc.index()

Or get a MyDocument object from elasticsearch::

    >>> doc = MyDocument.get('some_id')

See the doctests for more use cases.

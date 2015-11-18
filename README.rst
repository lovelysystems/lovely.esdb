=============================
Lovely Elasticsearch Database
=============================

Package that provides tools to manage Elasticsearch database objects with
Python classes.

Usage
=====

Add dependency
--------------

In your application, add this package as dependency (in the requires list of
your ``setup.py`` file for Lovely bootstrapped projects).

Document
--------

Create an elasticsearch client::

    >>> from elasticsearch import Elasticsearch
    >>> es_client = Elasticsearch(['localhost:9200'])

Create your classes inherited from ``Document``::

    >>> from lovely.esdb.document import Document, Property
    >>> class MyDocument(Document):
    ...     INDEX = 'mydocument'
    ...
    ...     ES = es_client
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

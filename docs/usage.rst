=====
Usage
=====

.. contents::

Here are some of the basics on how to use the ``Document`` class.

Implement a Document Class
--------------------------

Create your classes inherited from ``Document``::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property
    >>> class MyDocument(Document):
    ...     INDEX = 'mydocindex'
    ...
    ...     id = Property(primary_key=True)
    ...     name = Property(default=u'')
    ...
    ...     def __repr__(self):
    ...         return '<%s [id=%r, name=%r]>' % (
    ...                     self.__class__.__name__,
    ...                     self.id,
    ...                     self.name,
    ...                 )

The class can now globally be connected to an elasticsearch host.

``lovely.esdb`` uses the ``elasticsearch`` python package. We need an instance
of the ``Elasticsearch`` class to connect our documents to a store::

    >>> from elasticsearch import Elasticsearch
    >>> es_client = Elasticsearch(['localhost:%s' % crate_port])
    >>> MyDocument.ES = es_client

If you have only one elasticsearch cluster for your application it is also
possible to set the ES client for all new classes globally::

    >>> Document.ES = es_client

Create an index for the documents::

    >>> es_client.indices.create(
    ...     index=MyDocument.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "title" : { "type" : "string", "index" : "analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}


Create and Store Documents
--------------------------

That's all you need. Now you can use it::

    >>> doc = MyDocument(id="1", name="John Doe")
    >>> pprint(doc.store())
    {u'_id': u'1',
     u'_index': u'mydocindex',
     u'_type': u'default',
     u'_version': 1,
     u'created': True}


Get a Document
--------------

To get a document back using its ``primary key`` use the ``get`` method of
your class::

    >>> MyDocument.get("1")
    <MyDocument [id=u'1', name=u'John Doe']>


Get Multiple Documents
----------------------

``mget`` allows to get multiple documents by their ``primary key``::

    >>> pprint(MyDocument.mget(["1", "2"]))
    [<MyDocument [id=u'1', name=u'John Doe']>,
     None]


Search Documents
----------------

``Document`` provides a query method which allows to do any elasticsearch
query. The difference is that the result hits are resolved as ``Document``
instances::

    >>> _ = MyDocument.refresh()
    >>> query = {
    ...     "query": {
    ...         "match": {
    ...             "name": "John Doe"
    ...         }
    ...     }
    ... }
    >>> result = MyDocument.search(query)
    >>> pprint(result)
    {u'_shards': {u'failed': 0, u'successful': 1, u'total': 1},
     u'hits': {u'hits': [<MyDocument [id=u'1', name=u'John Doe']>],
               u'max_score': ...,
               u'total': 1},
     u'timed_out': False,
     u'took': ...}
    >>> result['hits']['hits']
    [<MyDocument [id=u'1', name=u'John Doe']>]


Delete a Document
-----------------

Deleting a document is as easy as creating it::

    >>> doc = MyDocument(id="2", name="to be deleted")
    >>> _ = doc.store()
    >>> pprint(doc.delete())
    {u'_id': u'2',
     u'_index': u'mydocindex',
     u'_type': u'default',
     u'_version': 2,
     u'found': True}

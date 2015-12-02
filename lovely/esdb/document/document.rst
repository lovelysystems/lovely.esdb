=======================
Elasticsearch Documents
=======================

Implement A Document
====================

Implement a document class::

    >>> from lovely.esdb.document import Document, Property

    >>> currentId = 0
    >>> def get_my_id():
    ...     global currentId
    ...     currentId += 1
    ...     return unicode(currentId)
    >>> class MyDocument(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True, default=get_my_id)
    ...     title = Property(default=u'')
    ...     name = Property(
    ...         default=u'',
    ...         doc="""
    ...         Add any documentation string to a property.
    ...         """
    ...         )
    ...     password = Property(name="pw")

    >>> MyDocument.name.doc
    '\n        Add any documentation string to a property.\n        '
    >>> MyDocument.title.doc
    u''

    >>> es_client.indices.create(
    ...     index=MyDocument.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "title" : { "type" : "string", "index" : "analyzed" },
    ...                     "name" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "pw" : { "type" : "string", "index" : "not_analyzed" },
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

    >>> doc = MyDocument()
    >>> doc.id
    u'1'
    >>> doc.title
    u''

Internal data::

    >>> from pprint import pprint
    >>> pprint(doc.get_source())
    {'id': u'1', 'title': u''}
    >>> pprint(doc._meta)
    {'_id': u'1', '_index': 'mydocument', '_type': 'default', '_version': None}
    >>> sorted(doc._update_properties)
    ['id', 'name', 'password', 'title']


Get source
==========

The ``get_source`` method only returns properties which are initialized::

    >>> doc2 = MyDocument()
    >>> doc2.get_source()
    {}

Initialization in constructor::

    >>> doc3 = MyDocument(id=u'someid')
    >>> doc3.get_source()
    {'id': u'someid'}

Initialization via property setter::

    >>> doc3.name = u'Günter'
    >>> pprint(doc3.get_source())
    {'id': u'someid', 'name': u'G\xfcnter'}

If a property getter is used, the default value is initialized and hence
available on the source::

    >>> doc3.title
    u''
    >>> pprint(doc3.get_source())
    {'id': u'someid', 'name': u'G\xfcnter', 'title': u''}


Save A Document
===============

To save a document use the "index" method::

    >>> doc.index()
    {u'_type': u'default', u'_id': u'1', u'created': True, u'_version': 1, u'_index': u'mydocument'}


Get A Document From Elasticsearch
=================================

    >>> prevId = currentId

Get the document::

    >>> myDoc = MyDocument.get(doc.id)
    >>> pprint(myDoc.get_source())
    {'id': u'1', 'name': u'', 'password': None, 'title': u''}
    >>> myDoc._meta
    {'_type': 'default', '_id': u'1', '_version': 1, '_index': 'mydocument'}

A get must not call the default() method for given properties::

    >>> currentId == prevId
    True

Get multiple documents from elasticsearch
=========================================

Create another document::

    >>> doc2 = MyDocument(title="A title", name="A Name")
    >>> _ = doc2.index()
    >>> prevId = currentId

Get a list of documents::

    >>> MyDocument.mget(['1', doc2.id])
    [<MyDocument object at 0x...>, <MyDocument object at 0x...>]

A mget must not call the default() method for given properties::

    >>> currentId == prevId
    True

If one document is not found, ``None`` is returned at that index::

    >>> MyDocument.mget(['1', doc2.id, 'unknown'])
    [<MyDocument object at 0x...>, <MyDocument object at 0x...>, None]

    >>> MyDocument.mget([])
    []

    >>> MyDocument.mget(None)
    []


Count Documents
===============

First refresh the index to be able the query can find the newly created
documents::

    >>> _ = MyDocument.refresh()

Count all documents::

    >>> MyDocument.count()
    2

Count with a query::

    >>> MyDocument.count({"query": {"term": {"title": "A title"}}})
    1


Update A Document
=================

Update instead of "index" a document allows to only update specific
properties::

    >>> myDoc.title = u'title'
    >>> myDoc.name = u'name'
    >>> myDoc.password = u'secret'
    >>> myDoc.update(['title', 'password'])
    {u'_type': u'default', u'_id': u'1', u'_version': 2, u'_index': u'mydocument'}

Only the title was changed in the database::

    >>> myDoc = MyDocument.get(doc.id)
    >>> pprint(myDoc.get_source())
    {'id': u'1', 'name': u'', 'password': u'secret', 'title': u'title'}

Set a value to None::

    >>> myDoc.name = None
    >>> _ = myDoc.update(['name'])
    >>> myDoc = MyDocument.get(myDoc.id)
    >>> print myDoc.get_source()['name']
    None


Updating A Not Existing Document
================================

Create a new document and provide all parameters in the contructor::

    >>> doc1 = MyDocument(id='newdoc', title='title 2', name='name 2')

Update the document::

    >>> doc1.update(['name'])
    {u'_type': u'default', u'_id': u'newdoc', u'_version': 1, u'_index': u'mydocument'}

Because the document is a new document it is fully written to elasticsearch::

    >>> myDoc = MyDocument.get(doc1.id)
    >>> pprint(myDoc.get_source())
    {'id': u'newdoc', 'name': u'name 2', 'password': None, 'title': u'title 2'}

Create a document with a default values (id)::

    >>> nextId = currentId + 1
    >>> doc3 = MyDocument(title='title 3', name='name 3')
    >>> doc3.update(['name'])
    {u'_type': u'default', u'_id': u'3', u'_version': 1, u'_index': u'mydocument'}
    >>> myDoc = MyDocument.get(nextId)
    >>> pprint(myDoc.get_source())
    {'id': u'3', 'name': u'name 3', 'password': None, 'title': u'title 3'}

Search
======

Refresh index and do a search query::

    >>> _ = MyDocument.refresh()
    >>> body = {
    ...     "query": {
    ...         "match": {
    ...             "title": "title 2"
    ...         }
    ...     }
    ... }
    >>> prevId = currentId

    >>> docs = MyDocument.search(body)

A tuple with the object and the search score is returned::

    >>> docs
    [(<MyDocument object at 0x...>, 2...)]
    >>> print docs[0][0].title
    title 2

Empty list is returned if nothing is found::

    >>> body['query']['match']['title'] = 'xxxx'
    >>> MyDocument.search(body)
    []

A search must not call the default() method for given properties::

    >>> currentId == prevId
    True


Delete
======

Documents can be deleted::

    >>> doc = MyDocument()
    >>> _ = doc.index()
    >>> MyDocument.get(doc.id) is not None
    True
    >>> doc.delete(refresh=True)
    {u'found': True, u'_type': u'default', u'_id': u'...', u'_version': 2, u'_index': u'mydocument'}
    >>> MyDocument.get(doc.id) is None
    True

Deleteing an already deleted document raises an exception::

    >>> doc.delete(refresh=True)
    Traceback (most recent call last):
    NotFoundError: TransportError(404, u'{"found":false,"_index":"mydocument","_type":"default","_id":"...","_version":3}')

The exception can be avoided by using the ignore parameter::

    >>> doc.delete(refresh=True, ignore=[404])
    {u'found': False, u'_type': u'default', u'_id': u'...', u'_version': 4, u'_index': u'mydocument'}


ES Client property
==================

The ES property on the Document class must be set, otherwise it's not possible
to fetch or store objects::

    >>> class ClientLessDocument(Document):
    ...
    ...     INDEX = 'clientlessdocument'
    ...
    ...     id = Property(primary_key=True)

Works on instance methods::

    >>> cld = ClientLessDocument(id='1')
    >>> cld.index()
    Traceback (most recent call last):
    ValueError: No ES client is set on class ClientLessDocument

And class methods::

    >>> ClientLessDocument.get('2')
    Traceback (most recent call last):
    ValueError: No ES client is set on class ClientLessDocument


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=MyDocument.INDEX)
    {u'acknowledged': True}

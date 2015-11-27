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

    >>> doc._source
    {'pw': None, 'title': u'', 'id': u'1', 'name': u''}
    >>> doc._meta
    {'_type': 'default', '_id': u'1', '_version': None, '_index': 'mydocument'}
    >>> doc._update_properties
    ['pw', 'title', 'id', 'name']


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
    >>> myDoc._source
    {'pw': None, 'title': u'', 'id': u'1', 'name': u''}
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
    >>> myDoc._source
    {'pw': u'secret', 'title': u'title', 'id': u'1', 'name': u''}


Updating A Not Existing Document
================================

Create a new document and provide all parameters in the contructor::

    >>> doc1 = MyDocument(id='newdoc', title='title 2', name='name 2')

Update the document::

    >>> doc1.update(['name'])
    {u'_type': u'default', u'_id': u'newdoc', u'_version': 1, u'_index': u'mydocument'}

Because the document is a new document it is fully written to elasticsearch::

    >>> myDoc = MyDocument.get(doc1.id)
    >>> myDoc._source
    {'pw': None, 'title': u'title 2', 'id': u'newdoc', 'name': u'name 2'}


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
    [(<MyDocument object at 0x...>, 1...)]
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

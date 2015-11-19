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
    ...     name = Property(default=u'')

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
    {'title': u'', 'id': u'1', 'name': u''}
    >>> doc._meta
    {'_type': 'default', '_id': u'1', '_version': None, '_index': 'mydocument'}
    >>> doc._update_properties
    ['title', 'id', 'name']


Save A Document
===============

To save a document use the "index" method::

    >>> doc.index()
    {u'_type': u'default', u'_id': u'1', u'created': True, u'_version': 1, u'_index': u'mydocument'}


Get A Document From Elasticsearch
=================================

Get the document::

    >>> myDoc = MyDocument.get(doc.id)
    >>> myDoc._source
    {'title': u'', 'id': u'1', 'name': u''}
    >>> myDoc._meta
    {'_type': 'default', '_id': u'1', '_version': 1, '_index': 'mydocument'}


Get multiple documents from elasticsearch
=========================================

Get a list of documents::

    >>> doc2 = MyDocument(title="A title", name="A Name")
    >>> _ = doc2.index()
    >>> MyDocument.mget(['1', doc2.id])
    [<MyDocument object at 0x...>, <MyDocument object at 0x...>]

If one document is not found, ``None`` is returned at that index::

    >>> MyDocument.mget(['1', doc2.id, 'unknown'])
    [<MyDocument object at 0x...>, <MyDocument object at 0x...>, None]

    >>> MyDocument.mget([])
    []

    >>> MyDocument.mget(None)
    []


Update A Document
=================

Update instead of "index" a document allows to only update specific
properties::

    >>> myDoc.title = u'title'
    >>> myDoc.name = u'name'
    >>> myDoc.update(['title'])
    {u'_type': u'default', u'_id': u'1', u'_version': 2, u'_index': u'mydocument'}

Only the title was changed in the database::

    >>> myDoc = MyDocument.get(doc.id)
    >>> myDoc._source
    {'title': u'title', 'id': u'1', 'name': u''}


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
    {'title': u'title 2', 'id': u'newdoc', 'name': u'name 2'}


Search
======

Refresh index and do a search query::

    >>> _ = es_client.indices.refresh(index="mydocument")
    >>> body = {
    ...     "query": {
    ...         "match": {
    ...             "title": "title 2"
    ...         }
    ...     }
    ... }
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

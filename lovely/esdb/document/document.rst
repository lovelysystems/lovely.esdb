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

Internal data. Only initialised properties exists in _source::

    >>> from pprint import pprint
    >>> pprint(doc.get_source())
    {'id': u'1'}
    >>> pprint(doc._meta)
    {'_id': u'1', '_index': 'mydocument', '_type': 'default', '_version': None}
    >>> sorted(doc._update_properties)
    ['id', 'name', 'password', 'title']


Get source
==========

The ``get_source`` method only returns properties which are initialised::

    >>> doc2 = MyDocument()
    >>> doc2.get_source()
    {}

Initialisation in constructor::

    >>> doc3 = MyDocument(id=u'someid')
    >>> doc3.get_source()
    {'id': u'someid'}

Initialisation via property setter::

    >>> doc3.name = u'Günter'
    >>> pprint(doc3.get_source())
    {'id': u'someid', 'name': u'G\xfcnter'}

Accessing a property which hasn't been initialised yet will lead return the
properties default value::

    >>> doc3.title
    u''

If a property getter is used, the default value is not initialised and hence
not available on the source. ::

    >>> pprint(doc3.get_source())
    {'id': u'someid', 'name': u'G\xfcnter'}


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

    >>> res = MyDocument.mget(['1', doc2.id])
    >>> print res
    [<MyDocument object at 0x...>, <MyDocument object at 0x...>]

The order is the same as the provided id list::

    >>> print res[0].id
    1

    >>> res = MyDocument.mget([doc2.id, '1'])
    >>> print res[0].id == doc2.id
    True

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

Updating a document with an object *not* loaded from the database::

    >>> notLoadedDoc = MyDocument(id=myDoc.id, name='not loaded')
    >>> notLoadedDoc.get_source()
    {'id': u'1', 'name': 'not loaded'}

The update body will reflect the upcoming changes. Note: The `upsert` contains
all available properties with possible defaults::

    >>> notLoadedDoc.get_update_body()
    {'doc': {'id': u'1', 'name': 'not loaded'},
     'upsert': {'pw': None, 'title': u'', 'id': u'1', 'name': 'not loaded'}}

    >>> _ = notLoadedDoc.update()

    >>> notLoadedDoc.get_source()
    {'id': u'1', 'name': 'not loaded'}

Loading the updated object from the database will show only the property
'name' has been updated::

    >>> MyDocument.get(myDoc.id).get_source()
    {'title': u'title', 'password': u'secret', 'id': u'1', 'name': u'not loaded'}


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
    >>> docs = MyDocument.search(body)

An elasticsearch result object is returned::

    >>> docs
    {u'hits': {u'hits': [<MyDocument ...], u'total': 1, u'max_score': ...}, u'_shards': {...}, ...}

The hits are resolved to documents::

    >>> docs['hits']['hits']
    [<MyDocument ...]
    >>> print docs['hits']['hits'][0].title
    title 2

Empty list is returned if nothing is found::

    >>> body['query']['match']['title'] = 'xxxx'
    >>> MyDocument.search(body)['hits']['hits']
    []


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


Primary Key
===========

The primary key value of a document is provided by the property
`primary_key`::

    >>> doc_pk = MyDocument(id=u'my_primary_key')
    >>> doc_pk.primary_key
    u'my_primary_key'

Exactly one primary key property must be defined on a document. If more than
one primary key property was defined one proper exception will be raised when
the meta class of such a document is loaded::

    >>> class TwoKeyDocument(Document):
    ...
    ...     INDEX = 'twokeydocument'
    ...
    ...     id1 = Property(primary_key=True)
    ...     id2 = Property(primary_key=True)
    Traceback (most recent call last):
    AttributeError: Multiple primary key properties.

If no primary key was defined one propery exception will be raised when
`primary_key` is accessed::

    >>> class NoKeyDocument(Document):
    ...
    ...     INDEX = 'nokeydocument'
    ...
    ...     id = Property(primary_key=False)
    >>> nokey = NoKeyDocument(id='1')
    >>> nokey.primary_key
    Traceback (most recent call last):
    AttributeError: No primary key column defined


Document inheritance
====================

Documents might inherit from other document classes without the need of
defining a different index::

    >>> class MyOtherDoc(MyDocument):
    ...     pass

    >>> MyOtherDoc.INDEX == MyDocument.INDEX
    True

The Registry contains one entry for each class per table::

    >>> from lovely.esdb.document import document
    >>> document.DocumentRegistry[MyOtherDoc.INDEX]
    {'MyOtherDoc': <class 'MyOtherDoc'>, 'MyDocument': <class 'MyDocument'>}

Another class with the same class name for the same table will cause an error::

    >>> class MyOtherDoc(MyDocument):
    ...     pass
    Traceback (most recent call last):
    NameError: Duplicate document name "MyOtherDoc" for index "mydocument"

If such a document is saved to the database the internally used field
`_db_class` is written to the document::

    >>> myOtherDoc = MyOtherDoc(id='other-1')
    >>> '_db_class' in myOtherDoc._source
    False

    >>> _ = myOtherDoc.index()

    >>> myOtherDoc._source['_db_class']
    'MyOtherDoc'

This field is not returned by the method `get_source`::

    >>> '_db_class' in myOtherDoc.get_source()
    False

After writing the document to the database the document could be loaded
again::

    >>> _ = MyOtherDoc.refresh()

    >>> MyOtherDoc.get('other-1').__class__ == MyOtherDoc
    True

It doesn't matter which base class is used to load the document because the
class to instantiate the object is determined by a lookup in the
document registry with the index and the value of `_db_class` as keys::

    >>> MyDocument.get('other-1').__class__ == MyOtherDoc
    True

If a stored object does contain the field `_db_class` then the called class is
used for instantiation::

    >>> _source = myOtherDoc.get_source()
    >>> '_db_class' in _source
    False

    >>> _ = MyOtherDoc.ES.index(
    ...             index=MyOtherDoc.INDEX,
    ...             doc_type=MyOtherDoc.DOC_TYPE,
    ...             id='other-2',
    ...             body=_source
    ...         )
    >>> _ = MyOtherDoc.refresh()

    >>> MyDocument.get('other-2').__class__ == MyDocument
    True
    >>> MyOtherDoc.get('other-2').__class__ == MyOtherDoc
    True


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=MyDocument.INDEX)
    {u'acknowledged': True}

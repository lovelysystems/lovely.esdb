=======================
Elasticsearch Documents
=======================

A test helper::

    >>> def showDocumentValues(doc):
    ...     pprint({
    ...         "source": doc._values.source,
    ...         "changed": doc._values.changed,
    ...         "default": doc._values.default,
    ...     })


Implement A Document
====================

Implement a document class::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property

A generator to create unique ids::

    >>> currentId = 0
    >>> def get_my_id():
    ...     global currentId
    ...     currentId += 1
    ...     return unicode(currentId)

A new document class derived from `Document`::

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
    ...
    ...     def __repr__(self):
    ...         return '<%s [id=%r, title=%r, name=%r, password=%r]>' % (
    ...                     self.__class__.__name__,
    ...                     self.id,
    ...                     self.title,
    ...                     self.name,
    ...                     self.password
    ...                 )

    >>> MyDocument.name.doc
    '\n        Add any documentation string to a property.\n        '
    >>> MyDocument.title.doc
    u''

Create an index on which the document can be stored::

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

Now a new document can be created::

    >>> doc = MyDocument()

The id is set to the value which is returned from the id generator::

    >>> doc.id
    u'1'
    >>> doc.title
    u''

A document is a new document if it was not loaded from the database and has
never beed stored::

    >>> doc.is_new()
    True

All values are set as defaults::

    >>> doc
    <MyDocument [id=u'1', title=u'', name=u'', password=None]>
    >>> showDocumentValues(doc)
    {'changed': {},
     'default': {'id': u'1', 'name': u'', 'pw': None, 'title': u''},
     'source': {}}


Store a Document
================

The store method stores our new index::

    >>> doc.store()
    {u'_type': u'default', u'_id': u'1', u'created': True, u'_version': 1, u'_index': u'mydocument'}

    >>> doc
    <MyDocument [id=u'1', title=u'', name=u'', password=None]>

Now the document is no longer a new document::

    >>> doc.is_new()
    False

The values are all copied to the source::

    >>> showDocumentValues(doc)
    {'changed': {},
     'default': {},
     'source': {'id': u'1', 'name': u'', 'pw': None, 'title': u''}}

The document can be retrieved using the primary key::

    >>> retrieved_doc = MyDocument.get(doc.primary_key)
    >>> retrieved_doc.id == doc.id
    True

The retrieved document has the same data::

    >>> retrieved_doc
    <MyDocument [id=u'1', title=u'', name=u'', password=None]>

but it is not the same instance::

    >>> retrieved_doc is doc
    False

Modify a document and store it::

    >>> doc.title = 'modified'
    >>> showDocumentValues(doc)
    {'changed': {'title': 'modified'},
     'default': {},
     'source': {'id': u'1', 'name': u'', 'pw': None, 'title': u''}}

    >>> doc.store()
    {u'_type': u'default', u'_id': u'1', u'created': False, u'_version': 2, u'_index': u'mydocument'}

    >>> showDocumentValues(doc)
    {'changed': {},
     'default': {},
     'source': {'id': u'1', 'name': u'', 'pw': None, 'title': 'modified'}}

    >>> retrieved_doc = MyDocument.get(doc.primary_key)
    >>> retrieved_doc.title
    u'modified'


Get a Single Document
=====================

Remember the the current id::

    >>> prevId = currentId

Get the document::

    >>> doc = MyDocument.get(doc.id)
    >>> doc
    <MyDocument [id=u'1', title=u'modified', name=u'', password=None]>
    >>> doc._meta
    {'_type': 'default', '_id': u'1', '_version': 2, '_index': 'mydocument'}
    >>> showDocumentValues(doc)
    {'changed': {},
     'default': {},
     'source': {u'id': u'1', u'name': u'', u'pw': None, u'title': u'modified'}}

current id has not changed because the get used the id from the database::

    >>> currentId == prevId
    True


Get Multiple Documents
======================

Create another document::

    >>> doc2 = MyDocument(title="A title", name="A Name")
    >>> _ = doc2.store()
    >>> prevId = currentId

Get a list of documents::

    >>> res = MyDocument.mget(['1', doc2.id])
    >>> pprint(res)
    [<MyDocument [id=u'1', title=u'modified', name=u'', password=None]>,
     <MyDocument [id=u'2', title=u'A title', name=u'A Name', password=None]>]

The order in the result list is the same as in the parameter::

    >>> res = MyDocument.mget([doc2.id, '1'])
    >>> pprint(res)
    [<MyDocument [id=u'2', title=u'A title', name=u'A Name', password=None]>,
     <MyDocument [id=u'1', title=u'modified', name=u'', password=None]>]

A mget must not call the default() method for given properties::

    >>> currentId == prevId
    True

If one document is not found, ``None`` is returned at that index::

    >>> pprint(MyDocument.mget(['1', doc2.id, 'unknown']))
    [<MyDocument [id=u'1', title=u'modified', name=u'', password=None]>,
     <MyDocument [id=u'2', title=u'A title', name=u'A Name', password=None]>,
     None]

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


Update or Create A Document
===========================

This is a special feature which must be used with care. It allows to update an
existing document without reading it first. This means the instance created is
not fully defined. A use case would be performance because it allows to update
parts of a document without the need to read it first.

Create an instance of a document with the id of an existing document::

    >>> original = MyDocument(id='original',
    ...                       title='original title',
    ...                       name='original name',
    ...                       password='original password')
    >>> _ = original.store()

    >>> updDoc = MyDocument(id='original', name='update or create')
    >>> pprint((original, updDoc))
    (<MyDocument [id='original', title='original title', name='original name', password='original password']>,
     <MyDocument [id='original', title=u'', name='update or create', password=None]>)

Now it is possible to update the document::

    >>> _ = updDoc.update_or_create()

The in memory object and the updated document do not contain the same data::

    >>> pprint((MyDocument.get('original'), updDoc))
    (<MyDocument [id=u'original', title=u'original title', name=u'update or create', password=u'original password']>,
     <MyDocument [id='original', title=u'', name='update or create', password=None]>)

If a document does not exist it will be created with the default values of the
missing properties::

    >>> updDoc = MyDocument(id='newupd', name='update or create')
    >>> _ = updDoc.update_or_create()
    >>> pprint((MyDocument.get('newupd'), updDoc))
    (<MyDocument [id=u'newupd', title=u'', name=u'update or create', password=None]>,
     <MyDocument [id='newupd', title=u'', name='update or create', password=None]>)

It is also possible to select which properties to update::

    >>> updDoc.name = 'new upd name'
    >>> updDoc.title = 'new upd title'
    >>> _ = updDoc.update_or_create(['title'])
    >>> pprint((MyDocument.get('newupd'), updDoc))
    (<MyDocument [id=u'newupd', title=u'new upd title', name=u'update or create', password=None]>,
     <MyDocument [id='newupd', title='new upd title', name='new upd name', password=None]>)


Get Documents By Property
=========================

Often it is needed to query for documents not using the primary key but using
another single property. This can be done with the `get_by` class method::

    >>> _ = MyDocument.refresh()
    >>> pprint(MyDocument.get_by(MyDocument.name, 'update or create'))
    [<MyDocument [id=u'original', title=u'original title', name=u'update or create', password=u'original password']>]

    >>> pprint(MyDocument.get_by(MyDocument.title, 'new upd title'))
    [<MyDocument [id=u'newupd', title=u'new upd title', name=u'update or create', password=None]>]

It is also possible to provide a list as value::

    >>> pprint(MyDocument.get_by(MyDocument.name,
    ...                          ['update or create', 'new upd name'],
    ...                          size=10
    ...                         ))
    [<MyDocument [id=u'original', title=u'original title', name=u'update or create', password=u'original password']>,
     <MyDocument [id=u'newupd', title=u'new upd title', name=u'update or create', password=None]>]


Search
======

Refresh index and do a search query::

    >>> _ = MyDocument.refresh()
    >>> body = {
    ...     "query": {
    ...         "match": {
    ...             "title": "new upd title"
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
    >>> docs['hits']['hits'][0].title
    u'new upd title'

Empty list is returned if nothing is found::

    >>> body['query']['match']['title'] = 'xxxx'
    >>> MyDocument.search(body)['hits']['hits']
    []


Delete
======

Documents can be deleted::

    >>> doc = MyDocument()
    >>> _ = doc.store()
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


Access The Source Data
======================

The document can provide the `source` data structure which is just a dict
containing all properties::

    >>> pprint(doc.get_source())
    {'id': u'3', 'name': u'', 'password': None, 'title': u''}


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
    >>> cld.store()
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
    AttributeError: No primary key column defined for "NoKeyDocument"


Document inheritance
====================

Documents might inherit from other document classes without the need of
defining a different index::

    >>> class MyOtherDoc(MyDocument):
    ...     WITH_INHERITANCE = True

    >>> MyOtherDoc.INDEX == MyDocument.INDEX
    True

.. note::

    WITH_INHERITANCE must be set to True on all classes using the shared
    index or better in the base class!

Make the base class inheritable::

    >>> MyDocument.WITH_INHERITANCE = True

A document gets an index type name for the internal registry::

    >>> MyOtherDoc.INDEX_TYPE_NAME
    'mydocument.default'

The Registry contains one entry for each class per table::

    >>> from lovely.esdb.document import document
    >>> document.DOCUMENTREGISTRY[MyOtherDoc.INDEX_TYPE_NAME]
    {'MyOtherDoc': <class 'MyOtherDoc'>, 'MyDocument': <class 'MyDocument'>}

Another class with the same class name for the same table will cause an error::

    >>> class MyOtherDoc(MyDocument):
    ...     pass
    Traceback (most recent call last):
    NameError: Duplicate document name "MyOtherDoc" for index type "mydocument.default"

If such a document is saved to the database the internally used field
`db_class__` is written to the document::

    >>> myOtherDoc = MyOtherDoc(id='other-1')
    >>> myOtherDoc._values.get('db_class__')
    Traceback (most recent call last):
    KeyError: 'db_class__'

    >>> _ = myOtherDoc.store(refresh=True)
    >>> myOtherDoc._values.get('db_class__')
    'MyOtherDoc'

After writing the document to the database the document could be loaded
again::

    >>> MyOtherDoc.get('other-1').__class__ == MyOtherDoc
    True

It doesn't matter which base class is used to load the document because the
class to instantiate the object is determined by a lookup in the
document registry with the index and the value of `db_class__` as keys::

    >>> MyDocument.get('other-1').__class__ == MyOtherDoc
    True

If a stored object does not contain the field `db_class__` then the called
class is used for instantiation::

    >>> source = myOtherDoc._values.source_for_index()
    >>> del source['db_class__']

    >>> _ = MyOtherDoc.ES.index(
    ...             index=MyOtherDoc.INDEX,
    ...             doc_type=MyOtherDoc.DOC_TYPE,
    ...             id='other-2',
    ...             body=source,
    ...             refresh=True,
    ...         )

    >>> MyDocument.get('other-2').__class__ == MyDocument
    True
    >>> MyOtherDoc.get('other-2').__class__ == MyOtherDoc
    True


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=MyDocument.INDEX)
    {u'acknowledged': True}

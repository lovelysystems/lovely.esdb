===================
Lazy Document Proxy
===================

    >>> from lovely.esdb.document.lazy import LazyDocument
    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property

    >>> class MyDoc(Document):
    ...     ES = es_client
    ...     INDEX = 'mydoc'
    ...     id = Property(primary_key=True)
    ...     name = Property(default='default name')
    ...     def __repr__(self):
    ...         return '<%s [id=%r, name=%r]>' % (
    ...                     self.__class__.__name__,
    ...                     self.id,
    ...                     self.name)

    >>> es_client.indices.create(
    ...     index=MyDoc.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "name" : { "type" : "string", "index" : "not_analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

Create a document::

    >>> doc = MyDoc(id='1')
    >>> doc.store(refresh=True)
    {u'_type': u'default', u'_id': u'1', u'created': True, u'_version': 1, u'_index': u'mydoc'}


Lazy Load a Document
====================

A LazyDocument can be instantiated with the document class and the primary key
of a document::

    >>> lazy_doc = LazyDocument(MyDoc, '1')

The lazy instance was not loading the document from the database::

    >>> object.__getattribute__(lazy_doc, "_doc_ref") is None
    True

Access to the primary key will not load the document because this information
is known without loading the document::

    >>> lazy_doc.id
    '1'
    >>> object.__getattribute__(lazy_doc, "_doc_ref") is None
    True

Access to another property will load the document::

    >>> lazy_doc.name
    u'default name'
    >>> object.__getattribute__(lazy_doc, "_doc_ref")
    <MyDoc [id=u'1', name=u'default name']>

It looks like MyDoc::

    >>> lazy_doc
    <MyDoc [id=u'1', name=u'default name']>

And behaves like MyDoc::

    >>> lazy_doc.name = 'new name'
    >>> lazy_doc.store()
    {u'_type': u'default', u'_id': u'1', u'created': False, u'_version': 2, u'_index': u'mydoc'}

The change is stored::

    >>> MyDoc.get('1')
    <MyDoc [id=u'1', name=u'new name']>


Existing Document as LazyDocument
=================================

A LazyDocument can be instantiated with an existing document::

    >>> doc2 = MyDoc(id='2', name='name 2')
    >>> lazy_doc = LazyDocument(doc2)
    >>> lazy_doc
    <MyDoc [id='2', name='name 2']>
    >>> isinstance(lazy_doc, MyDoc)
    True
    >>> lazy_doc.store()
    {u'_type': u'default', u'_id': u'2', u'created': True, u'_version': 1, u'_index': u'mydoc'}


LazyDocument With Volatile Properties
=====================================

A lazy document can be instantiated with `volatile` properties from other
sources::

    >>> lazy_doc = LazyDocument(MyDoc, '1', options='options')
    >>> lazy_doc.options
    'options'


Get the Unproxied Document
==========================

Remove the lazy document proxy and provide the original document instance::

    >>> from lovely.esdb.document import remove_proxy
    >>> remove_proxy(lazy_doc)
    <MyDoc [id=u'1', name=u'new name']>

This also works for not already loaded lazy documents::

    >>> lazy_doc = LazyDocument(MyDoc, '1')
    >>> remove_proxy(lazy_doc)
    <MyDoc [id=u'1', name=u'new name']>

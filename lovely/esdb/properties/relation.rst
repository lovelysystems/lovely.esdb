=================
Relation Property
=================


Define related documents::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property, Relation

    >>> class LocalDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     ref = Property()
    ...     rel = Relation('ref.id', 'RemoteDoc.id')

    >>> class RemoteDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     def __repr__(self):
    ...         return "<RemoteDoc %r>" % self.id

Create an index on which the document can be stored::

    >>> es_client.indices.create(
    ...     index=RemoteDoc.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

An instance of the document containing the relation::

    >>> doc = LocalDoc()
    >>> doc.ref is None
    True

Reading the relation provides an instance of RelationResolver::

    >>> resolver = doc.rel
    >>> resolver
    <RelationResolver RemoteDoc[None]>
    >>> resolver.id is None
    True
    >>> resolver.remote
    <class 'RemoteDoc'>

Assign a remote document::

    >>> remote = RemoteDoc(id='1')
    >>> doc.rel = remote

The previousely requested resolver can be used to access the changed
relation::

    >>> resolver
    <RelationResolver RemoteDoc[1]>
    >>> resolver.id
    '1'
    >>> resolver.remote
    <class 'RemoteDoc'>

The reference property contains the id::

    >>> doc.ref
    {'id': '1'}

The resolver can be used to get the references document::

    >>> _ = remote.store(refresh=True)
    >>> resolved_remote = resolver()
    >>> resolved_remote
    <RemoteDoc u'1'>

The resolver uses a cache::

    >>> id(resolved_remote) == id(resolver())
    True

None removes the id property::

    >>> doc.rel = None
    >>> doc.ref
    {}
    >>> doc.rel() is None
    True

Assign a dict containing the id of the remote document::

    >>> doc.rel = {'id': '2'}
    >>> doc.ref
    {'id': '2'}

Additional properties are ignored::

    >>> doc.rel = {'id': '3', 'more': 42}
    >>> doc.ref
    {'id': '3'}

Directly assign the id::

    >>> doc.rel = '4'
    >>> doc.ref
    {'id': '4'}
    >>> doc.rel = None
    >>> doc.ref
    {}

The reference property can contain other properties::

    >>> doc.ref['relproperty'] = 'relation data'
    >>> doc.ref
    {'relproperty': 'relation data'}

Changing the relation doesn't affect the additional properties::

    >>> doc.rel = '4'
    >>> doc.ref
    {'relproperty': 'relation data', 'id': '4'}

    >>> doc.rel = None
    >>> doc.ref
    {'relproperty': 'relation data'}


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=RemoteDoc.INDEX)
    {u'acknowledged': True}

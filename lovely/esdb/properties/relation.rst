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
    ...     rel = Relation('ref.rel_to_other', 'RemoteDoc.id')

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
    {'rel_to_other': '1'}

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

Directly assign the id::

    >>> doc.rel = '4'
    >>> doc.ref
    {'rel_to_other': '4'}
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
    {'relproperty': 'relation data', 'rel_to_other': '4'}

    >>> doc.rel = None
    >>> doc.ref
    {'relproperty': 'relation data'}

The RelationResolver provides a dict which represents the relation::

    >>> doc.rel.relation_dict
    {'id': None, 'class': 'RemoteDoc'}
    >>> doc.rel = '4'
    >>> doc.rel.relation_dict
    {'id': '4', 'class': 'RemoteDoc'}

The dict representation can also be used to set the relation::

    >>> dict_4 = doc.rel.relation_dict
    >>> doc.rel = {'id': '5'}
    >>> doc.ref
    {'relproperty': 'relation data', 'rel_to_other': '5'}

    >>> doc.rel = dict_4
    >>> doc.ref
    {'relproperty': 'relation data', 'rel_to_other': '4'}


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=RemoteDoc.INDEX)
    {u'acknowledged': True}

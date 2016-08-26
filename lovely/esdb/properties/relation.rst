=================
Relation Property
=================


Test Preparations
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


1:1 Relation
============

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

    >>> remote1 = RemoteDoc(id='1')
    >>> doc.rel = remote1

The reference property contains the id::

    >>> doc.ref
    {'rel_to_other': '1'}

The previousely requested resolver can be used to access the changed
relation::

    >>> resolver
    <RelationResolver RemoteDoc[1]>
    >>> resolver.id
    '1'
    >>> resolver.remote
    <class 'RemoteDoc'>

The resolver can be used to get the referenced document::

    >>> _ = remote1.store(refresh=True)
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


More Complex Relation References
================================


    >>> class ComplexLocalDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     a = Property()
    ...     a_rel = Relation('a', 'RemoteDoc.id')
    ...     b = Property()
    ...     b_rel = Relation('b.ref', 'RemoteDoc.id')
    ...     c = Property()
    ...     c_rel = Relation('c.very.deep.ref', 'RemoteDoc.id')

    >>> doc = ComplexLocalDoc(id=1)

    >>> doc.a_rel = 1
    >>> doc.a
    1
    >>> doc.a_rel()
    <RemoteDoc u'1'>
    >>> doc.a_rel = None
    >>> doc.a is None
    True
    >>> doc.a_rel() is None
    True

    >>> doc.b_rel = 1
    >>> doc.b
    {'ref': 1}
    >>> doc.b_rel()
    <RemoteDoc u'1'>
    >>> doc.b_rel = None
    >>> doc.b
    {}
    >>> doc.b_rel() is None
    True

    >>> doc.c_rel = 1
    >>> doc.c
    {'very': {'deep': {'ref': 1}}}
    >>> doc.c_rel()
    <RemoteDoc u'1'>
    >>> doc.c_rel = None
    >>> doc.c
    {'very': {'deep': {}}}
    >>> doc.c_rel() is None
    True


1:n Relation
============

1:n relations are stored as lists::

    >>> from lovely.esdb.properties import One2NRelation
    >>> class One2NLocalDoc(Document):
    ...
    ...     INDEX = 'one2onelocaldoc'
    ...
    ...     id = Property(primary_key=True)
    ...     a = Property()
    ...     a_rel = One2NRelation('a', 'RemoteDoc.id')

    >>> doc = One2NLocalDoc(id=1)
    >>> doc.a_rel
    <ListRelationResolver RemoteDoc(None)>
    >>> doc.a is None
    True
    >>> doc.a_rel = []
    >>> doc.a
    []
    >>> doc.a_rel[0]
    Traceback (most recent call last):
    IndexError: list index out of range

    >>> doc.a_rel = [1]
    >>> doc.a_rel[0]
    <ListItemRelationResolver[0] RemoteDoc[1]>

    >>> doc.a_rel[0]()
    <RemoteDoc u'1'>

    >>> doc.a_rel[0].relation_dict
    {'id': 1, 'class': 'RemoteDoc'}
    >>> doc.a_rel.relation_dict
    [{'id': 1, 'class': 'RemoteDoc'}]

    >>> doc.a_rel = [remote1, {'id': 2}, 3]
    >>> doc.a_rel.relation_dict
    [{'id': '1', 'class': 'RemoteDoc'},
     {'id': 2, 'class': 'RemoteDoc'},
     {'id': 3, 'class': 'RemoteDoc'}]


    >>> class ComplexOn2NLocalDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     a = Property()
    ...     a_rel = Relation('a', 'RemoteDoc.id')
    ...     b = Property()
    ...     b_rel = Relation('b.ref', 'RemoteDoc.id')
    ...     c = Property()
    ...     c_rel = Relation('c.very.deep.ref', 'RemoteDoc.id')

    >>> doc = ComplexOn2NLocalDoc(id=1)
    >>> doc.a_rel = [1]
    >>> doc.a
    [1]

    >>> doc.b_rel = [1]
    >>> doc.b
    {'ref': [1]}

    >>> doc.c_rel = [1]
    >>> doc.c
    {'very': {'deep': {'ref': [1]}}}


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=RemoteDoc.INDEX)
    {u'acknowledged': True}

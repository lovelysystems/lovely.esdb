=================
Relation Property
=================


Test Preparations
=================

Define related documents::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property, LocalRelation

    >>> class LocalDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     ref = Property()
    ...     rel = LocalRelation('ref.rel_to_other', 'RemoteDoc.id')

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


1:1 Relation With Properties
============================

Relations can hold additional properties::

    >>> class LocalPropertiesDoc(Document):
    ...
    ...     INDEX = 'localpropertiesdoc'
    ...
    ...     id = Property(primary_key=True)
    ...     ref = Property()
    ...     rel = LocalRelation(
    ...         'ref.rel_to_other',
    ...         'RemoteDoc.id',
    ...         relationProperties={'p1': None, 'p2': None}
    ...     )

    >>> doc = LocalPropertiesDoc(id=1)
    >>> doc.rel = {"id": '1', "p1": "prop1", "n1": "not used"}
    >>> doc.ref
    {'rel_to_other': {'p2': None, 'p1': 'prop1', 'id': '1'}}
    >>> doc.rel()
    <RemoteDoc u'1'>

    >>> remote2 = RemoteDoc(id='2')
    >>> _ = remote2.store()

    >>> doc.rel = '2'
    >>> doc.ref
    {'rel_to_other': {'p2': None, 'p1': 'prop1', 'id': '2'}}
    >>> doc.rel()
    <RemoteDoc u'2'>

    >>> doc.rel = {'p2': 'prop2'}
    >>> doc.ref
    {'rel_to_other': {'p2': 'prop2', 'p1': 'prop1', 'id': '2'}}

    >>> doc.rel = remote1
    >>> doc.ref
    {'rel_to_other': {'p2': 'prop2', 'p1': 'prop1', 'id': '1'}}
    >>> doc.rel()
    <RemoteDoc u'1'>


More Complex Relation References
================================

Some special use cases::

    >>> class ComplexLocalDoc(Document):
    ...
    ...     INDEX = 'mydocument'
    ...
    ...     id = Property(primary_key=True)
    ...     a = Property()
    ...     a_rel = LocalRelation('a', 'RemoteDoc.id')
    ...     b = Property()
    ...     b_rel = LocalRelation('b.ref', 'RemoteDoc.id')
    ...     c = Property()
    ...     c_rel = LocalRelation('c.very.deep.ref', 'RemoteDoc.id')
    ...     d_rel = LocalRelation(
    ...         'c.very.deep.propref',
    ...         'RemoteDoc.id',
    ...         relationProperties={'p1': None, 'p2': None}
    ...     )

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

    >>> doc.d_rel = remote1
    >>> doc.d_rel = {"p1": "prop1", "n1": "not used"}
    >>> doc.c
    {'very': {'deep': {'propref': {'p2': None, 'p1': 'prop1', 'id': '1'}}}}
    >>> doc.d_rel()
    <RemoteDoc u'1'>

    >>> doc.c_rel = 1
    >>> doc.c
    {'very': {'deep': {'ref': 1, 'propref': {'p2': None, 'p1': 'prop1', 'id': '1'}}}}


1:n Relation
============

1:n relations are stored as lists::

    >>> from lovely.esdb.properties import LocalOne2NRelation
    >>> class One2NLocalDoc(Document):
    ...
    ...     INDEX = 'one2onelocaldoc'
    ...
    ...     id = Property(primary_key=True)
    ...     a = Property()
    ...     a_rel = LocalOne2NRelation('a', 'RemoteDoc.id')

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
    ...     a_rel = LocalRelation('a', 'RemoteDoc.id')
    ...     b = Property()
    ...     b_rel = LocalRelation('b.ref', 'RemoteDoc.id')
    ...     c = Property()
    ...     c_rel = LocalRelation('c.very.deep.ref', 'RemoteDoc.id')

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


1:n Relation With Properties
============================

Relations can hold additional properties::

    >>> class One2NLocalPropertiesDoc(Document):
    ...
    ...     INDEX = 'one2nlocalpropertiesdoc'
    ...
    ...     id = Property(primary_key=True)
    ...     ref = Property()
    ...     rel = LocalOne2NRelation(
    ...         'ref.list_rel',
    ...         'RemoteDoc.id',
    ...         relationProperties={'p1': None, 'p2': None}
    ...     )

    >>> doc = One2NLocalPropertiesDoc(id=1)

    >>> doc.rel = [remote1]
    >>> doc.ref
    {'list_rel': [{'p2': None, 'p1': None, 'id': '1'}]}

    >>> doc.rel = [remote1, '2']
    >>> doc.ref
    {'list_rel': [{'p2': None, 'p1': None, 'id': '1'}, {'p2': None, 'p1': None, 'id': '2'}]}

    >>> doc.rel = [remote1, {'id': '2', 'p1': 'prop1', 'ignored': 42}]
    >>> doc.ref
    {'list_rel': [{'p2': None, 'p1': None, 'id': '1'}, {'p2': None, 'p1': 'prop1', 'id': '2'}]}


Clean Up
========

Delete the index used in this test::

    >>> es_client.indices.delete(index=RemoteDoc.INDEX)
    {u'acknowledged': True}

=========
Relations
=========

.. contents::


1:1 Relation
============

A simple relation property allows to manage and resolve one to one relations
between documents.

::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property, LocalRelation

    >>> class LocalDoc(Document):
    ...     """References RemoteDoc via the rel property.
    ...     """
    ...
    ...     INDEX = 'localdoc'
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     # The relation is configured with the name/path to the local
    ...     # property on which the relation stores its internal data and the
    ...     # remote Document and property name. The remote property name must
    ...     # be the primary key of the remote Document.
    ...     rel = LocalRelation('ref.ref_id', 'RemoteDoc.id')
    ...
    ...     # ref is the property which is needed by the relation to store the
    ...     # local relation data.
    ...     ref = Property()

RemoteDoc is the referenced document. There is nothing special about it::

    >>> class RemoteDoc(Document):
    ...     """Referenced document with only an id
    ...     """
    ...
    ...     INDEX = 'remotedoc'
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     def __repr__(self):
    ...         return "<RemoteDoc %r>" % self.id

Create an index on which the remote document can be stored::

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

Create a document which can be used in LocalDoc::

    >>> remote = RemoteDoc(id='1')
    >>> _ = remote.store()

    >>> local = LocalDoc()
    >>> local.rel = remote
    >>> local.rel()
    <RemoteDoc u'1'>

The ``ref`` property contains the id of the referenced document::

    >>> local.ref
    {'ref_id': '1'}

It is also possible to assign the primary key to the relation property::

    >>> remote2 = RemoteDoc(id='2')
    >>> _ = remote2.store()

    >>> local.rel = '2'
    >>> local.rel()
    <RemoteDoc u'2'>


1:n Relation
============

The simple 1:n relation maintains a local list with the ids of the related
documents.

::

    >>> from lovely.esdb.properties import LocalOne2NRelation
    >>> class LocalOne2NDoc(Document):
    ...     """References RemoteDoc via the rel property.
    ...     """
    ...
    ...     INDEX = 'localone2ndoc'
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     # The relation is configured with the name/path to the local
    ...     # property on which the relation stores its internal data and the
    ...     # remote Document and property name. The remote property name must
    ...     # be the primary key of the remote Document.
    ...     rel = LocalOne2NRelation('ref.ref_id', 'RemoteDoc.id')
    ...
    ...     # ref is the property which is needed by the relation to store the
    ...     # local relation data.
    ...     ref = Property()

    >>> local = LocalOne2NDoc()

    >>> local.rel = [remote]

The relation provides a resolver::

    >>> local.rel
    <ListRelationResolver RemoteDoc(['1'])>

The resolver allows access to the items::

    >>> local.rel[0]
    <ListItemRelationResolver[0] RemoteDoc[1]>

    >>> local.rel[0]()
    <RemoteDoc u'1'>

Item assignement::

    >>> local.rel = [remote, '2', {'id': '3'}]
    >>> local.rel
    <ListRelationResolver RemoteDoc(['1', '2', '3'])>

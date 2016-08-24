=========
Relations
=========

.. contents::


One To One Relation
===================

A simple relation property allows to manage and resolve one to one relations
between documents.


LocalDoc is the document which references another document via the `rel`
property. The `Relation` needs another property on which the relation stores
the id of the referenced document.

Here we create the relation with ``Relation('ref.id', 'RemoteDoc.id')``.

The first parameter ``'ref.id'`` defines the local property which will be used
to store the id of the remote document. The ``.id`` part defines the name of
the id in the ``ref`` property.

The second parameter defines the remote document with the name of the primary
key.

::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property, Relation

    >>> class LocalDoc(Document):
    ...
    ...     INDEX = 'localdoc'
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     ref = Property()
    ...     rel = Relation('ref.ref_id', 'RemoteDoc.id')

RemoteDoc is the referenced document. There is nothing special about it::

    >>> class RemoteDoc(Document):
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

    >>> remote = RemoteDoc(id='2')
    >>> _ = remote.store()

    >>> local.rel = '2'
    >>> local.rel()
    <RemoteDoc u'2'>

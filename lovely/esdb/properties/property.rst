==========
Properties
==========

Properties are representing database fields of documents.


Custom Getter and Setter
========================

Properties might use custom getter and/or setter for accessing field values.
Custom getter and setter methods are instances methods of a document decorated
as getter or setter of one specific property.

.. note::

      These custom getters and setters will be called with the value
      determined by the Property implementation. The modified value has to be
      returned to the Property implementation which is pretty unlikely for a
      setter method.

Example Document class::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property

    >>> currentId = 0
    >>> def get_my_id():
    ...     global currentId
    ...     currentId += 1
    ...     return unicode(currentId)
    >>> class SetterGetterDoc(Document):
    ...
    ...     INDEX = 'settergetterdoc'
    ...
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True, default=get_my_id)
    ...     title = Property(default=u'')
    ...
    ...     @title.setter
    ...     def set_title(self, value):
    ...         print "### set title"
    ...         return value.upper()
    ...
    ...     @title.getter
    ...     def get_title(self, value):
    ...         print "### get title"
    ...         return value.lower()
    ...
    ...     def __repr__(self):
    ...         return '<%s [id=%r, title=%r]>' % (
    ...                     self.__class__.__name__,
    ...                     self.id,
    ...                     self.title
    ...                 )

    >>> _ = es_client.indices.create(
    ...     index=SetterGetterDoc.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "title" : { "type" : "string", "index" : "analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })

The setter is called whenever the decorated property will be written. This
also includes initial writing while constructing an instance::

    >>> doc = SetterGetterDoc(title="Foo Bar")
    ### set title

    >>> doc.title = "Again Foo Bar"
    ### set title

Internally the property is stored in uppercase::

    >>> doc._values.changed
    {'title': 'AGAIN FOO BAR'}

But the setter will not be called when a stored document will be loaded from
the database::

    >>> _ = doc.store()
    >>> doc = SetterGetterDoc.get(doc.id)

The stored value has been manipulated by the custom setter::

    >>> pprint(doc._values.source)
    {u'db_class__': u'SetterGetterDoc', u'id': u'1', u'title': u'AGAIN FOO BAR'}

The getter is called whenever a property is accessed for reading by dotted
notation::

    >>> doc.title
    ### get title
    u'again foo bar'

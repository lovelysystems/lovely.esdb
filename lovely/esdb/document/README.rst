======================
esdb Document Handling
======================


Property Data Handling
======================

Property values are handled in the PropertyValueManager which provides some
mappings to manage the values.

A document holds the instance property _values which is an instance of a
PropertyValueManager. Properties manage their values inside this manager and
are allowed to access `_values` on the document.

_values.source
--------------

Is the copy of the currently known content in the database. It is not
neccessarily an exact copy of the current data. The content of `_source` is
meant to be read only for properties. It is set when a document is read from
the database and updated after storing/updating the document.


_values.changed
---------------

Like `_source` but contains only the modified properties. Properties write
into `_changed`.


_values.default
---------------

Contains all properties for which a new default value has been created. This
happens when a property is read and there is no value in `_changed` and in
`_source`.


_values.property_cache
----------------------

Properties can store cached values here. This is needed for complex data which
needs transformation between the database and the python representation. Such
properties usually use the `_apply` method to do the transformation into the
database representation before data is stored.


Property source Lookup
----------------------

The property source lookup is used to get the database representation of a
property.

Lookup order::

    1. _values.property_cache
    2. _values.changed
    3. _values.source
    4. _values.default

A source lookup happens in the `_transform_from_source`.
The default implementation of the `Property` class is doing the lookup in the
order described above.

Special property implementations which are using the `_property_cache` usually
provide the cached object if available or create a new cache entry based on
the default source lookup.


Document Value Manager
======================

The DocumentValueManager manages the different value storages::

    >>> from lovely.esdb.document.document import DocumentValueManager
    >>> manager = DocumentValueManager(None)
    >>> manager.source, manager.changed, manager.default, manager.property_cache
    ({}, {}, {}, {})
    >>> manager.changed['a'] = 'changed'
    >>> manager.default['b'] = 'default'
    >>> manager.source['c'] = 'source'
    >>> manager.get('a'), manager.get('b'), manager.get('c')
    ('changed', 'default', 'source')

    >>> manager.source['o'] = 'source'
    >>> manager.changed['o'] = 'changed'
    >>> manager.get('o')
    'changed'

    >>> manager.get('unknown')
    Traceback (most recent call last):
    KeyError: 'unknown'


Storing a New Document
======================

A newly in memory created document has an empty `_source`.
To build the JSON source, which is needed to be able to index a document, the
following lookup is done::

    1. _values.changed
    2. _values.source
    3. _values.default

After the document is stored `_source` is set to the JSON source. `_changed`
and `_default` is reset.

Create the source for indexing::

    >>> pprint(manager.source_for_index(update_source=False))
    {'a': 'changed',
     'b': 'default',
     'c': 'source',
     'db_class_': 'NoneType',
     'o': 'changed'}


Updating a Document
===================

If there is an already stored document only the changed properties need to be
changed. The JSON source for the document update is created using the
following lookup::

    1. _values.changed
    2. _values.default

After the document is stored `_source` is updated with the JSON source.
`_changed` and `_default` is reset.

Create the source for an update::

    >>> pprint(manager.source_for_update(update_source=False))
    {'a': 'changed', 'b': 'default', 'o': 'changed'}


Update or Create Document
=========================

This is a special use case which allows to update an existing document without
the need to first load it from the database. To be able to use this feature
the primary key of the document must be known.

First create a new instance of the document. Now assign the data to the
properties you want to change. Then call `update_or_create` on the document.

What happens:

The JSON source for the update will be created from `_changed` only. The JSON
source for the `upsert` will be created from `_changed` and all default values
of all properties providing defaults.

After the document is stored NO values are update (`_source` stays empty).

Do not use the `store` method on such documents.

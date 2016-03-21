===============
Pickle Property
===============


ObjectProperty
==============

The object property can be used to store python object on a document.

Usage::

    >>> from lovely.esdb.properties import ObjectProperty, Property
    >>> from lovely.esdb.document import Document
    >>> class MyDoc(Document):
    ...     INDEX = 'object_json_pickle__test'
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True)
    ...
    ...     o = ObjectProperty(
    ...         doc="Allows to store any python object"
    ...     )

    >>> _ = es_client.indices.create(
    ...     index=MyDoc.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "o" : {
    ...                         "dynamic": "ignore",
    ...                         "properties": {
    ...                             "name" : { "type" : "string", "index" : "not_analyzed" },
    ...                         }
    ...                     }
    ...                 }
    ...             }
    ...         }
    ...     })

    >>> from lovely.esdb.properties.testing import PickleDummy

    >>> doc = MyDoc(id='1')
    >>> doc.o = PickleDummy()
    >>> doc.o
    <PickleDummy [name='ll']>

Store and Retrieve the document::

    >>> _ = doc.store(refresh=True)
    >>> stored_doc = MyDoc.get('1')

The object property provides the correct instance::

    >>> stored_doc.o
    <PickleDummy [name='ll']>

An object property can be set to None::

    >>> doc.o = None
    >>> _ = doc.store()
    >>> stored_doc = MyDoc.get('1')
    >>> stored_doc.o is None
    True


Changing an object which is already assigned to a document property must also
be updated when indexing or updating the database::

    >>> doc = MyDoc(id='2')
    >>> doc.o = PickleDummy()
    >>> doc.o.name = 'new name'
    >>> _ = doc.store(refresh=True)
    >>> stored_doc = MyDoc.get('2')
    >>> stored_doc.o
    <PickleDummy [name=u'new name']>

    >>> doc.o.name = 'changed again'
    >>> _ = doc.store(refresh=True)
    >>> stored_doc = MyDoc.get('2')
    >>> stored_doc is doc
    False
    >>> stored_doc.o
    <PickleDummy [name=u'changed again']>


Object Property Encoding/Decoding
=================================


Objects
-------

The ObjectProperty uses the jsonpickle module to store and retrieve the data.
An object is stored ar the raw jsonpickle string in the `jsonpickle_`
property.

There are some limitations:

    - currently class properties do not show up in the encoded object, only
      properties which are in obj.__dict__ show up
    - properties modified outside the application are not recognized when the
      object is decoded

Some tests showing how endoce/decode works::

    >>> from lovely.esdb.properties import objectproperty

    >>> o1 = PickleDummy()
    >>> o1.p1 = 'p1'
    >>> pprint(objectproperty.encode(o1))
    {'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "p1": "p1"}',
     u'p1': u'p1'}

    >>> o1.name = 'schlag'
    >>> pprint(objectproperty.encode(o1))
    {u'name': u'schlag',
     'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "p1": "p1", "name": "schlag"}',
     u'p1': u'p1'}

    >>> def f():
    ...     pass
    >>> o1.f = f
    >>> pprint(objectproperty.encode(o1))
    {u'f': None,
     u'name': u'schlag',
     'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "p1": "p1", "name": "schlag", "f": {"py/function": "None.f"}}',
     u'p1': u'p1'}

    >>> o1.o = PickleDummy()
    >>> o1.o.d = 42
    >>> data = objectproperty.encode(o1)
    >>> pprint(data)
    {u'f': None,
     u'name': u'schlag',
     u'o': {u'd': 42},
     'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "p1": "p1", "name": "schlag", "o": {"py/object": "lovely.esdb.properties.testing.PickleDummy", "d": 42}, "f": {"py/function": "None.f"}}',
     u'p1': u'p1'}

    >>> import json
    >>> pprint(json.loads(data['object_json_pickle__']))
    {u'f': {u'py/function': u'None.f'},
     u'name': u'schlag',
     u'o': {u'd': 42, u'py/object': u'lovely.esdb.properties.testing.PickleDummy'},
     u'p1': u'p1',
     u'py/object': u'lovely.esdb.properties.testing.PickleDummy'}


datetime objects
----------------

jsonpickle provides the datetime object as `unicode(obj)` but we want to have
it in ISO format.

Datetime without timezone::

    >>> from datetime import datetime
    >>> o = PickleDummy()
    >>> o.dt = datetime(2016, 3, 14, 8, 50, 0, 0)
    >>> pprint(objectproperty.encode(o))
    {u'dt': u'2016-03-14T08:50:00',
     'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "dt": {"py/object": "datetime.datetime", "__reduce__": [{"py/type": "datetime.datetime"}, ["B+ADDggyAAAAAA=="]]}}'}

Datetime with timezone::

    >>> import pytz
    >>> o.dt = datetime(2016, 3, 14, 8, 50, tzinfo=pytz.utc
    ...                ).astimezone(pytz.timezone('Europe/Vienna'))
    >>> pprint(objectproperty.encode(o))
    {u'dt': u'2016-03-14T09:50:00+01:00',
     'object_json_pickle__': '{"py/object": "lovely.esdb.properties.testing.PickleDummy", "dt": {"py/object": "datetime.datetime", "__reduce__": [{"py/type": "datetime.datetime"}, ["B+ADDgkyAAAAAA==", {"py/object": "pytz.tzfile.Europe/Vienna", "py/reduce": [{"py/function": "pytz._p"}, {"py/tuple": ["Europe/Vienna", 3600, 0, "CET"]}, null, null, null]}]]}}'}


Simple Types
------------

It is not possible to use `simple types` to be stored on an object property::

    >>> pprint(objectproperty.encode(1))
    Traceback (most recent call last):
    TypeError: ...

    >>> pprint(objectproperty.encode([1, 2, 'rr']))
    Traceback (most recent call last):
    TypeError: ...

==========================
Elasticsearch Bulk Actions
==========================

A Bulk object can do different actions within one request. Allowed bulk
actions are `index`, `update` and `delete`. Different actions can be mixed in
one bulk request. Different types of documents can also be mixed in one bulk
request.

The Bulk class accepts various kwargs while initialisation which will be
passed to the bulk implementation of the elasticsearch client. For details see
the docs http://elasticsearch-py.readthedocs.org/en/master/helpers.html

Test Setup::

    >>> from lovely.esdb.document import Document, Property

    >>> currentId = 0
    >>> def get_my_id():
    ...     global currentId
    ...     currentId += 1
    ...     return unicode(currentId)

    >>> class MyObj(Document):
    ...     INDEX = 'myobj'
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True, default=get_my_id)
    ...     title = Property(default=u'')
    ...     name = Property(default=u'')

    >>> es_client.indices.create(
    ...     index=MyObj.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "title" : { "type" : "string", "index" : "analyzed" },
    ...                     "name" : { "type" : "string", "index" : "analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

Create a Bulk object::

    >>> from lovely.esdb.document.bulk import Bulk
    >>> b = Bulk(es_client)

Flushing without added actions does not do anything::

    >>> b.flush()

Indexing documents::

    >>> obj1 = MyObj(title="One", name="Hansi")
    >>> obj2 = MyObj(title="Two")
    >>> obj3 = MyObj(title="Three")
    >>> obj4 = MyObj(title="Four")
    >>> b.index(obj1)
    >>> b.index(obj2)
    >>> b.index(obj3)
    >>> b.index(obj4)
    >>> b.flush()
    (4, [])

    >>> MyObj.get(obj1.id).title
    u'One'
    >>> MyObj.get(obj2.id).title
    u'Two'
    >>> MyObj.get(obj3.id).title
    u'Three'
    >>> MyObj.get(obj4.id).title
    u'Four'

Once flushed, no more action are contained by the Bulk object hence a further
flush nothing do::

    >>> len(b.actions)
    0

    >>> b.flush()

Updating documents::

    >>> obj1.title = "updated 1"
    >>> obj2.title = "updated 2"
    >>> b.update(obj1)
    >>> b.update(obj2)
    >>> b.flush()
    (2, [])

    >>> MyObj.get(obj1.id).title
    u'updated 1'
    >>> MyObj.get(obj2.id).title
    u'updated 2'

Updating only specific porperties::

    >>> name_before_update = obj1.name
    >>> obj1.name = u'Hupsi'
    >>> obj1.title = "updated 1 with props"

    >>> b.update(obj1, properties=['title'])
    >>> b.flush()
    (1, [])

    >>> MyObj.get(obj1.id).title
    u'updated 1 with props'
    >>> MyObj.get(obj1.id).name == name_before_update
    True

For conflict resolution the update method supports the keyword argument
`retry_on_conflict` which accepts an integer value indicating how ofter
elasticsearch will retry to update the document in case of a version conflict.
The default value is set to 5::

    >>> b.update(obj1, retry_on_conflict=3)
    >>> b.flush()
    (1, [])

Deleting documents::

    >>> b.delete(obj1)
    >>> b.delete(obj2)
    >>> b.flush()
    (2, [])

    >>> MyObj.get(obj1.id) == None
    True

    >>> MyObj.get(obj2.id) == None
    True

Mixed actions::

    >>> obj5 = MyObj(title="Five")
    >>> b.index(obj5)
    >>> obj3.title = "updated 3"
    >>> b.update(obj3)
    >>> b.delete(obj4)
    >>> b.flush()
    (3, [])

    >>> MyObj.get(obj5.id).title
    u'Five'
    >>> MyObj.get(obj3.id).title
    u'updated 3'
    >>> MyObj.get(obj4.id) == None
    True

Mixed Documents::

    >>> class MySecondObj(Document):
    ...     INDEX = 'mysecondobj'
    ...     ES = es_client
    ...
    ...     id = Property(primary_key=True, default=get_my_id)
    ...     name = Property(default=u'')

    >>> es_client.indices.create(
    ...     index=MySecondObj.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "id" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "name" : { "type" : "string", "index" : "analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

    >>> objA = MyObj(title="Title")
    >>> objB = MySecondObj(name="Hansi")
    >>> b.index(objA)
    >>> b.index(objB)
    >>> b.flush()
    (2, [])

    >>> MyObj.get(objA.id).title
    u'Title'

    >>> MySecondObj.get(objB.id).name
    u'Hansi'

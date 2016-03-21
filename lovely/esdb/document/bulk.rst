==========================
Elasticsearch Bulk Actions
==========================

A Bulk object can do different actions within one request. Allowed bulk
actions are `store`, `delete` and `update_or_create`. Different actions can be
mixed in one bulk request. Different types of documents can also be mixed in
one bulk request.

The Bulk class accepts various kwargs while initialisation which will be
passed to the bulk implementation of the elasticsearch client. For details see
the docs http://elasticsearch-py.readthedocs.org/en/master/helpers.html

Test Setup::

    >>> from lovely.esdb.document import Document
    >>> from lovely.esdb.properties import Property

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

    >>> class MyOtherObj(MyObj):
    ...     pass

Create a Bulk object::

    >>> from lovely.esdb.document.bulk import Bulk
    >>> b = Bulk(es_client)

Flushing without added actions does not do anything::

    >>> b.flush()

Indexing documents::

    >>> obj1 = MyObj(title="One", name="Hansi")
    >>> obj2 = MyObj(title="Two")
    >>> obj3 = MyObj(title="Three")
    >>> obj4 = MyOtherObj(title="Four")
    >>> b.store(obj1)
    >>> b.store(obj2)
    >>> b.store(obj3)
    >>> b.store(obj4)
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

The indexed object `obj4` is of type MyOtherObj inherited from class MyObj.
These two classes are using the same index. The class to use is stored in the
document while indexing an object even using bulk operations::

    >>> type(MyObj.get(obj4.id)) == MyOtherObj
    True

Once flushed, no more action are contained by the Bulk object hence a further
flush nothing do::

    >>> len(b.actions)
    0

    >>> b.flush()

Updating documents::

    >>> obj1.title = "updated 1"
    >>> obj2.title = "updated 2"
    >>> b.store(obj1)
    >>> b.store(obj2)
    >>> b.flush()
    (2, [])

    >>> MyObj.get(obj1.id).title
    u'updated 1'
    >>> MyObj.get(obj2.id).title
    u'updated 2'

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
    >>> b.store(obj5)
    >>> obj3.title = "updated 3"
    >>> b.store(obj3)
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
    ...     key = Property(primary_key=True, default=get_my_id)
    ...     name = Property(default=u'')

    >>> es_client.indices.create(
    ...     index=MySecondObj.INDEX,
    ...     body={
    ...         'settings': {'number_of_shards': 1},
    ...         "mappings" : {
    ...             "default" : {
    ...                 "properties" : {
    ...                     "key" : { "type" : "string", "index" : "not_analyzed" },
    ...                     "name" : { "type" : "string", "index" : "analyzed" }
    ...                 }
    ...             }
    ...         }
    ...     })
    {u'acknowledged': True}

    >>> objA = MyObj(title="Title")
    >>> objB = MySecondObj(name="Hansi")
    >>> b.store(objA)
    >>> b.store(objB)
    >>> b.flush()
    (2, [])

    >>> MyObj.get(objA.id).title
    u'Title'

    >>> MySecondObj.get(objB.key).name
    u'Hansi'


Update or Create Partly defined Documents
=========================================

Modify an existing document without loading it first::

    >>> partA = MyObj(id=obj5.id, name="partA")
    >>> b.update_or_create(partA)

Create a new document for which it is not clear if it already exsits::

    >>> partB = MyObj(id='partB', name="partB")
    >>> b.update_or_create(partB)

    >>> b.flush()
    (2, [])

The updated document::

    >>> pprint(MyObj.get(obj5.id)._values.source)
    {u'db_class__': u'MyObj', u'id': u'5', u'name': u'partA', u'title': u'Five'}

The new document::

    >>> pprint(MyObj.get('partB')._values.source)
    {u'db_class__': u'MyObj', u'id': u'partB', u'name': u'partB', u'title': u''}


Bulk and Lazy Documents
=======================

Lazy documents can also be used with bulks::

    >>> from lovely.esdb.document import LazyDocument
    >>> o = LazyDocument(MyObj(id='lazybulk', name="lazy bulk name"))
    >>> b.store(o)
    >>> b.flush()
    (1, [])
    >>> pprint(MyObj.get('lazybulk')._values.source)
    {u'db_class__': u'MyObj',
     u'id': u'lazybulk',
     u'name': u'lazy bulk name',
     u'title': u''}

    >>> o.title = 'new lazybulk title'
    >>> b.store(o)
    >>> b.flush()
    (1, [])
    >>> pprint(MyObj.get('lazybulk')._values.source)
    {u'db_class__': u'MyObj',
     u'id': u'lazybulk',
     u'name': u'lazy bulk name',
     u'title': u'new lazybulk title'}

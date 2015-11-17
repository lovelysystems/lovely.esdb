==============================
Elasticsearch connection tests
==============================

If the elasticsearch pool is not initialized, an exception is thrown if
``get_es`` is tried to be called::

    >>> get_es()
    Traceback (most recent call last):
    ESDBUninitializedException: Elasticsearch connection pool not initialized.

The hosts of the Crate instance for the test suite are globally available::

    >>> print es_hosts
    ['localhost:19442']

Initialize the elasticsearch pool with a host and settings::

    >>> from lovely.esdb.connection import createESPool
    >>> createESPool(es_hosts, {})

Now an elasticsearch client is returned when ``get_es`` is called::

    >>> client = get_es()
    >>> print client
    <Elasticsearch([{u'host': u'localhost', u'port': 19442}])>

Calling the ``get_es`` method again will return the same client instance::

    >>> print client == get_es()
    True

Calling the ``get_es`` method in a new gevent local thread will return a new
elasticsearch client instance::

    >>> def get_it():
    ...     client2 = get_es()
    ...     print client2 == client
    >>> import gevent
    >>> gevent.joinall([gevent.spawn(get_it)])
    False
import logging

from . import es

log = logging.getLogger(__name__)

es_pool = None


def get_es():
    """A short version to get an elasticsearch client instance.

    The elasticsearch connection pool must have been initialized before this
    can be used.
    """
    if es_pool is None:
        raise es.ESDBUninitializedException()
    return es_pool.get()


def createESPool(hosts, settings):
    """Initialize the elasticsearch connection pool.

    This needs to be called on app initialization.

    Params:

      - ``hosts``: A list of elasticsearch/crate hosts
      - ``settings``: A dictionary with elasticsearch/crate settings
    """
    global es_pool
    es_pool = es.ConnectionPool(hosts, settings)
    log.info('created ES connection pool for %s with settings: "%s"',
             hosts,
             settings)

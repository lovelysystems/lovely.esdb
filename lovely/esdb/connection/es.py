import gevent.local

from elasticsearch import Elasticsearch


class ESDBException(Exception):
    """Base class for ES DB exceptions.
    """


class ESDBUninitializedException(ESDBException):
    """Thrown when the elasticsearch connection pool is not initialized.
    """

    def __init__(self):
        return super(ESDBUninitializedException, self).__init__(
            'Elasticsearch connection pool not initialized.'
        )


class ConnectionPool(object):

    def __init__(self, hosts, settings):
        self.hosts = hosts
        self.settings = settings

    def get(self):
        return _get_es(self.hosts, self.settings)

local = gevent.local.local()


def _get_es(hosts, settings):
    """Return a thread local es client instance"""
    if not hasattr(local, 'es'):
        local.es = Elasticsearch(hosts, **settings)
    return local.es

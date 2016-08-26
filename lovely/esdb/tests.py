import os
import unittest
import doctest
import requests
from pprint import pprint

from crate.testing.layer import CrateLayer
from elasticsearch import Elasticsearch

here = os.path.dirname(__file__)
buildout_dir = os.path.dirname(os.path.dirname(here))

test_dir = os.path.join(here, 'testing')
conf = os.path.join(test_dir, 'testing.ini')

default_app = None
app = None


def crate_path(*parts):
    return os.path.join(buildout_dir, 'parts', 'crate', *parts)

# crate Layer
crate_port = 19442
crate_host = '127.0.0.1:%s' % crate_port
crate_settings = os.path.join(here, 'testing', 'crate.yml')
crash_path = os.path.join(buildout_dir, 'bin', 'crash')
crate_setup_dir = os.path.join(buildout_dir, 'etc', 'crate', 'sql')
crate_cleanup = os.path.join(buildout_dir, 'bin', 'crate_cleanup')
crate_setup = os.path.join(buildout_dir, 'bin', 'crate_setup')


crate_layer = CrateLayer('crate',
                         crate_home=crate_path(),
                         crate_config=crate_settings,
                         crate_exec=crate_path('bin', 'crate'),
                         port=crate_port)


def setUp(test):
    test.globs['pprint'] = pprint
    delete_crate_indexes()
    test.globs['crate_port'] = crate_port
    test.globs['es_client'] = Elasticsearch(['localhost:%s' % crate_port])
    wait_for_cluster()


def tearDown(test):
    pass


def delete_crate_indexes():
    """Deletes the Crate indexes.
    """
    os.system('%s --host http://%s >/dev/null' % (
                crate_cleanup, crate_host))


def wait_for_cluster():
    """Wait for ES cluster to be ready to work.
    """
    healthurl = 'http://%s/_cluster/health' % crate_host
    params = {'wait_for_status': 'yellow',
              'timeout': '300s'}
    res = requests.get(healthurl, params=params)
    assert res.status_code == 200
    health = res.json()
    assert health['status'] != 'red'


def create_suite(testfile,
                 layer=crate_layer,
                 level=None,
                 setUp=setUp,
                 tearDown=tearDown,
                 cls=doctest.DocFileSuite,
                 encoding='utf-8'):
    suite = cls(
        testfile, tearDown=tearDown, setUp=setUp,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        encoding=encoding)
    if layer:
        suite.layer = layer
    if level:
        suite.level = level
    return suite


def test_suite():
    return unittest.TestSuite((
        create_suite('document/README.rst'),
        create_suite('document/document.rst'),
        create_suite('document/lazy.rst'),
        create_suite('document/bulk.rst'),

        create_suite('properties/property.rst'),
        create_suite('properties/relation.rst'),
        create_suite('properties/objectproperty.rst'),

        # the documentation
        create_suite('../../docs/usage.rst'),
        create_suite('../../docs/relation.rst'),
    ))

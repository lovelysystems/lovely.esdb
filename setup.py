import os

from setuptools import setup, find_packages


VERSION = "?"
execfile(os.path.join(os.path.dirname(__file__),
                      'lovely/esdb/__init__.py'))


requires = [
    'gevent',
    'elasticsearch',
    'jsonpickle',
]

setup(
    name='lovely.esdb',
    version=VERSION,
    author='lovelysystems',
    author_email='office@lovelysystems.com',
    packages=find_packages(),
    include_package_data=True,
    extras_require=dict(
          test=[
              'collective.xmltestreport',
              'pytz',
              'crate',
              'requests',
              'lovely.testlayers',
          ],
    ),
    zip_safe=False,
    install_requires=requires,
    test_suite="lovely.esdb",
)

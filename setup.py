import os

from setuptools import setup, find_packages


VERSION = "?"
execfile(os.path.join(os.path.dirname(__file__),
                      'lovely/esdb/__init__.py'))


requires = [
    'gevent',
    'elasticsearch',
    'jsonpickle',
    'python-dateutil',
]

setup(
    name='lovely.esdb',
    version=VERSION,
    description="a simple elasticsearch document mapper",
    author='lovelysystems',
    author_email='office@lovelysystems.com',
    url='http://lovelyesdb.readthedocs.io/en/latest/index.html',
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
        documentation=[
            'sphinx',
        ],
    ),
    zip_safe=False,
    install_requires=requires,
    test_suite="lovely.esdb",
)

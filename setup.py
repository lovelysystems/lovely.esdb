import os

from setuptools import setup, find_packages


def get_version():
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION.txt")
    with open(p) as f:
        return f.read().strip()



requires = [
    'gevent',
    'elasticsearch',
    'jsonpickle',
    'python-dateutil',
]

setup(
    name='lovely.esdb',
    version=get_version(),
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

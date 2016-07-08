===================================================
lovely.esdb: a simple elasticsearch document mapper
===================================================

This package provides a simple elasticsearch document management. Its main
purpose is to map ES documents to python classes with the possibility to
work with raw ES data for simple JSON mappings.


Features
--------

- provide a ``Document`` class for ES documents
- allows property definition (currently untyped)
- ``ObjectProperty`` to be able to store any JSON pickle-able object
- automatic mapping of ES index data to ``Document`` classes
- manage different ``Document`` classes in the same index
- manage bulk operations for ``Documents``
- ``Document`` proxy ``LazyDocument`` for lazy loading

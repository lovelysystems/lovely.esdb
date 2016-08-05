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


License
-------

The MIT License (MIT)
Copyright (c) 2016, Lovely Systems GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

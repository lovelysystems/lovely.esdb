=======================
Changes for lovely.esdb
=======================

unreleased
==========

 - apply default values not in init method but when values are read or written

 - do not initially call default() property methods on reading operations

2015/11/23 0.0.6
================

 - added delete method for documents

2015/11/22 0.0.5
================

 - added more functionallity to the Document class:
   - count
   - refresh

 - added a doc property to "Property"

2015/11/20 0.0.4
================

 - fix handling of default values when preparing the source

2015/11/19 0.0.3
================

 - fix handling of different name of properties in the database and in the
   document

2015/11/19 0.0.2
================

 - property defaults can be provided using a callable

2015/11/18 0.0.1
================

 - initial commit

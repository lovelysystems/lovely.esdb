=======================
Changes for lovely.esdb
=======================

unreleased
==========

 - added scan method

2016/01/19 0.1.1
================

 - bulk updates with conflict resolution

 - updating only initialized properties

 - added Bulk class

2015/12/11 0.1.0
================

 - Document.search now returns the full ES response
   Note: this is a backward incompatibiliy.

2015/12/02 0.0.7
================

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

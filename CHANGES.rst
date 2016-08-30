=======================
Changes for lovely.esdb
=======================

unreleased
==========

 - no longer call __init__ if a document is created from elasticsearch data

2016/08/29 0.3.5
================

 - fixed id lookup

2016/08/29 0.3.4
================

 - extended the relation_dict

2016/08/29 0.3.3
================

 - allow additional properties on relations

2016/08/26 0.3.2
================

 - added relation properties for 1:1 and 1:n relations

2016/08/10 0.3.1
================

 - do not apply None for ObjectProperty if property not found
 - fixed document.get_source for ObjectProperty handling

2016/07/27 0.3.0
================

 - added Document.get_by to build simple terms queries
 - added WITH_INHERITANCE property for the Document class to enable/disable
   the use of the db_class__ property.

2016/07/08 0.2.3
================

 - prepared for pypi
 - updated with readthedocs documentation

2016/03/23 0.2.2
================

 - json pickle datetime and date objects as iso8601 string
   This fixes problems with the jsonpickle package.

2016/03/21 0.2.1
================

 - added lazy documents

 - changed the way how the primary key property is handled in the document

 - allow to set None on object properties

2016/03/16 0.2.0
================

 - added ObjectProperty

 - complete refactoring of the document class

 - added support for multiple classes using the same document index

2016/03/04 0.1.3
================

 - fix: bulk implementation must use `primary_key` property instead of `id`

 - do not allow multiple primary key properties on documents

 - added `primary_key` property to document

2016/02/29 0.1.2
================

 - added possibility to set custom getter/setter on properties

 - do not invoke property setter when loading Document form database

2016/01/19 0.1.1
================

 - bulk updates with conflict resolution

 - updating only initialized properties

 - added Bulk class

2015/12/11 0.1.0
================

 - Document.search now returns the full ES response
   Note: this is a backward incompatibility.

2015/12/02 0.0.7
================

 - apply default values not in init method but when values are read or written

 - do not initially call default() property methods on reading operations

2015/11/23 0.0.6
================

 - added delete method for documents

2015/11/22 0.0.5
================

 - added more functionality to the Document class:
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

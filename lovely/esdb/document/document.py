import copy
import inspect
import json
import jsonpickle

from collections import defaultdict

import elasticsearch.exceptions

from ..properties import Property
from ..properties.relation import RelationBase


DOCUMENTREGISTRY = defaultdict(dict)
DOCUMENT_CLASSES = {}


class DocumentMeta(type):
    """Metaclass for the Document

    Adds the document to a global registry and sets the internal name of the
    `Property` declarations based on the name defined in the class.
    """

    def __init__(cls, name, bases, dct):
        # register the document class
        global DOCUMENTREGISTRY
        if cls.INDEX and cls.DOC_TYPE:
            cls.INDEX_TYPE_NAME = cls.INDEX + "." + cls.DOC_TYPE
            if name in DOCUMENTREGISTRY[cls.INDEX_TYPE_NAME]:
                raise NameError(
                    'Duplicate document name "%s" for index type "%s"' %
                    (name, cls.INDEX_TYPE_NAME)
                )
            DOCUMENTREGISTRY[cls.INDEX_TYPE_NAME][name] = cls
            DOCUMENT_CLASSES[cls.__name__] = cls
        # on all Properties set the name to the class property name if no
        # name was provided for the property
        for name, prop in dct.iteritems():
            if isinstance(prop, Property) and prop.name is None:
                prop.name = name
                if prop.primary_key:
                    if cls._primary_key_name is not None:
                        raise AttributeError(
                            "Multiple primary key properties."
                        )
                    cls._primary_key_name = name
        super(DocumentMeta, cls).__init__(name, bases, dct)


class Document(object):
    """Representation of an elasticsearch document as python object

    A simple document class to provide ORM style access for elasticsearch
    index data.
    """

    __metaclass__ = DocumentMeta

    ES = None

    INDEX = None
    DOC_TYPE = 'default'

    WITH_INHERITANCE = False

    RESERVED_PROPERTIES = set([])

    _values = None
    _meta = None
    _update_properties = None
    _primary_key_name = None

    def __init__(self, **kwargs):
        if self.INDEX is None:
            raise ValueError("No INDEX Provided for class %s!" % (
                                self.__class__.__name__))
        if self.DOC_TYPE is None:
            raise ValueError("No DOC_TYPE Provided for class %s!" % (
                                self.__class__.__name__))
        if 'update_properties' in kwargs:
            self._update_properties = kwargs.pop('update_properties')
        self.init(**kwargs)

    def init(self, **kwargs):
        self._values = DocumentValueManager(self)
        self._meta = {}
        self._prepare_values(**kwargs)
        self._update_meta()

    def store(self, **index_update_kwargs):
        """Store the document

        Here it would be possible to optimze by using an update script.

        Currently we always do a full index because the update API doesn't
        allow to remove properties for dictionaries.
        """
        return self._store_index(**index_update_kwargs)

    def delete(self, **delete_args):
        """Delete an object from elasticsearch
        """
        if self.is_new():
            # document has never been stored
            return
        return self._get_es().delete(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=self.get_primary_key(),
                    **delete_args
                )

    def update_or_create(self, properties=None, **update_kwargs):
        """Update or create the document in elasticsearch

        This will create a new or update an existing document.

        If this is an existing document only the properties defined in
        "update_properties" are updated.

        Special handling for the update:
            ...
        """
        body = self._get_update_or_create_body(properties)
        doc_id = self.get_primary_key()
        return self._get_es().update(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=doc_id,
                    body=body,
                    **update_kwargs
                )

    def is_new(self):
        """checks if this is a `new` document

        A `new` document is a document which was not loaded from the database
        and was never stored.
        """
        return self._meta.get('_id') is None

    @property
    def primary_key(self):
        """Provides the primary key as it is stored in the primary key property
        """
        if self._primary_key_name is None:
            raise AttributeError('No primary key column defined for "%s"' % (
                                                self.__class__.__name__))
        return getattr(self, self._primary_key_name)

    def get_primary_key(self, set_after_read=False):
        """Provides the primary key

        First it looks up `_id` in the meta data and if it is not set the
        primary key property must provide the id.

        set_after_read updates the id in the meta data if it was not already
        set.

        raises AttributeError if no primary key is defined
        """
        if self._meta.get('_id') is not None:
            return self._meta.get('_id')
        value = self.primary_key
        if value and set_after_read:
            self._meta['_id'] = value
        return value

    @property
    def primary_key_name(self):
        return self.__class__._primary_key_name

    def get_source(self):
        """This method returns all initialised properties of the instance.

        If a property has not been initialised yet it's not provided.
        Initialising may happen via keywords in the constructor or via
        setters.
        """
        res = {}
        for name, prop in self._properties():
            if self._values.exists(prop.name):
                res[name] = self._values.get(prop.name)
        return json.loads(jsonpickle.encode(res, unpicklable=False))

    @classmethod
    def get(cls, id):
        """Get an object with a specific id from elasticsearch
        """
        try:
            res = cls._get_es().get(index=cls.INDEX,
                                    doc_type=cls.DOC_TYPE,
                                    id=id,
                                   )
        except elasticsearch.exceptions.ElasticsearchException:
            return None
        return cls.from_raw_es_data(res)

    @classmethod
    def mget(cls, ids):
        """Get multiple objects from elasticsearch
        """
        if not ids:
            return []
        docs = cls._get_es().mget(index=cls.INDEX,
                                  doc_type=cls.DOC_TYPE,
                                  body={'ids': ids},
                                 ).get('docs')
        result = []
        for doc in docs:
            if 'error' in doc or not doc.get('found', False):
                result.append(None)
                continue
            result.append(cls.from_raw_es_data(doc))
        return result

    @classmethod
    def get_by(cls, prop, value, offset=0, size=1):
        """Get an object using a query on a specific property

        prop must be one of the properties defined in the Document.
        If value is a list type a terms query is used.
        """
        query_type = isinstance(value, (list, tuple)) and 'terms' or 'term'
        body = {
            "query": {
                query_type: {
                    prop.get_query_name(): value
                }
            },
            "size": size,
            "from": offset,
        }
        hits = cls.search(body)
        return hits['hits']['hits']

    @classmethod
    def search(cls, body, resolve_hits=True):
        """Retrieve objects from elasticsearch via a search query

        Returns the ES search result. If resolve_hits is set to true the hits
        are converted to Documents.
        """
        docs = cls._get_es().search(index=cls.INDEX,
                                    doc_type=cls.DOC_TYPE,
                                    body=body
                                   )
        if resolve_hits:
            data = []
            for d in docs['hits']['hits']:
                data.append(cls.from_raw_es_data(d))
            docs['hits']['hits'] = data
        return docs

    @classmethod
    def count(cls, body=None, **count_args):
        """Get the count of data stored in elasticsearch.

        It's possible to provide a query with the ``body`` argument.
        """
        res = cls._get_es().count(
            index=cls.INDEX,
            doc_type=cls.DOC_TYPE,
            body=body,
            **count_args
        )
        return res['count']

    @classmethod
    def refresh(cls, **refresh_args):
        """Refresh the index for this document
        """
        return cls._get_es().indices.refresh(index=cls.INDEX, **refresh_args)

    @classmethod
    def from_raw_es_data(cls, raw):
        """Setup the document from raw elasticsearch data

        raw must contain the data returned from ES which contains the
        "_source" property.
        """
        class_name = raw.get('_source', {}).get('db_class__')
        klass = DOCUMENTREGISTRY[cls.INDEX_TYPE_NAME].get(class_name, cls)
        obj = klass.__new__(klass)
        obj.init()
        obj._values.source = raw['_source']
        obj._update_meta(raw['_id'], raw.get('_version'))
        return obj

    @staticmethod
    def resolve_document_name(name):
        return DOCUMENT_CLASSES[name]

    def _store_index(self, **index_kwargs):
        """Write the current object to elasticsearch

        Used in the `store` method if this is a new document.
        After calling this method the document is no longer a new document.
        """
        body = self._get_store_index_body()
        doc_id = self.get_primary_key()
        return self._get_es().index(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=doc_id,
                    body=body,
                    **index_kwargs
                )

    def _get_store_index_body(self):
        """Create the body data needed to index a document

        This method is also used in the bulk implementation.
        """
        self._apply_properties()
        self._apply_defaults()
        # get_primary_key is called to make sure the id is copied to the
        # metadata because from now on the document is no longer a new
        # document.
        self.get_primary_key(set_after_read=True)
        return self._values.source_for_index(update_source=True)

    def _store_update(self, **update_kwargs):
        """Update the document if there are changes
        """
        doc = self._get_store_update_doc()
        if not doc:
            # no changes found
            return None
        body = {
            "doc": doc
        }
        doc_id = self.get_primary_key()
        return self._get_es().update(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=doc_id,
                    body=body,
                    **update_kwargs
                )

    def _get_store_update_doc(self):
        """Create the update document

        The result is a dict containing all the changed properties.
        If the result is an emtpy dict no update is needed.

        This method is also used in the bulk implementation.
        """
        self._apply_properties()
        self.get_primary_key()
        return self._values.source_for_update(update_source=True)

    def _get_update_or_create_body(self, properties=None):
        """Create the update/upsert body

        Used in update_or_create to update a partly created document.

        This method is also used in the bulk implementation.
        """
        self._apply_properties()
        self.get_primary_key()
        values = self._values.changed
        if properties is None:
            # use the update properties defined for the instance
            properties = self._update_properties
        if properties is not None:
            filtered = {}
            for name in properties:
                if hasattr(self.__class__, name):
                    prop = getattr(self.__class__, name)
                    filtered[prop.name] = values[prop.name]
            values = filtered
        return {
            "doc": values,
            "upsert": self._get_source_with_defaults()
        }

    def _get_source_with_defaults(self):
        """Return a dict representation of this document

        *All* properties are included. If one property hasn't been initialised
        yet the properties default value will be used.
        """
        for (name, prop) in self._properties():
            getattr(self, name)
        return self._values.source_for_index()

    def _prepare_values(self, **kwargs):
        for (name, prop) in self._properties():
            if name in kwargs:
                setattr(self, name, kwargs[name])
        for (name, prop) in self._get_relation_properties():
            if name in kwargs:
                setattr(self, name, kwargs[name])

    def _apply_properties(self):
        """call _apply on all properties

        calls _apply on all properties to give the properties a chance to
        update _source. This is needed for properties such as the
        PickleProperty which handles an object reference.
        """
        for (name, prop) in self._properties():
            prop._apply(self)

    def _apply_defaults(self):
        """Apply default values for all missing properties
        """
        source = self._values.source_for_index()
        for (name, prop) in self._properties():
            if prop.name not in source:
                # reading the property will set the default
                getattr(self, name)

    def _update_meta(self, _id=None, _version=None, **kwargs):
        if self._meta is None:
            self._meta = {}
        if not self._meta.get('_id') or _id:
            self._meta['_id'] = _id
        self._meta['_version'] = _version
        self._meta['_index'] = self.INDEX
        self._meta['_type'] = self.DOC_TYPE
        self._meta.update(kwargs)

    def _properties(self):
        """yield the properties of the document
        """
        def isProperty(obj):
            return isinstance(obj, Property)
        for (name, prop) in inspect.getmembers(self.__class__, isProperty):
            if name not in self.RESERVED_PROPERTIES:
                yield (name, prop)

    def _get_relation_properties(self):
        """yield the relations of the document
        """
        def isRelation(obj):
            return isinstance(obj, RelationBase)
        for (name, prop) in inspect.getmembers(self.__class__, isRelation):
            if name not in self.RESERVED_PROPERTIES:
                yield (name, prop)

    @classmethod
    def _get_es(cls):
        if cls.ES is None:
            raise ValueError('No ES client is set on class %s' % cls.__name__)
        return cls.ES


class DocumentValueManager(object):
    """Manages the stores for the property values

    A manager instance is used by the properties of a document to manage the
    values.
    """

    def __init__(self, doc):
        self.doc = doc
        self.source = {}
        self.changed = {}
        self.default = {}
        self.property_cache = {}

    def source_for_index(self, update_source=True):
        """Build the source which contains all properties for indexing
        """
        source = copy.deepcopy(self.default)
        source.update(copy.deepcopy(self.source))
        source.update(copy.deepcopy(self.changed))
        if self.doc and self.doc.WITH_INHERITANCE:
            source['db_class__'] = self.doc.__class__.__name__
        if update_source:
            self.source = copy.deepcopy(source)
            self.changed = {}
            self.default = {}
        return source

    def source_for_update(self, update_source=True):
        """Build the source for updating

        Will only contain changed properties and new defaults.
        """
        source = copy.deepcopy(self.default)
        source.update(copy.deepcopy(self.changed))
        if update_source:
            self.source.update(copy.deepcopy(source))
            self.changed = {}
            self.default = {}
        return source

    def get(self, name):
        """Provide the value for a property

        name must be the name which is used in the database not in the python
        class.
        """
        if name in self.property_cache:
            return self.property_cache[name]
        if name in self.changed:
            return self.changed[name]
        if name in self.source:
            return self.source[name]
        return self.default[name]

    def exists(self, name):
        """Tests if the value for a property is defined
        """
        return (name in self.property_cache
                or name in self.changed
                or name in self.source
                or name in self.default)

    def delete(self, name):
        """Delete the value from all stores
        """
        if name in self.property_cache:
            del self.property_cache[name]
        if name in self.changed:
            del self.changed[name]
        if name in self.source:
            del self.source[name]
        if name in self.default:
            del self.default[name]

    def raw_source(self, stripped=True):
        """Provides the current known source

        It is a representation of the object in the database but the internal
        metadata is stripped away.
        """
        source = self.source_for_index(update_source=False)
        if stripped:
            def strip(obj):
                if isinstance(obj, dict):
                    for k, v in list(obj.iteritems()):
                        if k.endswith('__'):
                            del obj[k]
                        else:
                            strip(v)
                elif isinstance(obj, (list, tuple)):
                    for v in obj:
                        strip(v)
            strip(source)
        return source

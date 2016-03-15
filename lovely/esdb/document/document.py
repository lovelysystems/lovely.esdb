import inspect
from collections import defaultdict

import elasticsearch.exceptions

from ..properties import Property


DOCUMENTREGISTRY = defaultdict(dict)


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
            # on all Properties set the name to the class property name if no
            # name was provided for the property
            for name, prop in dct.iteritems():
                if isinstance(prop, Property) and prop.name is None:
                    prop.name = name
                    if prop.primary_key:
                        if cls._primary_key_property is not None:
                            raise AttributeError(
                                "Multiple primary key properties."
                            )
                        cls._primary_key_property = prop
        super(DocumentMeta, cls).__init__(name, bases, dct)


class Document(object):
    """Representation of an elasticsearch document as python object
    """

    __metaclass__ = DocumentMeta

    ES = None

    INDEX = None
    DOC_TYPE = 'default'

    RESERVED_PROPERTIES = set(['_primary_key_property'])

    _values = None
    _meta = None
    _primary_key_property = None

    def __init__(self, **kwargs):
        if self.INDEX is None:
            raise ValueError("No INDEX Provided for class %s!" % (
                                self.__class__.__name__))
        if self.DOC_TYPE is None:
            raise ValueError("No DOC_TYPE Provided for class %s!" % (
                                self.__class__.__name__))
        self._values = DocumentValueManager(self)
        self._meta = {}
        self._prepare_values(**kwargs)
        self._update_meta()

    @classmethod
    def from_raw_es_data(cls, raw):
        """Setup the document from raw elasticsearch data

        raw must contain the data returned from ES which contains the
        "_source" property.
        """
        class_name = raw.get('_source', {}).get('db_class_')
        klass = DOCUMENTREGISTRY[cls.INDEX_TYPE_NAME].get(class_name, cls)
        obj = klass()
        obj._values.source = raw['_source']
        obj._update_meta(raw['_id'], raw.get('_version'))
        return obj

    def store(self, **index_update_kwargs):
        """Store the doucument

        If this is an existing document an update is done otherwise index is
        used to store the document.
        """
        if self.is_new():
            return self._store_index(**index_update_kwargs)
        else:
            return self._store_update(**index_update_kwargs)

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
        return [d['found'] and cls.from_raw_es_data(d) or None for d in docs]

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

    def is_new(self):
        """checks if this is a `new` document

        A `new` document is a document which was not loaded from the database
        and was never stored.
        """
        return self._meta.get('_id') is None

    @property
    def primary_key(self):
        if self._primary_key_property is None:
            raise AttributeError("No primary key column defined")
        return self._primary_key_property

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

    def _store_index(self, **index_kwargs):
        """Write the current object to elasticsearch
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
        body = self._get_store_update_body()
        if not body:
            # no changes found
            return None
        doc_id = self.get_primary_key()
        return self._get_es().update(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=doc_id,
                    body=body,
                    **update_kwargs
                )

    def _get_store_update_body(self):
        self._apply_properties()
        self.get_primary_key()
        return {
            "doc": self._values.source_for_update(update_source=True)
        }

    def _get_update_or_create_body(self, properties=None):
        self._apply_properties()
        self.get_primary_key()
        values = self._values.changed
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
        res = self._values.source_for_index()
        return res

    def _prepare_values(self, **kwargs):
        for (name, prop) in self._properties():
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

    @classmethod
    def _get_es(cls):
        if cls.ES is None:
            raise ValueError('No ES client is set on class %s' % cls.__name__)
        return cls.ES


class DocumentValueManager(object):
    """Manages the stores for the property values
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
        source = {}
        source.update(self.default)
        source.update(self.source)
        source.update(self.changed)
        source['db_class_'] = self.doc.__class__.__name__
        if update_source:
            self.source = source
            self.changed = {}
            self.default = {}
            self.properties = {}
        return source

    def source_for_update(self, update_source=True):
        """Build the source for updating

        Will only contain changed properties and new defaults.
        """
        source = {}
        source.update(self.default)
        source.update(self.changed)
        if update_source:
            self.source.update(source)
            self.changed = {}
            self.default = {}
            self.properties = {}
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
        if name in self.property_cache:
            del self.property_cache[name]
        if name in self.changed:
            del self.changed[name]
        if name in self.source:
            del self.source[name]
        if name in self.default:
            del self.default[name]

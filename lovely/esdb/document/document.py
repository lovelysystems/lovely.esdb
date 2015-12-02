import inspect

import elasticsearch.exceptions

from .property import Property


DocumentRegistry = {}


class DocumentMeta(type):
    """Metaclass for the Document

    Adds the document to a global registry and sets the internal name of the
    `Property` declarations based on the name defined in the class.
    """

    def __init__(cls, name, bases, dct):
        # register the document class
        global DocumentRegistry
        if name in DocumentRegistry:
            raise NameError('Duplicate document name: %s' % name)
        DocumentRegistry[name] = cls
        # on all Properties set the name to the class property name if no name
        # was provided for the property
        for name, prop in dct.iteritems():
            if isinstance(prop, Property) and prop.name is None:
                prop.name = name
        super(DocumentMeta, cls).__init__(name, bases, dct)


class Document(object):
    """Representation of an elasticsearch document as python Object
    """

    __metaclass__ = DocumentMeta

    ES = None

    INDEX = None
    DOC_TYPE = 'default'
    ROUTING = None

    _source = None
    _meta = None
    _update_properties = None

    def __init__(self, **kwargs):
        if self.INDEX is None:
            raise ValueError("No INDEX Provided for class %s!" % (
                                self.__class__.__name__))
        if self.DOC_TYPE is None:
            raise ValueError("No DOC_TYPE Provided for class %s!" % (
                                self.__class__.__name__))
        if 'update_properties' in kwargs:
            self._update_properties = kwargs.pop('update_properties')
        else:
            self._update_properties = [name for name, p in self._properties()]
        self._source = {}
        self._meta = {}
        self._prepare_source(**kwargs)
        self._update_meta()

    @classmethod
    def from_raw_es_data(cls, raw):
        """Setup the document from raw elasticsearch data

        raw must contain the data returned from ES which contains the
        "_source" property.
        """
        obj = cls(**raw['_source'])
        obj._update_meta(raw['_id'], raw.get('_version'))
        return obj

    def index(self, **index_args):
        """Write the current object to elasticsearch
        """
        self._apply_defaults()
        return self._get_es().index(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=self._meta['_id'],
                    body=self._source,
                    **index_args
                )

    def update(self, properties=None, **update_args):
        """Store the updated document in elasticsearch

        This will create a new or update an existing document.

        If this is an existing document only the properties defined in
        "update_properties" are updated.
        """
        update_values = {}

        self._apply_defaults()
        if properties is None:
            properties = self._update_properties
        for (name, prop) in self._properties():
            if name in properties:
                update_values[prop.name] = getattr(self, name)
        body = {
            "doc": update_values,
            "upsert": self._source
        }
        return self._get_es().update(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=self._meta['_id'],
                    body=body,
                    **update_args
                )

    def delete(self, **delete_args):
        """Delete an object from elasticsearch
        """
        return self._get_es().delete(
                    index=self._meta['_index'],
                    doc_type=self._meta['_type'],
                    id=self._meta['_id'],
                    **delete_args
                )

    @classmethod
    def get(cls, id):
        """Get an object with a specific primary key from elasticsearch
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
    def search(cls, body):
        """Retrieve objects from elasticsearch via a search query
        """
        docs = cls._get_es().search(index=cls.INDEX,
                                    doc_type=cls.DOC_TYPE,
                                    body=body
                                   )
        return [
            (cls.from_raw_es_data(d), d['_score'])
            for d in docs['hits']['hits']
        ]

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

    def get_source(self):
        """This method returns all initialized properties of the instance.

        If a property has not been initialized yet it's not provided.
        Initializing may happen via keywords in the constructor, via setters
        or via getters.
        """
        res = {}
        for name, prop in self._properties():
            if prop.name in self._source:
                res[name] = self._source[prop.name]
        return res

    def _prepare_source(self, **kwargs):
        for (name, prop) in self._properties():
            if prop.name in kwargs:
                setattr(self, name, kwargs[prop.name])

    def _apply_defaults(self):
        """Apply default values to all uninitialized properties
        """
        for (name, prop) in self._properties():
            if prop.name not in self._source:
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
        for prop in inspect.getmembers(self.__class__, isProperty):
            yield prop

    @classmethod
    def _get_es(cls):
        if cls.ES is None:
            raise ValueError('No ES client is set on class %s' % cls.__name__)
        return cls.ES

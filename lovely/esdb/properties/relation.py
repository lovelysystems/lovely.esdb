import copy


class RelationBase(object):
    """Used as a marker for relation classes
    """


class RelationResolver(object):
    """Resolve relations

    Instances of this class are returned when reading from a Relation.

    The resolver must be called to get the related document.
    The resolver manages a cache so multiple calls are always returning the
    same instance of the related document.
    """

    def __init__(self, instance, relation, transformer, cache=None):
        self.instance = instance
        self.relation = relation
        self.transformer = transformer
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache
        self.cacheKey = None

    @property
    def id(self):
        data = self.relation.get_local_data(self.instance)
        if isinstance(data, dict):
            return data["id"]
        return data

    @property
    def remote(self):
        return self.relation.remote_class

    @property
    def relation_dict(self):
        data = self.relation.get_local_data(self.instance)
        if isinstance(data, dict):
            item = copy.deepcopy(data)
        else:
            item = {"id": data}
        item['class'] = self.remote.__name__
        return item

    def __call__(self):
        """Calling the resolver provides the related document
        """
        remoteData = self._get_local_data()
        remoteId = self.transformer.getId(remoteData)
        cacheKey = self.cacheKey
        if (cacheKey not in self.cache
            or self.cache[cacheKey].get('for', object) != remoteId
           ):
            if remoteId is None:
                doc = None
            else:
                # get the document from the store
                doc = self.relation.remote_class.get(remoteId)
            self.cache[cacheKey] = {
                'for': remoteId,
                'doc': doc
            }
        return self.cache[cacheKey]['doc']

    def _get_local_data(self):
        return self.relation.get_local_data(self.instance)

    def __repr__(self):
        return '<%s %s[%s]>' % (
            self.__class__.__name__,
            self.relation.remote_class.__name__,
            self.relation.get_local_data(self.instance))


class LocalRelation(RelationBase):
    """A 1:1 relation property type for documents

    The relation stores the remote id in a property of the document.
    """

    _transformer = None

    def __init__(self,
                 local,
                 remote,
                 relationProperties=None,
                 doc=u''
                ):
        self._local_path = local.split('.')
        self._remote, self._remote_primary = remote.split('.', 1)
        self.relationProperties = copy.deepcopy(relationProperties)
        self.doc = doc
        self._setter = lambda doc, value: value

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return RelationResolver(local, self, self.transformer())

    def __set__(self, local, remote):
        remote = self._setter(local, remote)
        if remote is None:
            self.del_local_data(local)
        else:
            self.set_local_data(local, remote)

    def setter(self, setter):
        """allows to set a setter function

        When a value is read from a `Property` this is the first method
        called with the value.

        This can be used as a decorator:
            class MyDoc(Document):
                ...
                a = Relation(...)

                @a.setter
                def a_setter(self, value):
                    return value.lower()
        """
        self._setter = setter

    def get_query_name(self):
        return '.'.join(self._local_path[1:])

    def get_local_data(self, doc):
        """Provide the property data stored on the document
        """
        rel = getattr(doc, self._local_path[0])
        if rel is None or len(self._local_path) == 1:
            return rel
        for part in self._local_path[1:-1]:
            if part not in rel:
                rel = {}
                break
            rel = rel[part]
        return rel.get(self._local_path[-1])

    def set_local_data(self, doc, value):
        current = self.get_local_data(doc)
        value = self.transformer()(doc, current, value)
        rel = getattr(doc, self._local_path[0])
        if len(self._local_path) == 1:
            # store directly on the document property
            setattr(doc, self._local_path[0], value)
            return
        if rel is None:
            rel = {}
        data = rel
        # advance to the dict which contains the local data
        for part in self._local_path[1:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[self._local_path[-1]] = value
        setattr(doc, self._local_path[0], rel)

    def del_local_data(self, doc):
        rel = getattr(doc, self._local_path[0])
        if len(self._local_path) == 1:
            setattr(doc, self._local_path[0], None)
            return
        # advance to the dict which contains the local data
        data = rel
        for part in self._local_path[1:-1]:
            if part not in data:
                # path is not available: abort
                data = None
                break
            data = data[part]
        if data is not None:
            if self._local_path[-1] in data:
                del data[self._local_path[-1]]
            setattr(doc, self._local_path[0], rel)

    @property
    def remote_class(self):
        from ..document import Document
        return Document.resolve_document_name(self._remote)

    def transformer(self):
        if self._transformer is None:
            if self.relationProperties is not None:
                self.relationProperties["id"] = None
                self._transformer = RelationDictTransformer(
                                        self, self.relationProperties)
            else:
                self._transformer = RelationIdTransformer(self)
        return self._transformer


class ListRelationResolver(object):
    """Resolve a list of relations
    """

    def __init__(self, instance, relation, transformer, cache=None):
        self.instance = instance
        self.relation = relation
        self.transformer = transformer
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache

    @property
    def remote(self):
        return self.relation.remote_class

    @property
    def relation_dict(self):
        return [d.relation_dict for d in self]

    def __getitem__(self, idx):
        return ListItemRelationResolver(self.instance,
                                        self.relation,
                                        idx,
                                        self.transformer,
                                        self.cache)

    def __iter__(self):

        class ResolverIterator(object):

            def __init__(self, resolver):
                self.resolver = resolver
                self.offset = 0
                self.maxIter = len(
                    self.resolver.relation.get_local_data(
                                            self.resolver.instance))

            def next(self):
                if self.offset >= self.maxIter:
                    raise StopIteration
                self.offset += 1
                return ListItemRelationResolver(self.resolver.instance,
                                                self.resolver.relation,
                                                self.offset - 1,
                                                self.resolver.transformer,
                                                self.resolver.cache)
        return ResolverIterator(self)

    def __repr__(self):
        return '<%s %s(%r)>' % (
            self.__class__.__name__,
            self.relation.remote_class.__name__,
            self.relation.get_local_data(self.instance))


class ListItemRelationResolver(RelationResolver):
    """Resolve an item from a list relation
    """

    def __init__(self, instance, relation, idx, transformer, cache=None):
        super(ListItemRelationResolver, self).__init__(
                                        instance, relation, transformer, cache)
        self.idx = idx
        self.cacheKey = idx

    @property
    def id(self):
        data = self.relation.get_local_data(self.instance)[self.idx]
        if isinstance(data, dict):
            return data["id"]
        return data

    @property
    def relation_dict(self):
        data = self.relation.get_local_data(self.instance)[self.idx]
        if isinstance(data, dict):
            item = copy.deepcopy(data)
        else:
            item = {"id": data}
        item['class'] = self.remote.__name__
        return item

    def __repr__(self):
        return '<%s[%s] %s[%s]>' % (
            self.__class__.__name__,
            self.idx,
            self.relation.remote_class.__name__,
            self.relation.get_local_data(self.instance)[self.idx])

    def _get_local_data(self):
        return self.relation.get_local_data(self.instance)[self.idx]


class RelationDataTransformer(object):

    def __init__(self, relation):
        self.relation = relation

    def getId(self, value):
        return value


class RelationNullTransformer(RelationDataTransformer):

    def __call__(self, doc, current, value):
        return value


class RelationIdTransformer(RelationDataTransformer):

    def __call__(self, doc, current, value):
        data = value
        if isinstance(value, self.relation.remote_class):
            data = value.id
        elif isinstance(value, dict):
            data = value['id']
        return data


class RelationDictTransformer(RelationDataTransformer):

    def __init__(self, relation, relationProperties):
        self.relationProperties = relationProperties
        super(RelationDictTransformer, self).__init__(relation)

    def getId(self, value):
        return (value or {}).get('id')

    def __call__(self, doc, current, value):
        data = current
        if data is None:
            # None or an empty dict will use the default relation properties
            # as default.
            data = copy.deepcopy(self.relationProperties)
        if isinstance(value, self.relation.remote_class):
            data['id'] = value.id
        elif isinstance(value, dict):
            for k, default in self.relationProperties.iteritems():
                if k in value:
                    data[k] = value[k]
        else:
            data['id'] = value
        return copy.deepcopy(data)


class LocalOne2NRelation(LocalRelation):
    """A 1:n relation property type for documents

    The relations are stored locally in a list containing the reference data.
    """

    def __init__(self,
                 local,
                 remote,
                 relationProperties=None,
                 doc=u''
                ):
        super(LocalOne2NRelation, self).__init__(local,
                                                 remote,
                                                 relationProperties,
                                                 doc)
        self.elementTransformer = self.transformer()
        self._transformer = RelationNullTransformer(None)

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return ListRelationResolver(local, self, self.elementTransformer)

    def __set__(self, local, remote):
        remote = self._setter(local, remote)
        data = []
        for doc in remote:
            data.append(self.elementTransformer(local, None, doc))
        self.set_local_data(local, data)

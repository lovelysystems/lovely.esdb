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

    def __init__(self, instance, relation, cache=None):
        self.instance = instance
        self.relation = relation
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache

    @property
    def id(self):
        return self.relation.get_local_data(self.instance)

    @property
    def remote(self):
        return self.relation.remote_class

    @property
    def relation_dict(self):
        return {
            'id': self.id,
            'class': self.remote.__name__
        }

    def __call__(self):
        """Calling the resolver provides the related document
        """
        remoteData = self._get_local_data()
        remoteId = self.relation.transformer().getId(remoteData)
        if (None not in self.cache
            or self.cache[None].get('for', object) != remoteId
           ):
            if remoteId is None:
                doc = None
            else:
                # get the document from the store
                doc = self.relation.remote_class.get(remoteId)
            self.cache[None] = {
                'for': remoteId,
                'doc': doc
            }
        return self.cache[None]['doc']

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

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return RelationResolver(local, self)

    def __set__(self, local, remote):
        if remote is None:
            self.del_local_data(local)
        else:
            self.set_local_data(local, remote)

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

    def __init__(self, instance, relation, cache=None):
        self.instance = instance
        self.relation = relation
        if cache is None:
            self.cache = {}
        else:
            self.cache = cache

    @property
    def remote(self):
        return self.relation.remote_class

    @property
    def relation_dict(self):
        data = self.relation.get_local_data(self.instance)
        return [
            {
                'id': d,
                'class': self.remote.__name__
            }
            for d in data]

    def __getitem__(self, idx):
        return ListItemRelationResolver(self.instance,
                                        self.relation,
                                        idx,
                                        self.cache)

    def __repr__(self):
        return '<%s %s(%r)>' % (
            self.__class__.__name__,
            self.relation.remote_class.__name__,
            self.relation.get_local_data(self.instance))


class ListItemRelationResolver(RelationResolver):
    """Resolve an item from a list relation
    """

    def __init__(self, instance, relation, idx, cache=None):
        super(ListItemRelationResolver, self).__init__(
                                        instance, relation, cache)
        self.idx = idx

    @property
    def id(self):
        return self.relation.get_local_data(self.instance)[self.idx]

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
        return value.get('id')

    def __call__(self, doc, current, value):
        data = current
        if data is None:
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
        super(LocalOne2NRelation, self).__init__(local, remote, relationProperties, doc)
        self.elementTransformer = self.transformer()
        self._transformer =RelationNullTransformer(None)


    def __get__(self, local, cls=None):
        if local is None:
            return self
        return ListRelationResolver(local, self)

    def __set__(self, local, remote):
        data = []
        for doc in remote:
            data.append(self.elementTransformer(local, None, doc))
        self.set_local_data(local, data)

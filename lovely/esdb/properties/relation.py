

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
        remote_id = self._get_local_data()
        if (None not in self.cache
            or self.cache[None].get('for', object) != remote_id
           ):
            if remote_id is None:
                doc = None
            else:
                # get the document from the store
                doc = self.relation.remote_class.get(remote_id)
            self.cache[None] = {
                'for': remote_id,
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

    def __init__(self,
                 local,
                 remote,
                 doc=u''
                ):
        self._local_path = local.split('.')
        self._remote, self._remote_primary = remote.split('.', 1)
        self.doc = doc

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return RelationResolver(local, self)

    def __set__(self, local, remote):
        if remote is None:
            self.del_local_data(local)
        else:
            data = remote
            if isinstance(remote, self.remote_class):
                data = remote.id
            elif isinstance(remote, dict):
                data = remote['id']
            self.set_local_data(local, data)

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
                rel[part] = {}
            rel = rel[part]
        return rel.get(self._local_path[-1])

    def set_local_data(self, doc, value):
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


class LocalOne2NRelation(LocalRelation):
    """A 1:n relation property type for documents

    The relations are stored locally in a list containing the referenced ids.
    """

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return ListRelationResolver(local, self)

    def __set__(self, local, remote):
        data = []
        for doc in remote:
            if isinstance(doc, self.remote_class):
                data.append(doc.id)
            elif isinstance(doc, dict):
                data.append(doc['id'])
            else:
                data.append(doc)
        self.set_local_data(local, data)

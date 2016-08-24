

class Relation(object):
    """A relation property type for documents

    A relation property must be assigned to a document property which must
    contain an object. This object can contain anything. The relation uses the
    'id' property to manage the relation.

    """

    _remote_class_cache = None

    _resolved = object
    _resolved_for = object

    def __init__(self,
                 local,
                 remote
                ):
        self._local, self._local_relation_name = local.split('.', 1)
        self._remote, self._remote_primary = remote.split('.', 1)

    def __get__(self, local, cls=None):
        if local is None:
            return self
        return RelationResolver(local, self)

    def __set__(self, local, remote):
        rel = getattr(local, self._local)
        if rel is None:
            rel = {}
        if remote is None:
            if self._local_relation_name in rel:
                del rel[self._local_relation_name]
        else:
            if isinstance(remote, self._remote_class):
                rel[self._local_relation_name] = remote.id
            elif isinstance(remote, dict):
                rel[self._local_relation_name] = remote.get(
                                                    self._remote_primary)
            else:
                rel[self._local_relation_name] = remote
        setattr(local, self._local, rel)

    def remote_id(self, doc):
        rel = getattr(doc, self._local)
        if rel is None or rel.get(self._local_relation_name) is None:
            return None
        return rel.get(self._local_relation_name)

    @property
    def _remote_class(self):
        if self._remote_class_cache is None:
            if isinstance(self._remote, basestring):
                # resolve from the document name to the document class
                from ..document import Document
                self._remote_class_cache = Document.resolve_document_name(
                                                                self._remote)
            else:
                self._remote_class_cache = self._remote
        return self._remote_class_cache


class RelationResolver(object):
    """Resolve relations

    Instances of this class are returned when reading from a Relation.

    The resolver must be called to get the related document.
    The resolver manages a cache so multiple calls are always returning the
    same instance of the related document.
    """

    def __init__(self, instance, relation):
        self.instance = instance
        self.relation = relation

    @property
    def id(self):
        return self.relation.remote_id(self.instance)

    @property
    def remote(self):
        return self.relation._remote_class

    def __call__(self):
        """Calling the resolver provides the related document
        """
        remote_id = self.relation.remote_id(self.instance)
        if (self.relation._resolved == object
            or self.relation._resolved_for != remote_id
           ):
            if remote_id is None:
                self.relation._resolved = None
            else:
                # get the document from the store
                self.relation._resolved = \
                        self.relation._remote_class.get(remote_id)
            self.relation._resolved_for = remote_id
        return self.relation._resolved

    def __repr__(self):
        return '<%s %s[%s]>' % (self.__class__.__name__,
                                self.relation._remote_class.__name__,
                                self.relation.remote_id(self.instance))

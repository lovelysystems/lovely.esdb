from .document import Document


class LazyDocument(object):
    """Handle lazy loading of documents

    Modified from
       http://code.activestate.com/recipes/578014-lazy-load-object-proxying/
    """
    __slots__ = ["_doc_class",
                 "_doc_primary_key",
                 "_doc_properties",
                 "_doc_ref",
                 "__weakref__"]

    def __init__(self, doc_cls, primary_key=None, **properties):
        document = None
        if isinstance(doc_cls, Document):
            document = doc_cls
            doc_cls = document.__class__
        object.__setattr__(self, "_doc_class", doc_cls)
        object.__setattr__(self, "_doc_primary_key", primary_key)
        object.__setattr__(self, "_doc_properties", properties)
        object.__setattr__(self, "_doc_ref", document)

    def _doc_resolver(self):
        """Provides the referenced document

        Returns the already loaded document or loads the document.
        """
        return (object.__getattribute__(self, "_doc_ref")
                or object.__getattribute__(self, "_doc_loader")()
               )

    def _doc_loader(self):
        """Load a document based on the primary key
        """
        pk = object.__getattribute__(self, "_doc_primary_key")
        doc = object.__getattribute__(self, "_doc_class").get(pk)
        object.__setattr__(self, "_doc_ref", doc)
        if doc is not None:
            props = object.__getattribute__(self, "_doc_properties")
            for k, v in props.iteritems():
                setattr(doc, k, v)
        return doc

    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        """Read an attribute from the document

        Primary key handling:
            if the document is not already loaded the primary key is provided
            from the proxy instance instead of loading the document.
        """
        doc = object.__getattribute__(self, "_doc_ref")
        if doc is None:
            # the document is not loaded, if this is the primary key, provide
            # it from self.
            pk_name = getattr(object.__getattribute__(self, "_doc_class"),
                              '_primary_key_name')
            if name == pk_name:
                pk = object.__getattribute__(self, "_doc_primary_key")
                if pk is not None:
                    return pk
        return getattr(object.__getattribute__(self, "_doc_resolver")(), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_doc_resolver")(), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_doc_resolver")(), name, value)

    def __getitem__(self, index):
        return object.__getattribute__(self,
                                       "_doc_resolver")().__getitem__(index)

    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_doc_resolver")())

    def __str__(self):
        return str(object.__getattribute__(self, "_doc_resolver")())

    def __repr__(self):
        return repr(object.__getattribute__(self, "_doc_resolver")())

    def __len__(self):
        return len(object.__getattribute__(self, "_doc_resolver")())

    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
        '__contains__', '__delitem__', '__delslice__', '__div__',
        '__divmod__', '__eq__', '__float__', '__floordiv__', '__ge__',
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__',
        '__iand__', '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__',
        '__imod__', '__imul__', '__int__', '__invert__', '__ior__',
        '__ipow__', '__irshift__', '__isub__', '__iter__', '__itruediv__',
        '__ixor__', '__le__', '__long__', '__lshift__', '__lt__', '__mod__',
        '__mul__', '__ne__', '__neg__', '__oct__', '__or__', '__pos__',
        '__pow__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__',
        '__reduce__', '__reduce_ex__', '__repr__', '__reversed__',
        '__rfloorfiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__',
        '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__',
        '__rxor__', '__setitem__', '__setslice__', '__sub__', '__truediv__',
        '__xor__', 'next',
    ]

    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""

        def make_method(name):
            def method(self, *args, **kw):
                return getattr(object.__getattribute__(
                                    self, "_doc_resolver"
                                    )(),
                               name)(*args, **kw)
            return method
        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, theclass.__name__),
                    (cls,), namespace)

    def __new__(cls, doc_cls=None, primary_key=None, *args, **kwargs):
        """
        creates a proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        doc = None
        if isinstance(doc_cls, Document):
            doc = doc_cls
            doc_cls = doc.__class__
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[doc_cls]
        except KeyError:
            cache[doc_cls] = theclass = cls._create_class_proxy(doc_cls)
        ins = object.__new__(theclass)
        if doc:
            theclass.__init__(ins, doc, *args, **kwargs)
        else:
            theclass.__init__(ins, doc_cls, *args, **kwargs)
        return ins


def remove_proxy(lazyDoc):
    return object.__getattribute__(lazyDoc, "_doc_resolver")()

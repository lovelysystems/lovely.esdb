class Property(object):
    """A property to access data of a document

    Properties are use in Documents to provide access to the ES properties.
    """

    name = None  # outer property name

    def __init__(self,
                 name=None,
                 default=None,
                 primary_key=False,
                 doc=u''
                ):
        self.name = name
        self.doc = doc
        if hasattr(default, '__call__'):
            self.default = default
        else:
            def getDefault():
                return default
            self.default = getDefault
        self.primary_key = primary_key

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        if self.name in obj._source:
            return obj._source[self.name]
        else:
            value = self.default()
            obj._source[self.name] = value
            return value

    def __set__(self, obj, value):
        obj._source[self.name] = value
        if self.primary_key:
            obj._meta['_id'] = value

    def __delete__(self, obj):
        del obj._source[self.name]

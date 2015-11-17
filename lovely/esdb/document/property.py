class Property(object):
    """A property to access data of a document

    Properties are use in Documents to provide access to the ES properties.
    """

    name = None  # outer property name

    def __init__(self,
                 name=None,
                 default=None,
                 primary_key=False
                ):
        self.name = name
        self.default = default
        self.primary_key = primary_key

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return obj._source.get(self.name, self.default)

    def __set__(self, obj, value):
        obj._source[self.name] = value
        if self.primary_key:
            obj._meta['_id'] = value

    def __delete__(self, obj):
        del obj._source[self.name]

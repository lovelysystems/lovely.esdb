import copy


class Property(object):
    """A property to access data of a document

    Properties are used in Documents to provide access to the ES properties.
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
        self._setter = lambda doc, value: value
        self._getter = lambda doc, value: value

    def __get__(self, doc, cls=None):
        if doc is None:
            # access to the class property
            return self
        if not doc._values.exists(self.name):
            # property is not in the source, set the default
            self._set_default(doc)
        # allow subclasses to transform the source
        result = self._transform_from_source(doc)
        return self._getter(doc, result)

    def __set__(self, doc, value):
        value = self._setter(doc, value)
        doc._values.changed[self.name] = self._transform_to_source(doc, value)

    def __delete__(self, doc):
        """Delete the property from all storages
        """
        doc._values.delete(self.name)

    def getter(self, getter):
        """allows to set a getter function

        When a value is assigned to a `Property` this is the last method
        called with the value. The return value is what is returned to the
        reader.

        This can be used as a decorator:
            class MyDoc(Document):
                ...
                a = Property()

                @a.getter
                def a_getter(self, value):
                    return unicode(value)
        """
        self._getter = getter

    def setter(self, setter):
        """allows to set a setter function

        When a value is read from a `Property` this is the first method
        called with the value.

        This can be used as a decorator:
            class MyDoc(Document):
                ...
                a = Property()

                @a.setter
                def a_setter(self, value):
                    return value.lower()
        """
        self._setter = setter

    def get_query_name(self):
        return self.name

    def _apply(self, doc):
        """Called before the document is stored or updated

        Subclasses can do data transformations of cached data and update
        `doc._source`.

        Check if an object in `changed` is not different to the object in
        `changed`. Remove the object from `changed` if it is equal to the one
        in `source`.
        The default implementation does nothing
        """
        if (self.name in doc._values.changed
            and self.name in doc._values.source
            and (doc._values.changed[self.name]
                 == doc._values.source[self.name])
           ):
            # an unchanged value is in changed, remove it
            del doc._values.changed[self.name]
            return

    def _transform_from_source(self, doc):
        """Provides the property based on the _source data

        Subclasses can use this method the to data transformations between the
        representation in the database and the representation in python.

        Here we do some tricky things to make sure we can detect list and dict
        changes. Because this method is always called when accessing the
        property we copy a possibly existing object from source to changed if
        it is a dict or list. If somthing is changed inside the dict or list
        it will be detected in the `_apply` method.
        """
        if (self.name not in doc._values.changed
            and self.name in doc._values.source
           ):
            value = doc._values.source[self.name]
            if isinstance(value, (list, tuple, dict)):
                doc._values.changed[self.name] = copy.deepcopy(value)
        return doc._values.get(self.name)

    def _transform_to_source(self, doc, value):
        """Transform a value into a JSON compatible value
        """
        return value

    def _set_default(self, doc):
        if self.name not in doc._values.default:
            value = self._setter(doc, self.default())
            doc._values.default[self.name] = \
                self._transform_to_source(doc, value)

import json
from datetime import datetime
import jsonpickle
from jsonpickle.tags import RESERVED

from . import Property


class ObjectProperty(Property):

    def _transform_from_source(self, doc):
        """Provides the original object based on the source

        Uses a cached version of the transformed object or creates a new cache
        entry.
        """
        if self.name not in doc._values.property_cache:
            try:
                value = doc._values.get(self.name)
            except KeyError:
                value = None
            doc._values.property_cache[self.name] = decode(value)
        return doc._values.property_cache[self.name]

    def _transform_to_source(self, doc, value):
        """Stores the pickled version of `value` in the source

        `value` is also stored in the property cache.

        returns the stored value.
        """
        doc._values.property_cache[self.name] = value
        return encode(value)

    def _apply(self, doc):
        obj = doc._values.property_cache[self.name]
        doc._values.changed[self.name] = encode(obj)


def encode(obj):
    raw = json.loads(jsonpickle.encode(
                                obj,
                                unpicklable=False))
    pickle = jsonpickle.encode(obj)
    raw['_pickle'] = pickle
    return raw


def decode(data):
    if data is None:
        return None
    if '_pickle' in data:
        return jsonpickle.decode(data['_pickle'])
    return data


def meta_split(values):
    meta = {}
    data = {}
    for k, v in data:
        if k in RESERVED:
            pass
    return meta, data


class ISODatetimeHandler(jsonpickle.handlers.DatetimeHandler):
    """Handler for datetime object

    It is derived from the existing handler but provides the datetime in ISO
    format for the unpickable format.
    """

    def flatten(self, obj, data):
        pickler = self.context
        if not pickler.unpicklable:
            return obj.isoformat()
        return super(ISODatetimeHandler, self).flatten(obj, data)

ISODatetimeHandler.handles(datetime)

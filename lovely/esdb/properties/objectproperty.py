import json
import dateutil.parser
from datetime import datetime, date
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
            if value is None:
                doc._values.property_cache[self.name] = value
            else:
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
        if self.name not in doc._values.property_cache:
            # apply nothing if the property is not in the cache
            return
        obj = doc._values.property_cache.get(self.name)
        doc._values.changed[self.name] = obj is None and obj or encode(obj)


def encode(obj):
    """Build a JSON representation of the object
    """
    if obj is None:
        return None
    raw = json.loads(jsonpickle.encode(
                                obj,
                                unpicklable=False))
    pickle = jsonpickle.encode(obj)
    raw['object_json_pickle__'] = pickle
    return raw


def decode(data):
    """Recreate a python object from JSON
    """
    if data is None:
        return None
    if 'object_json_pickle__' in data:
        return jsonpickle.decode(data['object_json_pickle__'])
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
        """Builds the flattend date or datetime

        The value will be stored as iso8601 formatted string.
        """
        pickler = self.context
        payload = obj.isoformat()
        if not pickler.unpicklable:
            return payload
        flatten = pickler.flatten
        data['__reduce__'] = (flatten(obj.__class__, reset=False), payload)
        return data

    def restore(self, data):
        cls, payload = data['__reduce__']
        unpickler = self.context
        restore = unpickler.restore
        cls = restore(cls, reset=False)
        value = dateutil.parser.parse(payload)
        if cls is date:
            # this was a date object
            value = cls(value.year, value.month, value.day)
        return value

ISODatetimeHandler.handles(datetime)
ISODatetimeHandler.handles(date)

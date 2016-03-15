

class PickleDummy(object):
    """A dummy class to be used for PickleProperties

    The class must be placed here to have a proper module assignement.
    jsonpickle can not unpickle if the class is defined inside the doctest
    file.
    """
    name = 'll'

    def __repr__(self):
        return '<%s [name=%r]>' % (self.__class__.__name__,
                                   self.name)

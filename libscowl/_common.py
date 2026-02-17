from itertools import chain

class SlotsDataClass:
    __slots__ = ()
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
    def __repr__(self):
        slots = chain.from_iterable(getattr(cls, '__slots__', ()) for cls in reversed(self.__class__.__mro__))
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{k}={getattr(self, k)!r}' for k in slots if hasattr(self, k)))

def strtobool (val):
    """Convert a string representation of truth to True or False.
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")


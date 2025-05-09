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

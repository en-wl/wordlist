
class SlotsDataClass:
    __slots__ = ()
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(f'{k}={getattr(self, k)!r}' for k in self.__slots__ if hasattr(self, k)))

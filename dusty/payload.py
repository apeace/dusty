import cPickle

from .constants import VERSION

class Payload(object):
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.run_on_daemon = True
        self.client_version = VERSION
        self.args = args
        self.kwargs = kwargs
        self.suppress_warnings = False

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.fn == other.fn and self.args == other.args and self.kwargs == other.kwargs
        return False

    def run(self):
        self.fn(*self.args, **self.kwargs)

    def serialize(self):
        doc = {'fn': self.fn, 'client_version': self.client_version, 'suppress_warnings': self.suppress_warnings,
               'args': self.args, 'kwargs': self.kwargs}
        return cPickle.dumps(doc).encode('string_escape')

    @staticmethod
    def deserialize(doc):
        return cPickle.loads(doc.decode('string_escape'))

_daemon_command_mapping = {}

def daemon_command(f):
    key = '{}.{}'.join(f.__module__, f.__name__)
    if key in _daemon_command_mapping and _daemon_command_mapping[key] != f:
        raise RuntimeError("Function mapping key collision: {}. Name one of the functions something else".format(key))
    _daemon_command_mapping[key] = f
    return f


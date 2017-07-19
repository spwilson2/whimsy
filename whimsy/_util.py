import time

def kwonlyargs(given_kwargs, **available_kwargs):
    unrequested_kwargs = {}
    requested_kwargs = available_kwargs

    for key, val in given_kwargs.items():
        if key in requested_kwargs:
            requested_kwargs = key
        else:
            unrequested_kwargs[key] = val
    return (requested_kwargs, unrequested_kwargs)

class KwonlyargsError(TypeError):
    def __init__(self, func, kwargs):
        string = '%s got an unexpected keyword argument'\
                ' %s' % (func, kwargs.keys()[0])
        super(KwonlyargsError, self).__init__(string)


class InvalidEnumException(Exception):
    pass

class Enum(object):
    def __init__(self, enums, namespace=''):
        if namespace is not '':
            namespace = namespace + '.'
        for i, variant in enumerate(enums):
            new_enum = type(namespace+variant, (Enum,), {})
            setattr(self, variant, new_enum)

class Timer(object):
    def __init__(self, start=False):
        self.reset()

    def start(self):
        if self._start is None:
            self._start = time.time()

    def stop(self):
        self._finish = time.time()
        return self.runtime()

    def runtime(self):
        return self._finish - self._start

    def reset(self):
        self._start = self._finish = None

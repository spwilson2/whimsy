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

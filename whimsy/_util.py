def create_collector_metaclass(clsname,
                               callback=None,
                               save_instances=False,
                               save_inheritors=True):
    '''
    Creates a metaclass which collects all objects which inherit from the
    first parent utilizing the metaclass.

    :param callback: Optional callback which must take and return
    clsname, bases, dct to possibly modify or check them.
    '''

    # We need to do delayed initialization of the 'new' method, so we use
    # a lambda which will call our later defined new.
    __new__ = lambda *args, **kwargs : new(*args, **kwargs)

    newdict = {
        '__original_base__': None,
        '__new__': __new__,
    }

    if save_instances:
        newdict['__instances__'] = list()
    if save_inheritors:
        newdict['__inheritors__'] = list()

    metaclass = type(clsname, (type,), newdict)

    # We define new here (and do the awkward delayed call with the lambda) in
    # order to be able to capture the metaclass after its creation in this
    # function.
    def new(cls, clsname, bases, dct):

        if save_instances:

            # wrap __init__ of the derived class to automatically add itself
            # to the list of __instances__
            def wrap_init_save_instance(self, *args, **kwargs):
                if '__oldinit__' in dct:
                    dct['__oldinit__'](self, *args, **kwargs)
                cls.__instances__.append(self)

            # Move __init__ to __oldinit__ to solve the problem of recursion.
            if '__init__' in dct:
                dct['__oldinit__'] = dct['__init__']
            dct['__init__'] = wrap_init_save_instance

        if callback:
            (cls, clsname, bases, dct) = callback(cls, clsname, bases, dct)

        class_ = super(metaclass, cls).__new__(cls, clsname, bases, dct)

        if metaclass.__original_base__ is None:
            metaclass.__original_base__ = class_

        if save_inheritors:
            metaclass.__inheritors__.append(class_)
        return class_

    return metaclass

if __name__ == '__main__':
    metaclass = create_collector_metaclass('TestCollectorMetaclass')
    class TestCollector(object):
        __metaclass__ = metaclass
        def print_derived(self):
            print(self.__inheritors__)

    class Derived(TestCollector):
        def test():
            pass

    assert len(metaclass.__inheritors__) == 2, \
        'We should have captured inheritors.'

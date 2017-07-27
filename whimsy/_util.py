import collections
import time
import os
import difflib
import re
import tempfile
import shutil
import stat
import helper

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
    '''
    Generator for Enum objects.
    '''
    def __init__(self, enums, namespace=''):
        self.enums = []
        def __name__(self):
            return self.variant
        def __cmp__(self, other):
            return self.enums.index(self) > self.enums.index(other)


        if namespace is not '':
            namespace = namespace + '.'
        for i, variant in enumerate(enums):
            dct = {'__str__': __name__, 'variant': variant}

            new_enum = type('Enum.' + namespace + variant,
                            (object,),
                            dct)
            new_enum = new_enum()
            setattr(self, variant, new_enum)
            self.enums.append(new_enum)


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

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

def iter_recursively(self, inorder=True):
    '''
    Recursively iterate over all items contained in this collection.

    :param inorder: Traverses the tree in in-order fashion, returning nodes as
    well as leaves.
    '''
    for item in self:
        if isinstance(item, collections.Iterable):
            if inorder:
                # yield the node first
                yield item

            # Recurse into that node.
            for item_of_item in iter_recursively(item, inorder):
                yield item_of_item
        else:
            # Otherwise just yield the leaf
            yield item

unexpected_item_msg = \
        'Only TestSuites and TestCases should be contained in a TestSuite'

class AttrDict(object):
    '''Object which exposes its own internal dictionary through attributes.'''
    def __init__(self, dict_={}):
            self.__dict__.update(dict_)

    def __getattr__(self, attr):
        dict_ = self.__dict__
        if attr in dict_:
            return dict_[attr]
        raise AttributeError('Could not find %s attribute' % attr)

    def __setattr__(self, attr, val):
        self.__dict__[attr] = val

def _filter_file(fname, filters):
    with open(fname, "r") as file_:
        for line in file_:
            for regex in filters:
                if re.match(regex, line):
                    break
            else:
                yield line

def _copy_file_keep_perms(source, target):
    '''Copy a file keeping the original permisions of the target.'''
    st = os.stat(target)
    shutil.copy2(source, target)
    os.chown(target, st[stat.ST_UID], st[stat.ST_GID])

def _filter_file_inplace(fname, filters):
    '''
    Filter the given file writing filtered lines out to a temporary file, then
    copy that tempfile back into the original file.
    '''
    reenter = False
    (_, tfname) = tempfile.mkstemp(text=True)
    with open(tfname, 'w') as tempfile_:
        for line in _filter_file(fname, filters):
            tempfile_.write(line)

    # Now filtered output is into tempfile_
    _copy_file_keep_perms(tfname, fname)


def diff_out_file(ref_file, out_file, ignore_regexes=tuple()):
    if not os.path.exists(ref_file):
        raise OSError("%s doesn't exist in reference directory"\
                                     % ref_file)
    if not os.path.exists(out_file):
        raise OSError("%s doesn't exist in output directory" % out_file)

    _filter_file_inplace(out_file, ignore_regexes)
    _filter_file_inplace(ref_file, ignore_regexes)

    #try :
    (_, tfname) = tempfile.mkstemp(text=True)
    with open(tfname, 'r+') as tempfile_:
        try:
            helper.log_call(['diff', out_file, ref_file], stdout=tempfile_)
        except OSError:
            # Likely signals that diff does not exist on this system. fallback to
            # difflib
            with open(out_file, 'r') as outf, open(ref_file, 'r') as reff:
                diff = difflib.unified_diff(iter(reff.readline, ''),
                                            iter(outf.readline, ''),
                                            fromfile=ref_file,
                                            tofile=out_file)
                return ''.join(diff)
        except helper.CalledProcessError:
            tempfile_.seek(0)
            return ''.join(tempfile_.readlines())
        else:
            return None

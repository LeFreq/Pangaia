#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 1, 2002

"""Dictionary with default values, collision function, and sorted string output."""

__version__ = "$Revision: 2.3 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/07/31 23:06:06 $"

import exceptions
import copy

class KeyAlreadyExists(exceptions.LookupError): pass
class USE_DEFAULT:
    """Dummy class used as value in function parameters to indicate 
    no default value specified; i.e. use the value in defdict.default.
    Created special class to avoid clashing with possible value passed
    by user."""
#XXX perhaps should have instantiate default which takes arbitrary 
# number of parameters that will be passed to value stored in defdict.default
# to allow object creation.  defdict.add would check if isinstance(default, USE_DEFAULT)

#define some useful collision functions
#May wish to have return an expression instead of setting ddict directly
#  to allow lambda functions to be passed as collision functions.
#  may sacrifice speed for cases when value modified in place
OVERWRITE = None   #will use standard dict overwrite semantics
def RETAIN(ddict, key, new_value): pass  #do nothing to the value
def RAISE(ddict, key, new_value): raise KeyAlreadyExists, repr(key)
def ADD(ddict, key, new_value): ddict[key] += new_value
def MAX(ddict, key, new_value): ddict[key] = max(ddict[key], new_value)
def MIN(ddict, key, new_value): ddict[key] = min(ddict[key], new_value)
def OUTPUT_KEY(ddict, key, new_value): print key

class defdict(dict):
    """Extends standard dictionary type by allowing user to
    specify a default value when a key is inserted.  
    A 'collision' function can be provided to specify what should
    be done to the value when a key is added that already exists.
    
    User-defined collision function should take 
    (defdict, key, new_value) as parameters.
    """
    #XXX may wish to have collision method instead of constantly passing as parameter
    
    __slots__ = ['default']
    
    def __init__(self, init={}, default=None, collision=OVERWRITE):
        """Create dictionary and initialize with mapping or sequence
        object, if given.  
        
        Initialization interface similar to standard dictionary:
        >>> dd = defdict()  #create empty defdict
        >>> print dd
        {}
        >>> print defdict({1: 1, 2: 4, 3: 9}) #initialize with dict type
        {1: 1, 2: 4, 3: 9}
        >>> print defdict([('a', 2), ('b', 3), ('c', 1)]) #initialize with list of (key, value) pairs
        {'a': 2, 'b': 3, 'c': 1}
        
        Additionally, one can initialize defdict with a sequence of keys.
        The dictionary values of the keys will be determined by the default value,
        if given, otherwise defaults to None.  
        
        >>> print defdict(["apple", "banana", "carrot"])
        {'apple': None, 'banana': None, 'carrot': None}
        >>> dd = defdict(range(4), 0)   #initialize with values = 0
        >>> print dd
        {0: 0, 1: 0, 2: 0, 3: 0}
        
        The defdict's default value can be modified by writing to 
        its .default attribute.
        
        >>> dd.default = 1        #change dd's default value
        >>> dd.update([2, 3, 4])  #default will be used since no value specified
        >>> print dd
        {0: 0, 1: 0, 2: 1, 3: 1, 4: 1}
        
        A sequence of keys or (key, value) pairs may contain duplicate keys.
        The resulting value of such "key collisions" can be specified
        by providing a collision function.  The collision function will
        be called with parameters (self, key, new_value) and should set the
        value of self[key] as desired.
        
        This module defines a few useful collision functions:
        
        OVERWRITE:  the default--standard dictionary semantics; 
            i.e. if key already exists, new value overwrites existing 
            key value.
        RETAIN:  value remains unchanged if key already exists.
        RAISE_EXCEPTION:  raise 'KeyAlreadyExists' exception if key already 
            exists.  Value remains unchanged.
        ADD:  sets value to existing value + new value
        MAX:  sets to greater of old, new values
        MIN:  sets to lesser of old, new values
        
        >>> bag = defdict('abacab', 1, ADD) #character counts
        >>> print bag
        {'a': 3, 'b': 2, 'c': 1}
        """

        self.default = default
        if collision == OVERWRITE or isinstance(init, dict) or init==[]:
            try:
                dict.__init__(self, init)
                return        #success
            except (TypeError, ValueError): #must have been given just a regular sequence (not key, value pairs)
                self.clear()  #clear partially-created dict, fall-through to using update()
        dict.__init__(self)
        self.update(init, default, collision)
            
    def update(self, other, default=USE_DEFAULT, collision=OVERWRITE):
        """Updates defdict from mapping or sequence type.  

        >>> d = defdict('abc', 1)
        >>> print d
        {'a': 1, 'b': 1, 'c': 1}
        >>> d.update({'a': 0, 'b':7, 'd': 2})
        >>> print d
        {'a': 0, 'b': 7, 'c': 1, 'd': 2}
        
        If a sequence of keys is given, key values will assume default value,
        unless otherwise specified:
        
        >>> d.update(['b','e'], 5)  #use 5 as the value for the keys
        >>> d.update('af')          #a string is also a sequence
        >>> print d
        {'a': 1, 'b': 5, 'c': 1, 'd': 2, 'e': 5, 'f': 1}
        
        As seen above, when updating a key which already exists and no 
        collision function is specified, update defaults to standard dictionary 
        OVERWRITE semantics.  This behavior can be modified by passing a 
        collision function.
        
        >>> d.update({'a': 3, 'c': 1, 'f': 9}, collision=ADD)
        >>> print d
        {'a': 4, 'b': 5, 'c': 2, 'd': 2, 'e': 5, 'f': 10}
        >>> d.update('abc', collision=ADD)
        >>> print d
        {'a': 5, 'b': 6, 'c': 3, 'd': 2, 'e': 5, 'f': 10}
                
        NOTE:  If collision function raises an exception, defdict may be
        left in partially-updated state.
        """
        
        #perhaps should catch any exceptions that may be caused by collision
        #  and store aberrent keys in the exception to be reported later.
        if isinstance(other, dict):
            if collision == OVERWRITE:
                dict.update(self, other)
            else:   #other dict may contain keys in self
                for key, value in other.iteritems():
                    self.setdefault(key, value, collision)
        else:  #sequence 
            for key in other:   #XXX slower than necessary since setdefault will check default each time and return unused value
                self.setdefault(key, default, collision)
            
    def setdefault(self, key, value = USE_DEFAULT, collision=RETAIN):
        """Behaves like standard dict.setdefault, but uses value in
        default attribute if no default parameter specified.
        
        >>> dd = defdict(default=5)
        >>> dd.setdefault('a', 10), dd.setdefault('b'), dd.setdefault('b', 11)
        (10, 5, 5)
        >>> print dd
        {'a': 10, 'b': 5}
        
        A collision function can also be passed to override setdefault's
        standard RETAIN semantics.
        
        >>> dd.setdefault('a', collision=OVERWRITE), dd.setdefault('b', 6, ADD)
        (5, 11)
        >>> dd.setdefault('b', 12, MAX), dd.setdefault('b', 10, MAX)
        (12, 12)
        >>> dd.setdefault('c', 10, RAISE)
        10
        >>> dd.setdefault('c', 10, RAISE)
        Traceback (most recent call last):
           ...
        KeyAlreadyExists: 'c'
        >>> print dd
        {'a': 5, 'b': 12, 'c': 10}

        Default value is copied if non-simple type (ex. list, dict).

        >>> dd = defdict(default=[])
        >>> dd.setdefault(1), dd.setdefault(2)
        ([], [])
        >>> assert dd[1] is not dd[2]  #keys 1 and 2 have distinct value objects
        >>> dd[2].append(42)
        >>> print dd
        {1: [], 2: [42]}
        """
        key_absent = key not in self   #fail immediately if key unhashable
        if value == USE_DEFAULT:
            value = copy.copy(self.default) #could consider using property and assigning read method based on (copy(default) is default)
        if collision == OVERWRITE or key_absent:
            self[key] = value
            return value
        else:
            collision(self, key, value)
            return dict.__getitem__(self, key)  #may wish to allow dd[key] to insert key in dd with default value
        
    def get(self, key, *args):
        """Behaves like standard dict.get, but uses value in
        default attribute if no default parameter specified.
        
        >>> dd = defdict({'a': 10}, 0)
        >>> dd.get('a'), dd.get('b'), dd.get('b', 11)
        (10, 0, 11)
        >>> print dd
        {'a': 10}
        """
        if not args: args = (self.default,)
        return dict.get(self, key, *args)

    def __getitem__(self, key):
        """Return value of given key.  If key not in self, then create key with default value.
        
        >>> dd = defdict(default=defdict(default=0))
        >>> dd[1][2]
        0
        >>> print dd
        {1: {2: 0}}
        """
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            value = copy.copy(self.default)
            self[key] = value
            return value
            
    def copy(self):
        """Return shallow copy of dictionary.
        >>> dd = defdict(range(5), 5)
        >>> ddcopy = dd.copy()
        >>> print ddcopy.default, type(ddcopy); print ddcopy
        5 <class 'defdict.defdict'>
        {0: 5, 1: 5, 2: 5, 3: 5, 4: 5}
        >>> ddcopy[0] = 7
        >>> print dd[0], ddcopy[0]
        5 7
        """
        return self.__class__(self, self.default)
        
    __copy__ = copy
        
    def __str__(self, format_string="%r: %r"):
        """Convert self to string with keys in sorted order.
        >>> str(defdict())
        '{}'
        >>> str(defdict({9: 0, 'test': 0, 'a': 0, 0: 0}))
        "{0: 0, 9: 0, 'a': 0, 'test': 0}"
        """
        if not self: return '{}'    #nothing to sort
        keys = self.keys()
        keys.sort()
        return '{' + ', '.join([format_string % (k, self[k]) for k in keys]) + '}'


def _test():
    import doctest, defdict
    return doctest.testmod(defdict)
    
if __name__ == "__main__":
    _test()

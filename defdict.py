import exceptions
import operator
import copy

class KeyAlreadyExists(exceptions.LookupError): pass
class USE_DEFAULT:
    """Dummy class used as value in function parameters to indicate 
    no default value specified; i.e. use the value in defdict.default.
    Created special class to avoid clashing with possible value passed
    by user."""

#define some standard collision functions
#named functions (as opposed to using lambdas) allow the user to inspect
#what collision function is currently in effect.
#XXX allow passing of key value in case collision behavior should depend on key
#  ex: appending to a list of key values which already existed, or providing key value in KeyAlreadyExists exception.
#  would probably be best to have collision(defdict, key, newvalue) parameter signature
OVERWRITE = None   #will use standard dict overwrite semantics
def RETAIN(old, new): return old
def RAISE_EXCEPTION(old, new): raise KeyAlreadyExists
ADD, MAX, MIN = operator.add, max, min

class defdict(dict):
    """Extends standard dictionary type by allowing user to
    specify a default value when a key is inserted (see add()).  
    A 'collision' function can be provided to specify what should
    be done to the value when a key is added that already exists.
    """
    #XXX may wish to have collision method instead of constantly passing as parameter
    
    __slots__ = ['default']
    
    def __init__(self, init=None, default=None, collision=OVERWRITE):
        """Create dictionary and initialize with init if given.
        init can be dictionary or sequence type.  If sequence, will
        use default value if specified.  If sequence has duplicates, resulting
        value will be determined by collision function.
        If no default specified, dictionary values default to None.
        If no collision function specified, defaults to standard dict over-write
        semantics.
        
        Initialization interface similar to standard dictionary:
        >>> dd = defdict()  #create empty defdict
        >>> print dd
        {}
        >>> print defdict({1: 1, 2: 4, 3: 9}) #initialize with dict type
        {1: 1, 2: 4, 3: 9}
        >>> print defdict([('a', 2), ('b', 3), ('c', 1)]) #initialize with list of (key, value) pairs
        {'a': 2, 'b': 3, 'c': 1}
        
        Additionally, one can initialize defdict with a simple list of keys.
        The dictionary values of the keys will be determined by the default value,
        if given, otherwise defaults to None.
        
        >>> print defdict(["apple", "banana", "carrot"])
        {'apple': None, 'banana': None, 'carrot': None}
        >>> print defdict(range(4), 0)   #initialize with values = 0
        {0: 0, 1: 0, 2: 0, 3: 0}
        
        A list of keys or key, value pairs may contain duplicate keys.
        The resulting value of such "key collisions" can be specified
        by providing a collision function.  This module defines a few
        useful collision functions:
        
        OVERWRITE:  the default--standard dictionary semantics; 
            i.e. if key already exists, new key value overwrites existing 
            key value.
        RETAIN:  value remains unchanged if key already exists.
        RAISE_EXCEPTION:  raise 'KeyAlreadyExists' exception if key already 
            exists.  Value remains unchanged.
        ADD:  returns existing value + new value
        MAX:  returns greater of old, new values
        MIN:  returns lesser of old, new values
        
        >>> bag = defdict(map(None,'abacab'), 1, ADD) #character counts
        >>> print bag
        {'a': 3, 'b': 2, 'c': 1}
        
        defdict's default value can be modified by writing to .default attribute.
        """

        self.default = default
        if not init: 
            dict.__init__(self)
            return
        elif collision == OVERWRITE or isinstance(init, dict):
            try:
                dict.__init__(self, init)
                return        #success
            except (TypeError, ValueError): #must have been given just a regular sequence (not key, value pairs)
                self.clear()  #clear partially-created dict, fall-through to using update()
        dict.__init__(self)
        self.update(init, collision)
            
    def update(self, other, collision=OVERWRITE):
        """Updates defdict from other dict or list type.  

        >>> d = defdict(['a', 'b', 'c'], 1)
        >>> print d
        {'a': 1, 'b': 1, 'c': 1}
        >>> d.update({'a': 0, 'b':7, 'd': 2})
        >>> print d
        {'a': 0, 'b': 7, 'c': 1, 'd': 2}
        
        If a list of keys is given, key values will use default value:
        
        >>> d.update(['b','e'])
        >>> print d
        {'a': 0, 'b': 1, 'c': 1, 'd': 2, 'e': 1}
        
        As seen above, when updating a key which already exists and no 
        collision function is specified, update defaults to standard dictionary 
        OVERWRITE semantics.  This behavior can be modified by passing a 
        collision function.
        
        >>> import operator  #will use operator.add for collision function
        >>> d.update({'a': 3, 'c': 1, 'f': 9}, operator.add)
        >>> print d
        {'a': 3, 'b': 1, 'c': 2, 'd': 2, 'e': 1, 'f': 9}

        When update is given a key list, default values are assumed.

        >>> d.default
        1
        >>> d.update(['a', 'b', 'c'], operator.add)
        >>> print d
        {'a': 4, 'b': 2, 'c': 3, 'd': 2, 'e': 1, 'f': 9}
                
        NOTE:  User is responsible for ensuring that collision function will not 
        cause an error for any given or existing value operands, else dictionary
        may be left in partially-updated state.
        """
        
        #perhaps should catch any exceptions that may be caused by collision
        #and store aberrent keys in the exception to be reported later.
        #wish dict.update allowed collision function (much faster)
        if isinstance(other, dict):
            if collision == OVERWRITE:
                dict.update(self, other)
            else:   #other dict may contain keys in self
                for key, value in other.iteritems():
                    self.add(key, value, collision)
        else:   #list
            if not isinstance(other, list): raise TypeError, "dict or list type expected"
            for key in other:
                self.add(key, self.default, collision)
            
    def add(self, key, value = USE_DEFAULT, collision=OVERWRITE):
        """Add a single key, value pair to defdict using given collision 
        function if key already exists.  If no collision function is given,
        add defaults to default OVERWRITE semantics; i. e. self[key] = value,
        regardless of any existing key.
        If value is omitted, will set to a COPY of value specified in default 
        attribute; i.e. if default value is an empty list, then different keys
        will have unique empty list objects.  
        
        >>> dd = defdict({1: 2, 2: 4, 3: 9}, 0)
        >>> dd.add(4, 0, max)
        >>> print dd
        {1: 2, 2: 4, 3: 9, 4: 0}
        >>> dd.add(4, 16, max)
        >>> dd.add(4, 8, max)
        >>> print dd
        {1: 2, 2: 4, 3: 9, 4: 16}
        >>> dd.add(1)
        >>> print dd
        {1: 0, 2: 4, 3: 9, 4: 16}

        NOTE:  using 'dd[key] = value' notation, will always do a hard set
        of value to key in defdict; i.e.  no collision function is called
        if key already exists.
        """
        #XXX Update generally should use OVERWRITE, but add should use RETAIN[_IF_DEFAULT] semantics?
        #XXX should add() use *args for argument list (like setdefault()), instead of USE_DEFUALT hack?
        if value == USE_DEFAULT: value = copy.copy(self.default)
        if collision == OVERWRITE or key not in self:
            self[key] = value
        else:
            self[key] = collision(self[key], value)

    def setdefault(self, key, *args):
        """Behaves like standard dict.setdefault, but uses value in
        default attribute if no default parameter specified.
        
        >>> dd = defdict({'a': 10}, 0)
        >>> dd.default
        0
        >>> dd.setdefault('a'), dd.setdefault('b'), dd.setdefault('b', 11)
        (10, 0, 0)
        >>> print dd
        {'a': 10, 'b': 0}
        """
        if not args: args = (self.default,)
        return dict.setdefault(self, key, *args)
        
    def get(self, key, *args):
        """Behaves like standard dict.get, but uses value in
        default attribute if no default parameter specified.
        
        >>> dd = defdict({'a': 10}, 0)
        >>> dd.default
        0
        >>> dd.get('a'), dd.get('b'), dd.get('b', 11)
        (10, 0, 11)
        >>> print dd
        {'a': 10}
        """
        if not args: args = (self.default,)
        return dict.get(self, key, *args)

    def copy(self):
        """Return shallow copy of dictionary.
        >>> dd = defdict(range(5), 5)
        >>> ddcopy = dd.copy()
        >>> print type(ddcopy), ddcopy
        <class 'defdict.defdict'> {0: 5, 1: 5, 2: 5, 3: 5, 4: 5}
        """
        return self.__class__(self, self.default)
        
    def __str__(self):
        """Convert self to string with keys in sorted order.
        >>> str(defdict({9: 0, 'test': 0, 'a': 0, 0: 0}))
        "{0: 0, 9: 0, 'a': 0, 'test': 0}"
        """
        if len(self) < 2: return dict.__str__(self)   #nothing to sort
        keys = self.keys()
        keys.sort()
        s = '{'
        for k in keys: #XXX doesn't work right: omits quotes around strings
            s+= "%r: %r, " % (k, self[k]) #
        return s[:-2] + '}'


def _test():
    import doctest, defdict
    return doctest.testmod(defdict)
    
if __name__ == "__main__":
    _test()

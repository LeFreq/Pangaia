#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 1, 2002

"""Bag types"""

__version__ = "$Revision: 2.2 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/08/09 21:42:01 $"

import operator

#bag should have list interface? --should add list methods: append, remove, min/max,  __str__ return list string, etc.
#   in addition to min/max(), perhaps create most/least() to return the item with the highest/lowest count
#XXX figure out what should happen: bag[nokey] -= 5, bag[key] -=5
#XXX checking in setitem takes too much time: create compress function that removes zero-valued items periodically

IntegerType = (int, long)

class imbag(dict):
    """Implements a bag type that allows item counts to be negative."""

    __slots__ = []

    def __init__(self, init={}):
        """Initialize bag with optional contents.
        >>> b = bag()   #creates empty bag
        >>> b
        {}
        >>> b = bag({'b': 2, 'c': 1, 'a': 3})
        >>> b2 = bag(['a', 'b', 'c', 'b', 'a', 'a'])
        >>> b3 = bag("abacab")
        >>> assert b == b2 == b3
        >>> b = imbag({1: -1, 2: 0, 3: -9})
        >>> assert b == {1: -1, 3: -9}
        >>> word_count = bag("how much wood could a wood chuck chuck".split())
        >>> assert word_count == {'how': 1, 'much': 1, 'wood': 2, 'could': 1, 'a': 1, 'chuck': 2}
        """
        if isinstance(init, dict) or init==[]:
            dict.__init__(self, init)
            if not isinstance(init, imbag):   #non-bag may have questionble count values
                self._validate()
        else:   #assume sequence initializer
            dict.__init__(self)
            self += init

    def update(self, items):
        """Adds contents to bag.  Takes dictionary type.
        >>> b = imbag("abc")
        >>> b.update({'a': 2, 'b': 1, 'c': 0})
        >>> assert b == {'a': 3, 'b': 2, 'c': 1}
        
        Negative updates are allowable.
        >>> b.update({'a': -2, 'b': -2, 'c': -2, 'd': 2})
        >>> assert b == {'a': 1, 'c': -1, 'd': 2}
        
        Invalid values raise TypeError and may leave bag in
        unknown state:
        >>> b.update({0: 'test1', 'a': 'test2', 'd': 3, 'f': 1.0})
        Traceback (most recent call last):
        ...
        TypeError: value must be integral type, not <type 'str'>
        """
        #XXX require or check for bag type, then can drop two conditionals on each iteration
        for key, count in items.iteritems():
            if not isinstance(count, IntegerType): raise TypeError, "value must be integral type, not %r" % type(count)
            elif not count: continue  #nothing to add
            elif key in self:
                newvalue = dict.__getitem__(self, key) + count
                if newvalue: dict.__setitem__(self, key, newvalue)
                else: del self[key]
            else:
                dict.__setitem__(self, key, count)
            #self[key] += count  #about twice as slow than above XXX fix __iadd__ too?
    
    def pop(self):
        raise NotImplemented #XXX
    
    def __iadd__(self, items):
        """Add items in iterable object to bag.
        >>> b = bag()
        >>> b += [1, 2, 1, 0]
        >>> assert b == {0: 1, 1: 2, 2: 1}
        >>> b.clear()
        >>> b += "abca"
        >>> assert b == {'a': 2, 'b': 1, 'c': 1}
        """
        for item in items:
            self[item] += 1
        return self
            
    def __isub__(self, items):
        """Subtract items in iterable object from bag.
        >>> b = bag("abacab")
        >>> b -= "cab"
        >>> assert b == {'a': 2, 'b': 1}
        """
        #XXX Should this method be removed? (list doesn't support it)  What should happen if item not in bag?
        for item in items:
            self[item] -= 1
        return self
        
    def __imul__(self, factor):
        """Multiply bag contents by factor.
        >>> b = imbag("abacab")
        >>> b*= 4
        >>> assert b == {'a': 12, 'b': 8, 'c': 4}
        >>> b*= -1
        >>> assert b == {'a': -12, 'b': -8, 'c': -4}
        >>> b*=0
        >>> assert b == {}
        """
        if not isinstance(factor, IntegerType):
            raise TypeError, "unsupported operand type(s) for *: %r and %r" % (type(self), type(other))
        if factor > 1 or factor < 0:
            for item, count in self.iteritems():
                dict.__setitem__(self, item, count*factor) #bypass test logic in bag.__setitem__
        elif factor == 0:
            self.clear()
        return self
                
    def __eq__(self, other):
        """Equality test.  Can compare against dict or sequence type.
        >>> bag("abacab") == {'a': 3, 'b': 2, 'c': 1}
        1
        >>> bag([1, 2, 1, 3, 1]) == [1, 1, 1, 3, 2]
        1
        """
        if isinstance(other, list): other = self.__class__(other)
        return dict.__eq__(self, other)

    def setdefault(self, key, count=1):
        #XXX perhaps remove this on bag
        if not isinstance(count, IntegerType):  raise TypeError, "value must be integral type: %r" % count
        elif count:  return dict.setdefault(self, key, count)
        else:  return self[key]

    def __nonzero__(self):
        """Returns zero if bag is empty, non-zero otherwise.
        >>> b = bag()
        >>> not b
        1
        >>> b += [0]
        >>> not b
        0
        """
        return dict.__len__(self)
    
    def __len__(self):
        """Returns sum of item counts in bag.
        >>> b = imbag("abacab")
        >>> len(b)
        6
        >>> b['a'] = -4
        >>> len(b)
        -1
        """
        #XXX len(b)!=len(list(b)) -- perhaps should return abs (or iter not return negatived keys)
        return reduce(operator.add, self.itervalues(), 0)
        
    def __abs__(self):
        """Returns sum of absolute value of item counts in bag.
        >>> b = imbag("abacab")
        >>> b['a'] = -4
        >>> abs(b)
        7
        """
        return reduce(operator.add, map(abs, self.itervalues()), 0)

    def __getitem__(self, key):
        """Returns total count for given item.  If
        item not in bag, then returns 0.
        >>> b = bag("abacab")
        >>> b['a']
        3
        >>> b['d']
        0
        """
        if key in self: #seems faster than try/except
            return dict.__getitem__(self, key)
        else:
            return 0

    count = __getitem__

    def __setitem__(self, item, count):
        """Sets the count for the given item.
        >>> b = imbag([1, 2, 3])
        >>> b[1] = 3
        >>> b[4] = 2L   #long values okay
        >>> assert b == {1: 3, 2: 1, 3: 1, 4: 2}
        
        If count is zero, all items are deleted from bag.  
        >>> b[2] = 0
        >>> assert b == {1: 3, 3: 1, 4: 2}
        
        Counts for imbag are allowed to be negative.
        >>> b[4] = -2
        >>> b[5] -= 2
        >>> b[1] -= 4
        >>> b[3] -= 1
        >>> assert b == {1: -1, 4: -2, 5: -2}
        
        If count is non-integer, TypeError is raised.
        >>> b[1] = "oops"
        Traceback (most recent call last):
        ...
        TypeError: count must be integral type, not <type 'str'>
        """
        if not isinstance(count, IntegerType): raise TypeError, "count must be integral type, not %r" % type(count)
        elif count:
            dict.__setitem__(self, item, count)
        else:   
            try:  del self[item]
            except LookupError:  pass
            
    def __iter__(self):
        """Will iterate through all items in bag individually.
        >>> b = imbag("abacab")
        >>> b['b'] = -2
        >>> l = list(b); l.sort()
        >>> l
        ['a', 'a', 'a', 'b', 'b', 'c']
        """
        #XXX list(b) != imbag(list(b))
        #XXX is there a better way than pre-constructing the whole list??
        return iter(reduce(operator.add, [[key]*abs(count) for key, count in self.iteritems()], []))
        
    def __str__(self):
        """Convert self to string with items in sorted order.
        >>> str(imbag())
        '[]'
        >>> str(imbag({'b': -2, 'a': 3, 'c': 1}))
        "['a', 'a', 'a', 'b', 'b', 'c']"
        """
        #sort by values, largest first? should we sort at all?
        self._validate()
        if not self: return '[]'    #nothing to sort
        keys = self.keys()
        keys.sort()
        return str(reduce(operator.add, [[key]*abs(self[key]) for key in keys], []))

    def _validate(self):
        remove_list = []
        for key, count in self.iteritems():
            if not isinstance(count, IntegerType):
                raise TypeError, "invalid count type %r" % count
            elif count==0:
                remove_list.append(key) #can't delete while iterating
        for key in remove_list:
            del self[key]


class bag(imbag):
    """Standard bag class."""

    __slots__ = []

    def __imul__(self, factor):
        """Multiply bag contents by factor.
        >>> b = bag("abacab")
        >>> b*= 4
        >>> assert b == {'a': 12, 'b': 8, 'c': 4}
        
        Negative or zero factors will return empty bag.
        >>> b*= -2
        >>> b
        {}
        """
        if not isinstance(factor, IntegerType):
            raise TypeError, "unsupported operand type(s) for *: %r and %r" % (type(self), type(other))
        if factor > 1:
            for item, count in self.iteritems():
                dict.__setitem__(self, item, count*factor) #bypass test logic in bag.__setitem__
        elif factor < 0:
            self.clear()    #duplicates list.__imul__ behavior
        return self

    def __len__(self):
        """Returns total number of items in bag.
        >>> b = bag("abacab")
        >>> len(b)
        6
        """
        return reduce(operator.add, self.itervalues(), 0)

    def setdefault(self, key, count=1):
        #XXX perhaps remove this on bag
        if not isinstance(count, IntegerType):  raise TypeError, "value must be integral type: %r" % count
        elif count<0:  raise ValueError, "value must be >= 0: %r" % count
        elif count==0:  return self[key]
        else:  return dict.setdefault(self, key, count)

    def __setitem__(self, item, count=1):
        """Like imbag.__setitem__, however if count is 
        less than zero, ValueError is raised.
        >>> b = bag([1, 2, 3, 4, 4])
        >>> b[4] = -2
        Traceback (most recent call last):
        ...
        ValueError: 4 depleted
        
        #>>> b[5] = -2
        #Traceback (most recent call last):
        #...
        #ValueError: 5 depleted
        """
        if not isinstance(count, IntegerType): raise TypeError, "count must be integral type, not %r" % type(count)
        elif count>0:
            dict.__setitem__(self, item, count)
        else:   #XXX fix this, inconsistent: bag[key]=-1 vs bag[nokey]=-1
            try:
                del self[item]
            except LookupError:
                pass
            else:
                if count<0:
                    raise ValueError, "%r depleted" % item
            
    def _validate(self):
        remove_list = []
        for key, count in self.iteritems():
            if not isinstance(count, IntegerType) or count<0:
                raise ValueError, "invalid count value %r" % count
            elif count==0:
                remove_list.append(key) #can't delete while iterating
        for key in remove_list:
            del self[key]

    def __iter__(self):
        """Will iterate through all items in bag individually.
        >>> b = bag("abacab")
        >>> l = list(b); l.sort()
        >>> l
        ['a', 'a', 'a', 'b', 'b', 'c']
        """
        #XXX is there a better way than pre-constructing the whole list??
        return iter(reduce(operator.add, [[key]*count for key, count in self.iteritems()], []))
        
    def __str__(self):
        """Convert self to string with items in sorted order.
        >>> str(bag())
        '[]'
        >>> str(bag("abacab"))
        "['a', 'a', 'a', 'b', 'b', 'c']"
        """
        #sort by values, largest first? should we sort at all?
        self._validate()
        if not self: return '[]'    #nothing to sort
        keys = self.keys()
        keys.sort()
        return str(reduce(operator.add, [[key]*self[key] for key in keys], []))


def _test():
    import doctest, bag
    return doctest.testmod(bag)
    
if __name__ == "__main__":
    _test()

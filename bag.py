#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 1, 2002

"""Bag"""

__version__ = "$Revision: 2.1 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/08/08 03:00:13 $"

import operator

#bag should have list interface? --should add list methods: append, remove, min/max,  __str__ return list string, etc.
#   in addition to min/max(), perhaps create most/least() to return the item with the highest/lowest count
#XXX figure out what should happen: bag[nokey] -= 5, bag[key] -=5

IntegerType = (int, long)

class bag(dict):

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
        >>> word_count = bag("how much wood could a wood chuck chuck".split())
        >>> assert word_count == {'how': 1, 'much': 1, 'wood': 2, 'could': 1, 'a': 1, 'chuck': 2}
        """
        if isinstance(init, dict) or init==[]:
            dict.__init__(self, init)
        else:   #assume sequence initializer
            dict.__init__(self)
            self += init
        self._validate()

    def update(self, items):
        """Adds contents to bag.  Takes dictionary type.
        >>> b = bag("abc")
        >>> b.update({'a': 2, 'b': 1, 'c': 0})
        >>> assert b == {'a': 3, 'b': 2, 'c': 1}
        
        Negative updates are allowable.
        >>> b.update({'a': -2, 'b': -2, 'c': 2})
        >>> assert b == {'a': 1, 'c': 3}
        
        If the count drop below zero, a ValueError is raised,
        possibly leaving bag in partially-updated state.
        >>> b.update({'a': -2})
        Traceback (most recent call last):
        ...
        ValueError: 'a' depleted
        >>>
        """
        for key, count in items.iteritems():
            self[key] += count
    
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
        >>> b = bag("abacab")
        >>> b*= 4
        >>> assert b == {'a': 12, 'b': 8, 'c': 4}
        """
        if not isinstance(factor, IntegerType):
            raise TypeError, "unsupported operand type(s) for *: %r and %r" % (type(self), type(other))
        if factor > 1:
            for item, count in self.iteritems():
                dict.__setitem__(self, item, count*factor) #bypass test logic in bag.__setitem__
        elif factor < 0:
            self.clear()    #duplicates list.__imul__ behavior
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
        elif count<0:  raise ValueError, "value must be >= 0: %r" % count
        elif count==0:  return self[key]
        else:  return dict.setdefault(self, key, count)

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
        """Returns total number of items in bag.
        >>> b = bag("abacab")
        >>> len(b)
        6
        """
        return reduce(operator.add, self.itervalues(), 0)

    def __getitem__(self, key):
        """Returns total count for given item.  If
        item not in bag, then returns 0.
        >>> b = bag("abacab")
        >>> b['a']
        3
        >>> b['d']
        0
        """
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return 0

    count = __getitem__

    def __setitem__(self, item, count=1):
        """Sets the count for the given item.
        >>> b = bag([1, 2, 3])
        >>> b[1] = 3
        >>> b[4] = 2L
        >>> assert b == {1: 3, 2: 1, 3: 1, 4: 2}
        
        If count is zero, all items are deleted from bag.  
        >>> b[2] = 0
        >>> assert b == {1: 3, 3: 1, 4: 2}
        
        If count is less than zero, ValueError is raised.
        >>> b[4] = -2
        Traceback (most recent call last):
        ...
        ValueError: 4 depleted
        
        #>>> b[5] = -2
        #Traceback (most recent call last):
        #...
        #ValueError: 5 depleted
        
        If count is non-integer, TypeError is raised.
        >>> b[1] = "oops"
        Traceback (most recent call last):
        ...
        TypeError: count must be integral type, not <type 'str'>
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

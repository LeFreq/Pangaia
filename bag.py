#!/usr/bin/env python
# Mark Janssen,  July 1, 2002

"""Bag types"""

__version__ = "$Revision: 2.11 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2003/06/23 02:07:05 $"

#bag should have list interface? --should add list methods: append, remove, min/max,  __str__ return list string, etc.
#   in addition to min/max(), perhaps create most/least() to return the item with the highest/lowest count
#XXX checking in setitem takes too much time: create compress function that removes zero-valued items periodically or on methods which rely on non-zero values: iter, str, etc.
#create bag attribute to hold size of bag and re-calculate only when bag has been written to.
#XXX .size() should probably be converted to a property.
#perhaps limit bag to either list or dict types for adding/updating.  --note new dict.fromkeys has no such limit
#create bag exception class instead of generic TypeError to refine what users catch
#Let __init__ take a check function instead of defining one in class to make it easier for bag refinements w/o resorting to subclassing
# OR perhaps set __setitem__ to a class static variable, initially set to None, but then set appropriately in the __init__()
# this way bag could just be a special type of defdict (which would use this "staticmethod" to set value to default if none specified.

import random  #pick()

_DEBUG = True

IntegerType = (int, long)
RealType = (float, int, long)
NumberType  = (int, float, long, complex)

class RealBag:
    pass

class IntegerBag(dict):
    """Implements a bag type that allows item counts to be negative."""

    __slots__ = []

    def __init__(self, init={}):
        """Initialize bag with optional contents.

        >>> b = NaturalBag()   #creates empty bag
        >>> b
        {}
        >>> print IntegerBag({1: -1, 2: 0, 3: -9})
        {1: -1, 3: -9}

        Can initialize with (key, count) list as in standard dict.
        However, duplicate keys will accumulate counts:
        >>> print NaturalBag([(1, 2), (2, 4), (1, 7)])
        {1: 9, 2: 4}
        """
        if not init or isinstance(init, self.__class__):
            dict.__init__(self, init)   #values known to be good, use faster dict creation
        else:   #initializing with list or plain dict
            dict.__init__(self)
            if isinstance(init, dict):
                for key, count in init.iteritems():
                    self[key] = count #will test invariants
            else:       #sequence may contain duplicates, so add to existing value, if any
                for key, count in init:
                    self[key] += count

    def fromkeys(cls, iterable, count=1):
        """Class method which creates bag from iterable adding optional count for each item.

        >>> b = NaturalBag({'b': 2, 'c': 1, 'a': 3})
        >>> b2 = NaturalBag.fromkeys(['a', 'b', 'c', 'b', 'a', 'a'])
        >>> b3 = NaturalBag.fromkeys("abacab")
        >>> assert b == b2 == b3

        >>> word_count = NaturalBag.fromkeys("how much wood could a wood chuck chuck".split())
        >>> print word_count
        {'a': 1, 'chuck': 2, 'could': 1, 'how': 1, 'much': 1, 'wood': 2}

        An optional count can be specified.  Count added each time item is encountered.
        >>> print NaturalBag.fromkeys("abacab", 5)
        {'a': 15, 'b': 10, 'c': 5}
        """
        b = cls()
        for key in iterable: #could just return b.__iadd__(iterable, count)
            b[key] += count  #perhaps slower than necessary but will simplify derived classes that override __setitem__()
        return b

    fromkeys = classmethod(fromkeys)

    def update(self, items, count=1):
        """Adds contents to bag from other mapping type or iterable.

        >>> ib = IntegerBag.fromkeys('abc')
        >>> ib.update({'a': 2, 'b': 1, 'c': 0})
        >>> print ib
        {'a': 3, 'b': 2, 'c': 1}

        Negative updates are allowable.
        >>> ib.update({'a': -2, 'b': -2, 'c': -2, 'd': 2})
        >>> print ib
        {'a': 1, 'c': -1, 'd': 2}

        Can call with iterable.  Amount added can be specified by count parameter:
        >>> ib.update(['a','b'], 2)
        >>> print ib
        {'a': 3, 'b': 2, 'c': -1, 'd': 2}

        Values that can't be converted to ints are skipped and will raise TypeError.
        >>> ib.update({0: 'test1', 'a': 'test2', 'd': 3, 'f': '1.0', 'c': 2.0})
        Traceback (most recent call last):
        TypeError: unsupported operand type(s) for +=: 'int' and 'str'
        >>> print ib
        {'a': 3, 'b': 2, 'c': 1, 'd': 5}

        Updating NaturalBag with values that would cause the count to go negative
        sets count to 0, removing item.
        >>> b = NaturalBag({'a': 1, 'c': 2, 'd': 5})
        >>> b.update({'a': -4, 'b': -1, 'c': -2, 'd': -2})
        >>> print b
        {'d': 3}

        NOTE:  Exceptions are only reported on the last bad element encountered.
        """
        #XXX may be able to improve this by calling dict methods directly and/or using map and operator functions
        #XXX should raise exception and return unchanged self if problem encountered!
        #XXX or use logging.warning() and continue
        error = False
        if isinstance(items, dict):
            for key, count in items.iteritems():
                try:
                    self[key] += count  #may be slower than necessary
                except TypeError, error: pass
        else: #sequence
            for key in items:
                try:
                    self[key] += count
                except TypeError, error: pass
        if error: raise TypeError, error

    def pick(self, count=1, remove=True):
        """Returns a bag with 'count' random items from bag (defaults to 1), removing the items unless told otherwise.

        >>> b = IntegerBag({'a': 3, 'b': -2, 'c': 1})
        >>> sub = b.pick(4)
        >>> sub.size, b.size
        (4, 2)
        """
        l = list(self.itereach())
        picked = IntegerBag(random.sample(l, min(abs(count), len(l))))
        if count < 0:  picked *= (-1)  #this probably not useful
        if remove: self -= picked
        return picked

    def discard(self, item):
        """Removes all of the specified item if it exists, otherwise ignored.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> b.discard('b')
        >>> b.discard('d')  #non-existent items ignored
        >>> print b
        {'a': 3, 'c': 1}
        """
        try: del self[item] #note: this does not call __getitem__
        except KeyError: pass

    def setdefault(self, item, count=1):
        count = self._filter(count)
        return count and dict.setdefault(self, item, count)

    def itereach(self):
        """Will iterate through all items in bag individually.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> l = list(b.itereach()); l.sort()
        >>> l
        [('a', 1), ('a', 1), ('a', 1), ('b', 1), ('b', 1), ('c', 1)]
        >>> b = IntegerBag(b)
        >>> b['b'] = -2
        >>> l = list(b.itereach()); l.sort()
        >>> l
        [('a', 1), ('a', 1), ('a', 1), ('b', -1), ('b', -1), ('c', 1)]

        Note: iteration on bag itself just iterates through unique keys:
        >>> l = list(b) ; l.sort()
        >>> l
        ['a', 'b', 'c']
        """
        for key, count in self.iteritems():
            for i in xrange(abs(count)):
                yield (key, count >= 0 and 1 or -1) #consider returning (key, +/-1) pair to account for negative counts

    def __iadd__(self, other):
        """Add items in bag.

        >>> b = NaturalBag()
        >>> b += [1, 2, 1, 0]
        >>> print b
        {0: 1, 1: 2, 2: 1}
        >>> b.clear()
        >>> b += "abca"
        >>> print b
        {'a': 2, 'b': 1, 'c': 1}
        """
        self.update(other, 1)  #XXX may fail mid-update...
        return self

    def __add__(self, other):
        """Add one bag to another, returns type of first bag.

        >>> b = IntegerBag({1: 2, 2: -2}) + NaturalBag({1: 5, 2: 1, 3: 7})
        >>> b, type(b)
        ({1: 7, 2: -1, 3: 7}, <class 'bag.IntegerBag'>)
        """
        return self.__class__(self).__iadd__(other)

    def __isub__(self, other):
        """Subtract items from bag.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> b -= "cccccab"
        >>> print b
        {'a': 2, 'b': 1}
        """
        if isinstance(other, dict):
            other = IntegerBag(other) * (-1)
        self.update(other, -1)
        return self

    def __sub__(self, other):
        """Subtract items from bag.

        >>> IntegerBag({1: 2, 2: -2}) - {1: 5, 2: -2, 3: 7}
        {1: -3, 3: -7}
        """
        return self.__class__(self).__isub__(other)

    def __imul__(self, factor):
        """Multiply bag contents by factor.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> b *= 4
        >>> print b
        {'a': 12, 'b': 8, 'c': 4}

        Negative factors can be used with IntegerBag.
        >>> ib = IntegerBag(b)
        >>> ib *= -1
        >>> print ib
        {'a': -12, 'b': -8, 'c': -4}

        Trying that on a NaturalBag will return empty bag (akin to list behavior).
        >>> b *= -1
        >>> b
        {}

        Zero factors will return empty bag.
        >>> b += "abacab"
        >>> b *= 0
        >>> b
        {}

        """
        if self._filter(factor):
            for item, count in self.iteritems():
                dict.__setitem__(self, item, count*factor) #bypass test logic in bag.__setitem__
        else:   #factor==0 or negative on NaturalBag
            dict.clear(self)    #call dict.clear to protect subclass which might override and do other things besides clear dict values
        return self

    def __mul__(self, factor):
        """Returns new bag of same type multiplied by factor.

        >>> d = {1: 2, 2: 4, 3: -9}
        >>> IntegerBag(d) * -1
        {1: -2, 2: -4, 3: 9}
        >>> NaturalBag(d) * -1
        {}
        """
        #XXX should perhaps use explicit IntBag in case derived class needs parameters -- or use copy()???
        return self.__class__(self).__imul__(factor)

    def _size(self):
        """Returns sum of absolute value of item counts in bag.

        >>> b = IntegerBag.fromkeys("abacab")
        >>> b['a'] = -4
        >>> b.size
        7
        """
        return sum(map(abs, self.itervalues()))

    size = property(_size, None, None, None)

    def __getitem__(self, item):
        """Returns total count for given item, or zero if item not in bag.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> b['a']
        3
        >>> b['d']
        0
        """
        return self.get(item, 0)

    count = __getitem__

    def __setitem__(self, item, count):
        """Sets the count for the given item in bag, removing if zero.

        >>> b = NaturalBag()
        >>> b[1] = 3
        >>> b[2] = 2L   #long values okay
        >>> b[3] = 1.6  #floats get coerced to ints
        >>> b[4] = "2"  #as do int strings
        >>> print b
        {1: 3, 2: 2, 3: 1, 4: 2}

        If count is zero, all 'matching items' are deleted from bag.
        >>> b[2] = 0
        >>> print b
        {1: 3, 3: 1, 4: 2}

        Counts for IntegerBag are allowed to be negative.
        >>> ib = IntegerBag(b)
        >>> ib[4] = -2
        >>> ib[5] -= 2
        >>> ib[1] -= 4
        >>> ib[3] -= 1
        >>> print ib
        {1: -1, 4: -2, 5: -2}

        Trying to set negative values on NaturalBag reverts to zero.
        >>> b[4] = -2
        >>> b[4]
        0

        If count is non-integer, TypeError is raised.
        >>> b[1] = "oops"
        Traceback (most recent call last):
        ValueError: invalid literal for int(): oops
        """
        count = self._filter(count)
        if count:
            dict.__setitem__(self, item, count)  #XXX should this call super instead of dict (for cases of multiple inheritence etc...)
        else:   #setting to 0 so discard key
            self.discard(item)

    def __str__(self):
        """Convert self to string with items in sorted order.

        >>> str(IntegerBag())
        '{}'
        >>> str(IntegerBag({'b': -2, 'a': 3, 'c': 1, 1: 0}))
        "{'a': 3, 'b': -2, 'c': 1}"
        >>> str(NaturalBag.fromkeys("abacab"))
        "{'a': 3, 'b': 2, 'c': 1}"
        """
        #sort by values, largest first? should we sort at all?
        if _DEBUG: self._validate()
        if not self: return '{}'    #nothing to sort
        keys = self.keys()
        keys.sort()
        return '{%s}' % ', '.join(["%r: %r" % (k, self[k]) for k in keys])

    def _filter(value): #XXX coult just set _filter = int but doctest complains
        """Coerces value to int and returns it, or raise raises TypeError."""
        return int(value)

    _filter = staticmethod(_filter)

    def _validate(self):
        """Check class invariants.

        >>> b = IntegerBag.fromkeys("abc")
        >>> dict.__setitem__(b, 'a', "oops")
        >>> b._validate()
        Traceback (most recent call last):
        ValueError: invalid literal for int(): oops
        >>> b = NaturalBag()
        >>> dict.__setitem__(b, 'a', 0)    #zero values are normally deleted
        >>> b
        {'a': 0}
        >>> b._validate()
        Traceback (most recent call last):
        AssertionError: zero value encountered
        >>> b = NaturalBag()
        >>> dict.__setitem__(b, 'a', -1)   #negative values not allowed
        >>> b._validate()
        Traceback (most recent call last):
        AssertionError: unfiltered value
        """
        for count in self.itervalues():
            assert count == self._filter(count), "unfiltered value"
            assert count, "zero value encountered"


class NaturalBag(IntegerBag):
    """Standard bag class.  Allows only non-negative bag counts."""

    __slots__ = []

    def _size(self):
        """Returns total number of items in bag.

        >>> b = NaturalBag.fromkeys("abacab")
        >>> b.size
        6
        """
        return sum(self.itervalues())

    size = property(_size, None, None, None)

    def _filter(value):
        """Returns 0 if value is negative. """
        return max(int(value), 0)

    _filter = staticmethod(_filter)


def _test():
    """Miscillaneous tests:

    Equality test.  Can compare against dictionary or bag types.
    >>> NaturalBag.fromkeys("abacab") == {'a': 3, 'b': 2, 'c': 1}
    True
    >>> b, l = NaturalBag.fromkeys([1, 2, 1, 3, 1]), [1, 1, 1, 3, 2]
    >>> b == l
    False
    >>> b == NaturalBag.fromkeys(l) == IntegerBag.fromkeys(l)
    True

    Tests for non-zero:
    >>> b = NaturalBag()
    >>> bool(b)
    False
    >>> b += [0]
    >>> bool(b)
    True
    """
    import doctest, bag
    return doctest.testmod(bag, isprivate=lambda *args: 0)

if __name__ == "__main__":
    _test()

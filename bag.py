#!/usr/bin/env python
# Mark Janssen,  July 1, 2002

"""Bag types"""

__version__ = "$Revision: 2.7 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2003/06/10 00:36:07 $"

#bag should have list interface? --should add list methods: append, remove, min/max,  __str__ return list string, etc.
#   in addition to min/max(), perhaps create most/least() to return the item with the highest/lowest count
#XXX figure out what should happen: bag[nokey] -= 5, bag[key] -=5
#XXX checking in setitem takes too much time: create compress function that removes zero-valued items periodically
#create bag attribute to hold size of bag and calculate only when bag has been written to.
#perhaps limit bag to either list or dict types for adding/updating.

from __future__ import generators

if 'sum' not in dir(__builtins__):
    import operator
    def sum(iterable):
        return reduce(operator.add, iterable, 0)

IntegerType = (int, long)

class imbag(dict):
    """Implements a bag type that allows item counts to be negative."""

    __slots__ = []

    def __init__(self, init={}):
        """Initialize bag with optional contents.

        >>> b = bag()   #creates empty bag
        >>> b
        {}
        >>> print imbag({1: -1, 2: 0, 3: -9})
        {1: -1, 3: -9}

        Can initialize with (key, count) list as in standard dict.
        However, duplicate keys will accumulate counts:
        >>> print bag([(1, 2), (2, 4), (1, 7)])
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

        >>> b = bag({'b': 2, 'c': 1, 'a': 3})
        >>> b2 = bag.fromkeys(['a', 'b', 'c', 'b', 'a', 'a'])
        >>> b3 = bag.fromkeys("abacab")
        >>> assert b == b2 == b3

        >>> word_count = bag.fromkeys("how much wood could a wood chuck chuck".split())
        >>> print word_count
        {'a': 1, 'chuck': 2, 'could': 1, 'how': 1, 'much': 1, 'wood': 2}

        An optional count can be specified.  Count added each time item is encountered.
        >>> print bag.fromkeys("abacab", 5)
        {'a': 15, 'b': 10, 'c': 5}
        """
        b = cls()
        for key in iterable:
            b[key] += count  #perhaps slower than necessary but will simplify derived classes that override __setitem__()
        return b

    fromkeys = classmethod(fromkeys)

    def update(self, items):
        """Adds contents to bag from other dictionary type.

        >>> ib = imbag.fromkeys('abc')
        >>> ib.update({'a': 2, 'b': 1, 'c': 0})
        >>> print ib
        {'a': 3, 'b': 2, 'c': 1}

        Negative updates are allowable.
        >>> ib.update({'a': -2, 'b': -2, 'c': -2, 'd': 2})
        >>> print ib
        {'a': 1, 'c': -1, 'd': 2}

        Invalid values are skipped, and will raise TypeError.
        >>> ib.update({0: 'test1', 'a': 'test2', 'd': 3, 'f': 1.0, 'c': 2.0})
        Traceback (most recent call last):
        ...
        TypeError: must use integral type for bag values, not <type 'float'>
        >>> print ib
        {'a': 1, 'c': -1, 'd': 5}

        Updating bag with values that would cause the count to go negative raises ValueError,
        leaving value unaffected.  Other elements still get updated:
        >>> b = bag({'a': 1, 'c': 2, 'd': 5})
        >>> b.update({'a': -4, 'c': -2, 'd': -2})
        Traceback (most recent call last):
        ...
        ValueError: bag values must be non-negative: -4
        >>> print b
        {'a': 1, 'd': 3}

        NOTE:  Exceptions above are only reported on the first bad element encountered.
        """
        #XXX may be able to improve this by calling dict methods directly and/or using map and operator functions
        #we don't want to abort mid-update, so validate at end of loop
        #XXX should raise exception and return unchanged self if problem encountered!
        bad_value_encountered = False
        for key, count in items.iteritems():
            try:
                self[key] += count  #may be slower than necessary
            except (TypeError, ValueError):
                bad_value_encountered, bad_value = True, count
        if bad_value_encountered: self._check_value(bad_value)

    def pop(self):
        """Removes and returns one item from the bag."""
        raise NotImplementedError #XXX

    def discard(self, item):
        """Removes all of the specified item if it exists, otherwise ignored.

        >>> b = bag.fromkeys("abacab")
        >>> b.discard('b')
        >>> b.discard('d')  #non-existent items ignored
        >>> print b
        {'a': 3, 'c': 1}
        """
        #XXX what if imbag bag counts are negative?
        try: del self[item]
        except KeyError: pass

    def setdefault(self, item, count=1):
        #XXX perhaps remove this on bag, may not even be accurate
        self._check_value(count)
        if count:  return dict.setdefault(self, item, count)
        else:  return self[item]

    def __iadd__(self, iterable):
        """Add items in iterable object to bag.

        >>> b = bag()
        >>> b += [1, 2, 1, 0]
        >>> print b
        {0: 1, 1: 2, 2: 1}
        >>> b.clear()
        >>> b += "abca"
        >>> print b
        {'a': 2, 'b': 1, 'c': 1}
        """
        for key in iterable:
            self[key] += 1
        return self

    def __isub__(self, iterable):
        """Subtract items in iterable object from bag.

        >>> b = bag.fromkeys("abacab")
        >>> b -= "cab"
        >>> print b
        {'a': 2, 'b': 1}
        """
        #XXX Should this method be removed? (list doesn't support it)  What should happen if item not in bag?
        #XXX what should happen if item doesn't exist?
        for item in iterable:
            self[item] -= 1
        return self

    def __imul__(self, factor):
        """Multiply bag contents by factor.

        >>> b = bag.fromkeys("abacab")
        >>> b *= 4
        >>> print b
        {'a': 12, 'b': 8, 'c': 4}

        Negative factors can be used with imbag.
        >>> ib = imbag(b)
        >>> ib *= -1
        >>> print ib
        {'a': -12, 'b': -8, 'c': -4}

        Trying that on a standard bag will raise ValueError.
        >>> b *= -1
        Traceback (most recent call last):
        ...
        ValueError: bag values must be non-negative: -1

        Zero factors will return empty bag.
        >>> b *= 0
        >>> b
        {}

        """
        self._check_value(factor)
        if factor:
            for item, count in self.iteritems():
                dict.__setitem__(self, item, count*factor) #bypass test logic in bag.__setitem__
        else:   #factor==0
            dict.clear(self)    #call dict.clear to protect subclass which might override and do other things besides clear dict values
        return self

    def __abs__(self):
        """Returns sum of absolute value of item counts in bag.

        >>> b = imbag.fromkeys("abacab")
        >>> b['a'] = -4
        >>> abs(b)
        7
        """
        return sum(map(abs, self.itervalues()))

    def __getitem__(self, item):
        """Returns total count for given item, or zero if item not in bag.

        >>> b = bag.fromkeys("abacab")
        >>> b['a']
        3
        >>> b['d']
        0
        """
        if item in self: #seems faster than try/except
            return dict.__getitem__(self, item)
        else:
            return 0

    count = __getitem__

    def __setitem__(self, item, count):
        """Sets the count for the given item in bag, removing if zero.

        >>> b = bag.fromkeys([1, 2, 3])
        >>> b[1] = 3
        >>> b[4] = 2L   #long values okay
        >>> print b
        {1: 3, 2: 1, 3: 1, 4: 2L}

        If count is zero, all 'matching items' are deleted from bag.
        >>> b[2] = 0
        >>> print b
        {1: 3, 3: 1, 4: 2L}

        Counts for imbag are allowed to be negative.
        >>> ib = imbag(b)
        >>> ib[4] = -2
        >>> ib[5] -= 2
        >>> ib[1] -= 4
        >>> ib[3] -= 1
        >>> print ib
        {1: -1, 4: -2, 5: -2}

        Setting negative values on standard bag raises ValueError.
        >>> b[4] = -2
        Traceback (most recent call last):
        ...
        ValueError: bag values must be non-negative: -2

        If count is non-integer, TypeError is raised.
        >>> b[1] = "oops"
        Traceback (most recent call last):
        ...
        TypeError: must use integral type for bag values, not <type 'str'>
        """
        self._check_value(count)
        if count:
            dict.__setitem__(self, item, count)
        else:   #setting to 0 so delete key
            try:  del self[item]
            except LookupError:  pass

    def __iter__(self):
        """Will iterate through all items in bag individually.

        >>> b = bag.fromkeys("abacab")
        >>> l = list(b); l.sort()
        >>> l
        ['a', 'a', 'a', 'b', 'b', 'c']
        >>> b = imbag(b)
        >>> b['b'] = -2
        >>> l = list(b); l.sort()
        >>> l
        ['a', 'a', 'a', 'b', 'b', 'c']

        If you want to iterate through unique keys in bag, use iterkeys():
        >>> l = list(b.iterkeys()) ; l.sort()
        >>> l
        ['a', 'b', 'c']
        """
        #XXX list(b) != imbag(list(b))
        for key, count in self.iteritems():
            for i in xrange(abs(count)):
                yield key

    def __str__(self):
        """Convert self to string with items in sorted order.

        >>> str(imbag())
        '{}'
        >>> str(imbag({'b': -2, 'a': 3, 'c': 1, 1: 0}))
        "{'a': 3, 'b': -2, 'c': 1}"
        >>> str(bag.fromkeys("abacab"))
        "{'a': 3, 'b': 2, 'c': 1}"
        """
        #sort by values, largest first? should we sort at all?
        if not self: return '{}'    #nothing to sort
        self._validate()
        keys = self.keys()
        keys.sort()
        return '{%s}' % ', '.join(["%r: %r" % (k, self[k]) for k in keys])

    def _check_value(value):
        """Raises TypeError if value is not integral type."""
        if not isinstance(value, IntegerType):
            raise TypeError("must use integral type for bag values, not %r" % type(value))

    _check_value = staticmethod(_check_value)

    def _validate(self):
        for count in self.itervalues():
            self._check_value(count)
            assert count


class bag(imbag):
    """Standard bag class.  Allows only non-negative bag counts."""

    __slots__ = []

    def __len__(self):
        """Returns total number of items in bag.

        >>> b = bag.fromkeys("abacab")
        >>> len(b)
        6
        """
        return sum(self.itervalues())

    def _check_value(value):
        """Tests baseclass invariants, plus raises ValueError if value is negative. """
        imbag._check_value(value)
        if value < 0:
            raise ValueError("bag values must be non-negative: %r" % value)

    _check_value = staticmethod(_check_value)


def _test():
    """Miscillaneous tests:

    Equality test.  Can compare against dictionary or bag types.
    >>> bag.fromkeys("abacab") == {'a': 3, 'b': 2, 'c': 1}
    True
    >>> b, l = bag.fromkeys([1, 2, 1, 3, 1]), [1, 1, 1, 3, 2]
    >>> b == l
    False
    >>> b == bag.fromkeys(l) == imbag.fromkeys(l)
    True

    Tests for non-zero:
    >>> b = bag()
    >>> bool(b)
    False
    >>> b += [0]
    >>> bool(b)
    True
    """
    import doctest, bag
    return doctest.testmod(bag, isprivate=lambda i, j: 0)

if __name__ == "__main__":
    _test()

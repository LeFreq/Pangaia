# -*- coding: utf-8 -*-
# This file is part of the pangaia project.
# Mark Janssen, dreamingforward@gmail.com, Santa Fe, NM

#Ideally would dict inherit from set.
#Ideally would have ABCs "compound" type with a default value when no second parameter.

"""
A module defining a fractal (recursive) dictionary type.

The purpose of this module is to implement the unifed information model of the pangaia project 
and hopefully contribute to an ideal of Python 3000.
"""

import sys
from collections import Counter

#sys.setrecursionlimit(50)

class Mdict(Counter):
    """Metadict:  for every operation d1 op d2, apply op to values where
    keys are in common. Cannot do arbitrary functions without breaking meta
    abstraction.  One level of recursion should be sufficient for real apps?
    """

    #With any "meta"-type, one must define a base-case that informs how one should perform grouping.
    #NOTE:  it's up to you to make each operation meaningful on your leaf-values.

    def __init__(self, *args, **kwargs):
        """Initialize meta dict.  All values should be homogeneous or other MetaRecurs type."""
        super(Mdict, self).__init__(*args, **kwargs)

    def __add__(self, other):
        """Add together, with recursion.  The basic idea is that the set of keys
        should be added together and then recurse the addition to the values where keys are shared
        otherwise just add the value.

        >>> m, m2 = Mdict('a'), Mdict('abb')
        >>> m + m2 == {'a':2, 'b':2}
        True
        >>> m + 1 == {None:1, 'a':1}
        True
        >>> m['a'] = m2  #now fractal
        >>> m == {'a': {'a':1, 'b':2}}
        True
        >>> m + m + 1 == {'a': {'a':2, 'b':4}, None: 1}
        True
        """
        try: # need to add (union) of keys, and then recurse into values of common keys
            return Mdict(Counter.__add__(self, other)) #Counter.__add__(self, other)
        except TypeError: #must've been an integer for other
            return Mdict(Counter.__add__(self, Counter({None: other})))
    
        #    self += set(other.keys()) #base case for group
#
##        except AttributeError: #no keys() method
##            try:
##                self[None] += other
##            except TypeError(other):
##                print other + " must be integer."

    #def __iadd__(self, other):
        

    def __radd__(self, other):
        """Add int to group.

        >>> m = Mdict('a')
        >>> 1 + m == {None:1, 'a':1}
        True
        """
        #print self,other
        return self + other
                


if __name__ == "__main__":

    #m = Mdict('a')
    #print m
    #m2 = Mdict('abb')
    #print m2
    
    #print m+ m2
    #print m + 1
    import doctest

    doctest.testmod()

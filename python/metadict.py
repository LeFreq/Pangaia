# Mark Janssen, dreamingforward@gmail.com, Santa Fe, NM

#Ideally would dict inherit from set.
#Ideally would have ABS compound type with a default value when no second parameter.

"""
A module defining a fractal (multi-level) dictionary type.
"""

class Mdict(dict):
    """Metadict:  for every operation d1 op d2, apply op to values where
    keys are in common. Cannot do arbitrary functions without breaking meta
    abstraction.  One level of recursion should be sufficient for real apps?
    """

    #NOTE:  it's up to you to make each operation meaningful on your leaf-values.

#    def __init__(self, init={}):
#        """Initialize meta dict.  All values should be homogeneous or other MetaRecurs type."""
    

    def __add__(self, other):
        """Add together,...

        >>> d + d2 == {'a':2, 'b':2}
        >>> d + 1 == {None:1, 'a':1}
        True
        >>> d['a'] = d2  #now fractal
        >>>
        """
        try: # need to add (union) of keys, and then recurse into values of common keys
            self += set(other.keys()) #base case for group

            for k in newdict:
                if k in self and k in other:     #recurs
                    newdict[k] = self[k] + other[k]
                else:
                    try:
                        newdict[k] = self[k]
                    except:
                        newdict[k] = other[k]
        
            return Mdict(newdict)  #shouldn't recurs
        except AttributeError:
            try:
                self[None] += other
            except TypeError(other):
                print other + " must be integer."

    def __radd__(self, other):
        """Add int to group.

        >>> 1 + d == {None:1, 'a':1}
        True
        """
        #print self,other
        return self + other
                

    def __getitem__(self, key):
        return self.get(key, 0)

    def update(self, other):
        return self + other


if __name__ == "__main__":

    d = Mdict({'a':1})
    d2 = Mdict({'a':1, 'b':2})

    import doctest

    doctest.testmod()

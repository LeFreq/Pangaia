"""An expanded dictionary class with set operations in Python.
This class implements sets as dictionaries whose values are ignored
but preserved.  The usual operations (union, intersection, deletion,
etc.) are provided as both methods and operators.
"""

__version__ = "$Revision: 1.3 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/07/08 04:22:56 $"

from copy import deepcopy, copy

#XXX make set operators consistent wrt key collision handling and parameter types
# enhance set operators with optional "collision_function" parameter that is called when a key exists in both dictionaries
#  default to (lambda s, o: o), but could also provide (lambda s, o: s+o) for example, or (lambda s,o: o.copy())

default_value = None  #unless specified otherwise, values get assigned default_value

class DictSet(dictionary):

    #----------------------------------------
    def __init__(self, init=None, value=default_value):
        """Construct a set, optionally initializing it with elements
        drawn from an iterable object.  If value is passed,
        then all new elements get assigned it unless told otherwise."""

        dictionary.__init__(self)
        if init is not None:
            self.update(init, value) #will try dictionary.update first

    #----------------------------------------
    def __str__(self):
        """Return string in sorted standard set notation."""
        content = self.keys()
        content.sort()
        return '{' + str(content)[1:-1] + '}'

    #----------------------------------------
    # Comparisons
    def __lt__(self, other):
        """Return true if self is proper subset of other."""
        if not isinstance(other, dictionary):
            return type(self) < type(other)
        return len(self) < len(other) and self._within(other)

    def __le__(self, other):
        """Return true if self is subset or equal to other."""
        if not isinstance(other, dictionary):
            return type(self) <= type(other)
        return len(self) <= len(other) and self._within(other)

    def __eq__(self, other):
        return isinstance(other, dictionary) and len(self)==len(other) and self._within(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if not isinstance(other, dictionary):
            return type(self) > type(other)
        return len(self) > len(other) and self._altwithin(other)

    def __ge__(self, other):
        if not isinstance(other, dictionary):
            return type(self) >= type(other)
        return len(self) >= len(other) and self._altwithin(other)

    is_subset_of        = __le__
    is_proper_subset_of = __lt__

    #----------------------------------------
    def __copy__(self):  #XXX necessary?
        """Return a shallow copy of the set."""
        return self.__class__(init=self)

    #----------------------------------------
    # Define 'copy' method as readable alias for '__copy__'.
    # Overrides dictionary.copy()
    copy = __copy__

    #----------------------------------------
    def __deepcopy__(self, memo):
        #XXX since no more hash value, couldn't this be simpler?
        result          = self.__class__()
        memo[id(self)]  = result
        for elt in self:
            result[deepcopy(elt, memo)] = deepcopy(self[elt], memo)  #XXX?
        return result

    #----------------------------------------
    def union_update(self, other):
        """Update set with union of its own elements and the elements
        in another set."""

        self.update(other)
        return self

    #----------------------------------------
    def union(self, other):
        """Create new set whose elements are the union of this set's
        and another's."""

        result = self.__class__(init=self)
        result.update(other)
        return result

    #----------------------------------------
    # intersect should probably keep value of other set to be consistent w/update()
    def intersect_update(self, other):
        """Update set with intersection of its own elements and the
        elements in another set.  Does not affect values of self."""

        for elt in self.keys():  #make copy since modifying below
            if elt not in other: #XXX slow if other is list
                del self[elt]
        return self

    #----------------------------------------
    def intersect(self, other):
        """Create new set whose elements are the intersection of this
        set's and another's.  Retains values of self."""

        if len(self) <= len(other) and isinstance(other, dictionary):
            little, big = self, other
        else:
            little, big = other, self
        result = self.__class__()
        for elt in little:
            if elt in big:
                result[elt] = self[elt]
        return result

    #----------------------------------------
    def sym_difference_update(self, other):
        """Update set with symmetric difference of its own elements
        and the elements in another set.  A value 'x' is in the result
        if it was originally present in one or the other set, but not
        in both."""

        if not isinstance(other, dictionary):
            raise ValueError, "Set operation only permitted between dictionary types."
        for elt in other:
            try:
                del self[elt]
            except LookupError:
                self[elt] = other[elt]
        return self

    #----------------------------------------
    def sym_difference(self, other):
        """Create new set with symmetric difference of this set's own
        elements and the elements in another set.  A value 'x' is in
        the result if it was originally present in one or the other
        set, but not in both."""

        if not isinstance(other, dictionary):
            raise ValueError, "Set operation only permitted between dictionary types."
        result = self.__class__(init=self)
        for elt in other:
            try:
                del result[elt]
            except LookupError:
                result[elt] = other[elt]
        return result

    #----------------------------------------
    def difference_update(self, other):
        """Remove all elements of another set from this set."""

        if len(self):
            for elt in other:
                self.discard(elt)
        return self

    #----------------------------------------
    def difference(self, other):
        """Create new set containing elements of this set that are not
        present in another set."""

        result = self.__class__(init=self)
        if len(result):
            for elt in other:
                result.discard(elt)
        return result

    #----------------------------------------
    # Arithmetic forms of operations
    __or__      = union
    __ror__     = union
    __ior__     = union_update
    __and__     = intersect
    __rand__    = intersect
    __iand__    = intersect_update
    __xor__     = sym_difference
    __rxor__    = sym_difference
    __ixor__    = sym_difference_update
    __sub__     = difference
    __rsub__    = difference
    __isub__    = difference_update

    #----------------------------------------
    def add(self, item, value=default_value):
        """Add a hashable item to a set.  This has no effect if the item is
        already present."""

        if item not in self:
            self[item] = value

    #----------------------------------------
    def update(self, iterable, value=default_value):
        """Add all values from an iteratable (such as a tuple, list,
        or file) to this set."""

        try:
            dictionary.update(self, iterable)
        except AttributeError:
            for item in iterable:  #if item not in self: self[item]=value faster??
                self[item] = value

    #----------------------------------------
    def discard(self, item):
        """Remove an element from a set if it is present, or do
        nothing if it is not."""

        try:
            del self[item]
        except KeyError:
            pass

    #----------------------------------------
    def pop(self):
        """Remove and return a randomly-chosen set element."""

        return dictionary.popitem(self)[0]

    #----------------------------------------
    def _within(self, other):
        """Return true if all elements of self are contained in other."""
        for elt in self:
            if elt not in other:
                return 0
        return 1

    def _altwithin(self, other):
        """Return true if all elements of other are contained in self."""
        for elt in other:
            if elt not in self:
                return 0
        return 1


#----------------------------------------------------------------------
# Rudimentary self-tests
#----------------------------------------------------------------------

if __name__ == "__main__":

    # Empty set
    red = DictSet()
    assert str(red) == "{}", "Empty set: %s" % `red`

    # Unit set
    green = DictSet((0,))
    assert str(green) == "{0}", "Unit set: %s" % `green`

    # 3-element set
    blue = DictSet([0, 1, 2])
    assert str(blue) == "{0, 1, 2}", "3-element set: %s" % `blue`

    # 2-element set with other values
    black = DictSet([0, 5])
    assert str(black) == "{0, 5}", "2-element set: %s" % `black`

    # All elements from all sets
    white = DictSet([0, 1, 2, 5])
    assert str(white) == "{0, 1, 2, 5}", "4-element set: %s" % `white`

    # Add element to empty set
    red.add(9)
    assert str(red) == "{9}", "Add to empty set: %s" % `red`

    # Remove element from unit set
    del red[9]
    assert str(red) == "{}", "Remove from unit set: %s" % `red`

    # Remove element from empty set
    try:
        del red[0]
        assert 0, "Remove element from empty set: %s" % `red`
    except LookupError:
        pass

    # Length
    assert len(red) == 0,   "Length of empty set"
    assert len(green) == 1, "Length of unit set"
    assert len(blue) == 3,  "Length of 3-element set"

    # Compare
    assert green == DictSet([0]),   "Equality failed"
    assert green != DictSet([1]),   "Inequality failed"
    assert green < DictSet([0, 1]), "Less-than failed"
    assert green <= DictSet([0]),   "Less-than-or-equal failed"
    assert green > DictSet([]),     "Greater-than failed"
    assert green >= DictSet([0]),   "Greater-than-or-equal failed"

    # Union
    assert blue  | red   == blue,  "Union non-empty with empty"
    assert red   | blue  == blue,  "Union empty with non-empty"
    assert green | blue  == blue,  "Union non-empty with non-empty"
    assert blue  | black == white, "Enclosing union"

    # Intersection
    assert blue  & red   == red,   "Intersect non-empty with empty"
    assert red   & blue  == red,   "Intersect empty with non-empty"
    assert green & blue  == green, "Intersect non-empty with non-empty"
    assert blue  & black == green, "Enclosing intersection"

    # Symmetric difference
    assert red ^ green == green,        "Empty symdiff non-empty"
    assert green ^ blue == DictSet([1, 2]), "Non-empty symdiff"
    assert white ^ white == red,        "Self symdiff"

    # Difference
    assert red - green == red,           "Empty - non-empty"
    assert blue - red == blue,           "Non-empty - empty"
    assert white - black == DictSet([1, 2]), "Non-empty - non-empty"

    # In-place union
    orange = DictSet([])
    orange |= DictSet([1])
    assert orange == DictSet([1]), "In-place union"

    # In-place intersection
    orange = DictSet([1, 2])
    orange &= DictSet([2])
    assert orange == DictSet([2]), "In-place intersection"

    # In-place difference
    orange = DictSet([1, 2, 3])
    orange -= DictSet([2, 4])
    assert orange == DictSet([1, 3]), "In-place difference"

    # In-place symmetric difference
    orange = DictSet([1, 2, 3])
    orange ^= DictSet([3, 4])
    assert orange == DictSet([1, 2, 4]), "In-place symmetric difference"


    print "All tests passed"

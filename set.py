"""A class to represent sets in Python.
This class implements sets as dictionaries whose values are ignored.
The usual operations (union, intersection, deletion, etc.) are
provided as both methods and operators.  The only unusual feature of
this class is that once a set's hash code has been calculated (for
example, once it has been used as a dictionary key, or as an element
in another set), that set 'freezes', and becomes immutable.  See
PEP-0218 for a full discussion.
"""

__version__ = "$Revision: 1.5 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2001/09/28 04:30:19 $"

from copy import deepcopy

class Set(dictionary):

    # Displayed when operation forbidden because set has been frozen
    _Frozen_Msg = "Set is frozen: %s not permitted"

    #----------------------------------------
    def __init__(self, iterable=None):
        """Construct a set, optionally initializing it with elements
        drawn from an interable object.  The 'hashcode' element is
        given a non-None value the first time the set's hashcode is
        calculated; the set is frozen thereafter."""

        dictionary.__init__(self)
        if iterable is not None:
            try:
                self.update(iterable)
            except AttributeError:
                for item in iterable:
                    self[item] = None
        self.hashcode = None

    #----------------------------------------
    def __str__(self):
        """Return sorted set string in standard notation."""
        content = self.keys()
        content.sort()
        content = map(str, self.keys())  #XXX
        return '{' + ', '.join(content) + '}'

    def __repr__(self):
        """Convert set to string."""
        return 'Set(' + `self.keys()` + ')'

    #----------------------------------------
    def __iter__(self):
        """Return iterator for enumerating set elements.  This is a
        keys iterator for the underlying dictionary."""
        return self.iterkeys()

    #----------------------------------------
    # Comparisons
    # XXX should not assume dictionary values equal to None
    def __lt__(self, other):
        return self._generic_cmp(other, dictionary.__lt__)

    def __le__(self, other):
        return self._generic_cmp(other, dictionary.__le__)

    def __eq__(self, other):
        return self._generic_cmp(other, dictionary.__eq__)

    def __ne__(self, other):
        return self._generic_cmp(other, dictionary.__ne__)

    def __gt__(self, other):
        return self._generic_cmp(other, dictionary.__gt__)

    def __ge__(self, other):
        return self._generic_cmp(other, dictionary.__ge__)

    def __eq__(self, other):
        #won't compare dictionary values
        if not isinstance(other, Set) or len(self)!=len(other):
            return 0
        for i in self:
            if i not in other:
                return 0
        return 1
    def __ne__(self, other):
        return not self.__eq__(other)


    #----------------------------------------
    def __hash__(self):
        """Calculate hash code for set by xor'ing hash codes of set
        elements.  This algorithm ensures that the hash code does not
        depend on the order in which elements are added to the
        code."""

        # If set already has hashcode, the set has been frozen, so
        # code is still valid.
        if self.hashcode is not None:
            return self.hashcode

        # Combine hash codes of set elements to produce set's hash code.
        self.hashcode = 0
        for elt in self:
            self.hashcode ^= hash(elt)
        return self.hashcode

    #----------------------------------------
    def is_frozen(self):
        """Report whether set is frozen or not.  A frozen set is one
        whose hash code has already been calculated.  Frozen sets may
        not be mutated, but unfrozen sets can be."""

        return self.hashcode is not None

    #----------------------------------------
    def __copy__(self):
        """Return a shallow copy of the set."""
        return Set(self)

    #----------------------------------------
    # Define 'copy' method as readable alias for '__copy__'.
    # Overrides dictionary.copy()
    copy = __copy__

    #----------------------------------------
    def __deepcopy__(self, memo):
        result          = Set()
        memo[id(self)]  = result
        for elt in self:
            result[deepcopy(elt, memo)] = None
        return result

    #----------------------------------------
    def clear(self):
        """Remove all elements of unfrozen set."""
        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "clearing"
        dictionary.clear(self)

    #----------------------------------------
    def union_update(self, other):
        """Update set with union of its own elements and the elements
        in another set."""

        self._binary_sanity_check(other, "updating union")
        self.update(other)
        return self

    #----------------------------------------
    def union(self, other):
        """Create new set whose elements are the union of this set's
        and another's."""

        self._binary_sanity_check(other)
        result = Set(self)
        result.update(other)
        return result

    #----------------------------------------
    def intersect_update(self, other):
        """Update set with intersection of its own elements and the
        elements in another set."""

        self._binary_sanity_check(other, "updating intersection")
        for elt in self.keys():
            if elt not in other:
                del self[elt]
        return self

    #----------------------------------------
    def intersect(self, other):
        """Create new set whose elements are the intersection of this
        set's and another's."""

        self._binary_sanity_check(other)
        if len(self) <= len(other):
            little, big = self, other
        else:
            little, big = other, self
        result = Set()
        for elt in little:
            if elt in big:
                result[elt] = None
        return result

    #----------------------------------------
    def sym_difference_update(self, other):
        """Update set with symmetric difference of its own elements
        and the elements in another set.  A value 'x' is in the result
        if it was originally present in one or the other set, but not
        in both."""

        self._binary_sanity_check(other, "updating symmetric difference")
        for elt in other:
            try:
                del self[elt]
            except LookupError:
                self[elt] = None
        return self

    #----------------------------------------
    def sym_difference(self, other):
        """Create new set with symmetric difference of this set's own
        elements and the elements in another set.  A value 'x' is in
        the result if it was originally present in one or the other
        set, but not in both."""

        self._binary_sanity_check(other)
        result = Set(self)
        for elt in other:
            try:
                del result[elt]
            except LookupError:
                result[elt] = None
        return result

    #----------------------------------------
    def difference_update(self, other):
        """Remove all elements of another set from this set."""

        self._binary_sanity_check(other, "updating difference")
        for elt in other:
            self.discard(elt)
        return self

    #----------------------------------------
    def difference(self, other):
        """Create new set containing elements of this set that are not
        present in another set."""

        self._binary_sanity_check(other)
        result = Set(self)
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
    def add(self, item):
        """Add an item to a set.  This has no effect if the item is
        already present."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "adding an element"
        self[item] = None

    #----------------------------------------
    def update(self, iterable):
        """Add all values from an iteratable (such as a tuple, list,
        or file) to this set."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "adding an element"
        try:
            dictionary.update(self, iterable)
        except AttributeError:
            for item in iterable:
                self[item] = None

    #----------------------------------------
    def remove(self, item):
        """Remove an element from a set if it is present, or raise a
        LookupError if it is not."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        del self[item]

    #----------------------------------------
    def discard(self, item):
        """Remove an element from a set if it is present, or do
        nothing if it is not."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        try:
            del self[item]
        except KeyError:
            pass

    #----------------------------------------
    def pop(self):
        """Remove and return a randomly-chosen set element."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        return dictionary.popitem(self)[0]

    #----------------------------------------
    def is_subset_of(self, other):
        """Reports whether other set contains this set."""
        if not isinstance(other, Set):
            raise ValueError, "Subset tests only permitted between sets"
        for element in self:
            if element not in other:
                return 0
        return 1

    #----------------------------------------
    def _generic_cmp(self, other, method):
        """Compare one set with another using a dictionary method.
        Sets may only be compared with sets; ordering is determined
        by the keys in the underlying dictionary."""
        if not isinstance(other, Set):
            raise ValueError, "Sets can only be compared to sets"
        return method(self, other)

    #----------------------------------------
    def _binary_sanity_check(self, other, updating_op=''):
        """Check that the other argument to a binary operation is also a
        set, and that this set is still mutable (if appropriate),
        raising a ValueError if either condition is not met."""
        if updating_op and (self.hashcode is not None):
            raise ValueError, Set._Frozen_Msg % updating_op
        if not isinstance(other, Set):
            raise ValueError, "Binary operation only permitted between sets"

#----------------------------------------------------------------------
# Rudimentary self-tests
#----------------------------------------------------------------------

if __name__ == "__main__":

    # Empty set
    red = Set()
    assert `red` == "Set([])", "Empty set: %s" % `red`

    # Unit set
    green = Set((0,))
    assert `green` == "Set([0])", "Unit set: %s" % `green`

    # 3-element set
    blue = Set([0, 1, 2])
    assert `blue` == "Set([0, 1, 2])", "3-element set: %s" % `blue`

    # 2-element set with other values
    black = Set([0, 5])
    assert `black` == "Set([0, 5])", "2-element set: %s" % `black`

    # All elements from all sets
    white = Set([0, 1, 2, 5])
    assert `white` == "Set([0, 1, 2, 5])", "4-element set: %s" % `white`

    # Add element to empty set
    red.add(9)
    assert `red` == "Set([9])", "Add to empty set: %s" % `red`

    # Remove element from unit set
    red.remove(9)
    assert `red` == "Set([])", "Remove from unit set: %s" % `red`

    # Remove element from empty set
    try:
        red.remove(0)
        assert 0, "Remove element from empty set: %s" % `red`
    except LookupError:
        pass

    # Length
    assert len(red) == 0,   "Length of empty set"
    assert len(green) == 1, "Length of unit set"
    assert len(blue) == 3,  "Length of 3-element set"

    # Compare
    assert green == Set([0]), "Equality failed"
    assert green != Set([1]), "Inequality failed"

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
    assert green ^ blue == Set([1, 2]), "Non-empty symdiff"
    assert white ^ white == red,        "Self symdiff"

    # Difference
    assert red - green == red,           "Empty - non-empty"
    assert blue - red == blue,           "Non-empty - empty"
    assert white - black == Set([1, 2]), "Non-empty - non-empty"

    # In-place union
    orange = Set([])
    orange |= Set([1])
    assert orange == Set([1]), "In-place union"

    # In-place intersection
    orange = Set([1, 2])
    orange &= Set([2])
    assert orange == Set([2]), "In-place intersection"

    # In-place difference
    orange = Set([1, 2, 3])
    orange -= Set([2, 4])
    assert orange == Set([1, 3]), "In-place difference"

    # In-place symmetric difference
    orange = Set([1, 2, 3])
    orange ^= Set([3, 4])
    assert orange == Set([1, 2, 4]), "In-place symmetric difference"

    print "All tests passed"

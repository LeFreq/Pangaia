"""A class to represent sets in Python.
This class implements sets as dictionaries whose values are ignored
but preserved.  The usual operations (union, intersection, deletion,
etc.) are provided as both methods and operators.  The only unusual
feature of this class is that once a set's hash code has been
calculated (for example, once it has been used as a dictionary key,
or as an element in another set), that set 'freezes', and becomes
immutable.  See PEP-0218 for a full discussion.
"""

__version__ = "$Revision: 1.9 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2001/10/04 02:03:21 $"

from copy import deepcopy

class Set:

    # Displayed when operation forbidden because set has been frozen
    _Frozen_Msg = "Set is frozen: %s not permitted"

    #----------------------------------------
    def __init__(self, iterable=None):
        """Construct a set, optionally initializing it with elements
        drawn from an interable object.  The 'hashcode' element is
        given a non-None value the first time the set's hashcode is
        calculated; the set is frozen thereafter."""

        self.data = {}
        self.hashcode = None
        if iterable is not None:
            self.update(iterable)

    #----------------------------------------
    def __str__(self):
        """Return sorted set string in standard notation."""
        content = self.data.keys()
        content.sort()
        return '{' + ', '.join(map(str, content)) + '}'  #XXX map-str desirable?

    def __repr__(self):
        """Convert set to string."""
        return 'Set(' + `self.data.keys()` + ')'

    #----------------------------------------
    def __iter__(self):   #this method unnecessary??
        """Return iterator for enumerating set elements.  This is a
        keys iterator for the underlying dictionary."""
        return self.data.iterkeys()

    def __len__(self):
        """Return size of set."""
        return len(self.data)

    def __contains__(self, item):
        """Return non-zero if item is an element of set."""
        print "test"
        return item in self.data

    #----------------------------------------
    # Comparisons
    def __lt__(self, other):
        """Return true if self is proper subset of other."""
        if not isinstance(other, Set):
            return type(self) < type(other)
        return len(self) < len(other) and self._within(other)

    def __le__(self, other):
        """Return true if self is subset or equal to other."""
        if not isinstance(other, Set):
            return type(self) < type(other)
        return len(self) <= len(other) and self._within(other)

    def __eq__(self, other):
        return isinstance(other, Set) and len(self)==len(other) and self._within(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if not isinstance(other, Set):
            return type(self) > type(other)
        return len(self) > len(other) and other._within(self)

    def __ge__(self, other):
        if not isinstance(other, Set):
            return type(self) > type(other)
        return len(self) >= len(other) and other._within(self)

    is_subset_of        = __le__
    is_proper_subset_of = __lt__

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
        for elt in self.data:
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
        result = Set()
        result.data = self.data.copy()
        return result

    #----------------------------------------
    # Define 'copy' method as readable alias for '__copy__'.
    copy = __copy__

    #----------------------------------------
    def __deepcopy__(self, memo):
        result          = Set()
        memo[id(self)]  = result
        for elt in self.data:
            result.data[deepcopy(elt, memo)] = None
        return result

    #----------------------------------------
    def clear(self):
        """Remove all elements of unfrozen set."""
        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "clearing"
        self.data.clear()

    #----------------------------------------
    def union_update(self, other):
        """Update set with union of its own elements and the elements
        in another set."""

        self._binary_sanity_check(other, "updating union")
        self.data.update(other.data)
        return self

    #----------------------------------------
    def union(self, other):
        """Create new set whose elements are the union of this set's
        and another's."""

        self._binary_sanity_check(other)
        result = Set(self)
        result.data.update(other.data)
        return result

    #----------------------------------------
    def intersect_update(self, other):
        """Update set with intersection of its own elements and the
        elements in another set."""

        self._binary_sanity_check(other, "updating intersection")
        for elt in self.data.keys():  #make copy since modifying below
            if elt not in other.data:
                del self.data[elt]
        return self

    #----------------------------------------
    def intersect(self, other):
        """Create new set whose elements are the intersection of this
        set's and another's."""

        self._binary_sanity_check(other)
        if len(self.data) <= len(other.data):
            little, big = self.data, other.data
        else:
            little, big = other.data, self.data
        result = Set()
        for elt in little:
            if elt in big:
                result.data[elt] = None
        return result

    #----------------------------------------
    def sym_difference_update(self, other):
        """Update set with symmetric difference of its own elements
        and the elements in another set.  A value 'x' is in the result
        if it was originally present in one or the other set, but not
        in both."""

        self._binary_sanity_check(other, "updating symmetric difference")
        for elt in other.data:
            try:
                del self.data[elt]
            except LookupError:
                self.data[elt] = None
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
                del result.data[elt]
            except LookupError:
                result.data[elt] = None
        return result

    #----------------------------------------
    def difference_update(self, other):
        """Remove all elements of another set from this set."""

        self._binary_sanity_check(other, "updating difference")
        for elt in other.data:
            self.discard(elt)
        return self

    #----------------------------------------
    def difference(self, other):
        """Create new set containing elements of this set that are not
        present in another set."""

        self._binary_sanity_check(other)
        result = Set(self)
        for elt in other.data:
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
        self.data[item] = None

    #----------------------------------------
    def update(self, iterable):
        """Add all values from an iteratable (such as a tuple, list,
        or file) to this set."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "adding an element"
        if isinstance(iterable, Set):
            self.data.update(iterable.data)
        elif isinstance(iterable, type(self.data)):
            self.data.update(iterable)
        else:
            selfdict = self.data
            for item in iterable:
                selfdict[item] = None

    #----------------------------------------
    def remove(self, item):
        """Remove an element from a set if it is present, or raise a
        LookupError if it is not."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        del self.data[item]

    #----------------------------------------
    def discard(self, item):
        """Remove an element from a set if it is present, or do
        nothing if it is not."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        try:
            del self.data[item]
        except KeyError:
            pass

    #----------------------------------------
    def pop(self):
        """Remove and return a randomly-chosen set element."""

        if self.hashcode is not None:
            raise ValueError, Set._Frozen_Msg % "removing an element"
        return self.data.popitem()[0]

    #----------------------------------------
    def _within(self, other):
        """Return true if all elements of self are contained in other."""
        other = other.data
        for elt in self.data:
            if elt not in other:
                return 0
        return 1

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
    assert green == Set([0]),   "Equality failed"
    assert green != Set([1]),   "Inequality failed"
    assert green < Set([0, 1]), "Less-than failed"
    assert green <= Set([0]),   "Less-than-or-equal failed"
    assert green > Set([]),     "Greater-than failed"
    assert green >= Set([0]),   "Greater-than-or-equal failed"

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

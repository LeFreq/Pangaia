#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> February 5, 2001

"""Graph class."""

__version__ = "$Revision: 2.0 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/07/06 23:50:00 $"

#change a lot of these for loops to use faster map() function (see FAQ and QuickReference)
#remember reduce(lambda x,y: x+y, [1,2,3,4,5]) works for summing all elements...
#also: map/reduce/filter now work with any iterable object (including dictionaries!)
#add persistence
#implementation options:  { id: Vertex(id).{tail:Edge(tail)}}, {Vertex(id):kjSet(Edges)
#  {id: vertex(id)}{id:{Edge(proxy(Vertex(tail)))}; g.add(vertex, VertType=BaseVert), etc..
#having second thoughts about design:  maybe should use a SparseMatrix class (in Numeric module?) for holding
#  connection matrix:  0 for no connection 1 for unweighted graph, or the actual weight in case of weighted graph
#  a separate dictionary (or list/vector?)  for holding actual vertices and indices
#  a second vector would hold the action energy (for Network type)
#  but remember:  premature optimization...
#XXX Use of exceptions for control flow may prevent seeing actual errors.  Perhaps catch exception, plus error string and assert string is as expected
#XXX Use super() for calling base class methods
#perhaps Vertex._fastupdate() should be renamed __iadd__()
#consider sorting keys in __str__ methods.
#add setoperator mixin class to add set functions to a dict type

from __future__ import generators
from defdict import *

#EdgeBaseType = int
VertexBaseType = defdict
GraphBaseType = defdict
EDGEVALUE = 1

_DEBUG = 1
_PROFILE = 1

def OVERWRITE_DEFAULT(vertex, tail, edge_value): 
    if edge_value != EDGEVALUE: 
        vertex[tail] = edge_value

# {{{ Vertex
class Vertex(VertexBaseType):
    """Vertex holds the set of the vertices of its own outward directed edges.
    Edge values are user-settable and use overwrite semantics."""
    #Add id property to determine id, given Vertex

    __slots__ = ['_graph', '_id']  #Put all Vertex attributes here.  Uses base class' dictionary, instead of creating duplicate

    def __init__(self, graph, id, init={}, edge_value=EDGEVALUE):
        """Create a vertex object in graph.  Assumes id already in graph."""
        self._graph = graph  #graph to which this vertex belongs
        self._id = id
        super(Vertex, self).__init__(init, edge_value, OVERWRITE)
        if init and not isinstance(init, dict): graph.add(init) #ensure tails are in graph

    def setdefault(self, tail, edge_value=EDGEVALUE, collision=RETAIN):
        """Does defdict.setdefault with addition of adding tails to graph, if necessary.
        >>> g = Graph()
        >>> g.add(5)
        >>> g[5].setdefault(2)  #unless otherwise specified, will use default edge value
        1
        >>> print g             #note new vertex 2
        {2: {}, 5: {2: 1}}
        
        This method provided for completeness and to ensure preservation of Graph
        invariants.  Vertex.add() is recommended method.
        """
        if tail not in self._graph:
            self._graph.add(tail)
        return super(Vertex, self).setdefault(tail, edge_value, collision)
        
    def add(self, tail, edge_value=EDGEVALUE, collision=OVERWRITE_DEFAULT):
        """Add the tails to Vertex with optional edge value.  Add tails to graph if needed.
        >>> g = Graph()
        >>> g.add(5)        #add vertex with id=5 to graph
        >>> g[5].add(5)     #edges pointing back to self are allowed
        >>> g[5].add(7, 42) #add single out-edge from vertex 5 to 7 with weight 42
        >>> assert 7 in g   #vertex 7 automatically added to graph
        >>> g[5].add([3, 2, 4])   #add 4 out edges from 5, default weight 1
        >>> print g[5]      #show out-edges from vertex 5
        {2: 1, 3: 1, 4: 1, 5: 1, 7: 42}
        >>> g[5].add(7, 24) #edge values are over-written
        >>> g[5][7]
        24
        >>> g[5].add(7)     #if no edge value given, it is preserved
        >>> g[5][7]
        24
        """
        #XXX check if edge_value==use_default; if so, leave existing value as is
        try:  #single tail addition
            if tail in self:
                collision(self, tail, edge_value)
                return
            elif tail not in self._graph:
                self._graph.add(tail)
        except TypeError:  #multiple tail addition
            if not isinstance(tail, list): raise TypeError("argument must be hashable type or a list object.")
            self.update(tail, edge_value, collision)
        else:
            self[tail] = edge_value
            
    def update(self, tails, edge_value=EDGEVALUE, collision=OVERWRITE):
        """Like dict.update, but will also add tails to Graph.
        >>> g = Graph()
        >>> g.add(5)
        >>> g[5].update([1, 3, 5], 2)  #add the three tail vertices to vertex 5 with weight 2
        >>> print g[5]
        {1: 2, 3: 2, 5: 2}
        >>> assert 1 in g and 3 in g and 5 in g     #the vertices are now in the graph
        """
        super(Vertex, self).update(tails, edge_value, collision)
        for t in tails:  #could be dict or sequence type  #note use of super.update forces to loop again here
            self._graph.add(t)

    def discard(self, tail):
        """Removes tail(s) if present, otherwise does nothing.
        >>> g = Graph()
        >>> g.add(5, range(5))
        >>> print g[5]
        {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
        >>> g[5].discard(3)     #remove single edge
        >>> g[5].discard(90)    #discard of non-existent edge ignored
        >>> g[5].discard([0, 1, 90]) #discard multiple edges
        >>> print g[5]
        {2: 1, 4: 1}
        """
        try: #single tail removal
            del self[tail]
        except LookupError:  return     #ignore non-existent tails
        except TypeError: #must have been given a tail list
            if not isinstance(tail, list): raise TypeError("argument must be hashable type or a list object.")
            for t in tail:  #XXX inefficient if self is near empty
                try:
                    del self[t]
                except LookupError:
                    if not len(self): break  #good place to check if self is empty yet...

    def in_vertices(self):  #O(n)
        """Return iterator over the vertices that point to self."""
        for h in self._graph:
            if self._id in self._graph[h]:
                yield h

    out_vertices = VertexBaseType.iterkeys

    def in_degree(self):
        """Return number of edges pointing into vertex.
        >>> g = Graph()
        >>> g.add(1, [2, 3, 4])
        >>> g.add(2, [3, 2])
        >>> g[1].in_degree(), g[2].in_degree(), g[4].in_degree()
        (0, 2, 1)
        """
        i = 0
        for h in self.in_vertices():
            i += 1
        return i

    out_degree = VertexBaseType.__len__

    def __eq__(self, other):
        """Return non-zero if all edges in self are present in other with same weight."""
        return (type(self) == type(other) and
                self._id == other._id and
                super(Vertex, self).__eq__(other)) 
                #XXX and self.in_vertices()==other.in_vertices())

    def __str__(self):
        """Return string of tail vertices in set notation."""
        if _DEBUG: self.validate()
        return super(Vertex, self).__str__()
#        return "{%r| %s}" % (self._id, `self.keys()`[1:-1])

    def copy(self):
        """Make a copy of the vertex tail set.
        >>> g = Graph()
        >>> g.add(5, 1)
        >>> v = g[5].copy()
        >>> type(v), v 
        (<class 'graphdef.Vertex'>, {1: 1})
        """
        return self.__class__(self._graph, self._id, self)
        #XXX shallow copy assumes EDGEVALUE is simple type!

    def validate(self):
        """Assert Vertex invariants."""
        assert isinstance(self._graph, Graph)
        hash(self._id) #id should be hashable
        assert self._id in self._graph
        for t in self:
            assert t in self._graph, "Non-existant tail %s in vertex %s" % (t, self._id)
# }}} Vertex
# {{{ VMixin
class VMixin:
    """VMixin expands on Vertex class by allowing user to set a policy function
    to be called with a tail is added to the vertex that already exists.
    Users can derive from this class and override collide() to
    set different policies."""

    def sum_in(self):
        """Return sum of all edges that point to vertex."""
        g, t = self._graph, self._id
        sum = 0
        #return reduce(lambda h1, h2: g[h1][t]+g[h2][t], self.in_vertices())  #XXX doesn't work, why?
        for h in self.in_vertices():
            sum += g[h][t]
        return sum

    def sum_out(self):
        """Return sum of all edges that leave from vertex."""
        return reduce(lambda t1, t2: t1+t2, self.itervalues())  #use operator.add instead of lambda?

    def validate(self):
        """Assert Vertex invariants."""
        super(Vertex, self).validate()
        for t in self:
            assert type(self[t]) is type(EDGEVALUE), "Bad value on tail %s in vertex %s" % (t, self._id)

# }}} VMixin

def MERGE_VERTEX(g, h, vert): g[h].update(vert)

# {{{ Graph class
class Graph(GraphBaseType):
    """Basic class implementing a directed Graph.  Vertices without edges are allowed.
    Self-referencing vertices are allowed."""
    #Basic data structure {vertex id: {t1: edge; t2: edge}}
    #Add label to __init__ to attach description to graph?
    #Disable __setitem__()?

    __slots__ = ['VertexType']

    def __init__(self, initgraph=None, VertexType=Vertex):
        """Create the graph, optionally initializing from another graph.
        Optional VertexType parameter can be passed to specify default vertex type.
        >>> g=Graph()
        >>> len(g), g
        (0, {})
        >>> g.add([1, 2, 3], [2, 3])
        >>> g2 = Graph(g)       #can initialize with other Graph type
        >>> print g2
        {1: {2: 1, 3: 1}, 2: {2: 1, 3: 1}, 3: {2: 1, 3: 1}}
        """
        if isinstance(initgraph, Graph):
            super(Graph, self).__init__(initgraph) #XXX shared Vertex objects
            self.VertexType = initgraph.VertexType
        elif initgraph:
            raise TypeError, "can only initailize with Graph object"
        else:
            super(Graph, self).__init__()
            self.VertexType = VertexType

    def add(self, head, tail=[], edge_value=EDGEVALUE, collision=MERGE_VERTEX):
        """Add the vertices and/or edges.
        Parameters can be single vertex or list of vertices.
        If no second parameter given, assume vertex addition only.
        >>> g=Graph()
        >>> g.add(1)            #single vertex addition
        >>> g.add(1)            #adding existing vertex is ignored
        >>> g.add([2, 3, 4])    #multiple vertex addition
        >>> g.add([2])          #list containing only one vertex is allowed
        >>> print g
        {1: {}, 2: {}, 3: {}, 4: {}}
        
        If second parameter given, then edge addition is performed.
        Vertices are added as necessary.  An optional edge value
        is accepted as a third parameter.
        
        >>> g.add(2, 1)         #edge from vertex 2 to vertex 1
        >>> g.add(1, 5, 100)    #edge from 1 to new vertex 5 with weight 100
        >>> g.add(1, 5, 90)     #adding existing edge, edge value overwritten
        >>> g.add(3, 3)         #loops are allowed
        >>> print g
        {1: {5: 90}, 2: {1: 1}, 3: {3: 1}, 4: {}, 5: {}}
        
        Vertex lists allowed on either parameter for multiple edge addition.

        >>> g.clear()                 #remove all vertices (and edges)        
        >>> g.add(1, [0, 2])          #add edges (1, 0) and (1, 2)
        >>> g.add(1, [1])
        >>> print g
        {0: {}, 1: {0: 1, 1: 1, 2: 1}, 2: {}}
        >>> g.add(range(3), range(3)) #fully-connected 3-vertex graph
        >>> print g
        {0: {0: 1, 1: 1, 2: 1}, 1: {0: 1, 1: 1, 2: 1}, 2: {0: 1, 1: 1, 2: 1}}
        """
        #XXX if no edge_value given, then value should not be overwritten
        if not isinstance(tail, list): tail = [tail]
        try:  #single head addition
            if head not in self:    #check to avoid infinite loop
                self[head] = self.VertexType(self, head, tail, edge_value)
            elif tail:
                self[head].update(tail, edge_value)
        except TypeError:  #multiple head addition
            if not isinstance(head, list): raise "head must be hashable object or list type"
            for h in head:  #XXX will add same tails multiple times
                self.add(h, tail, edge_value)
        if _DEBUG: self.validate()

    def discard(self, head, tail=[]):
        """Remove vertices and/or edges.
        Parameters can be single vertex or list of vertices.
        If tail is non-empty, then only edge deletions are made.
        If tail is empty, then vertex deletions are made and any associated edges.
        """
        if tail==[]:    #vertex deletions
            try:
                del self[head]
            except LookupError: pass   #do nothing if given non-existent vertex
            except TypeError:          #given head list
                if not isinstance(head, list): raise TypeError("argument must be hashable type or a list object.")
                for h in head:
                    if h in self:
                        self[h].clear()
                        GraphBaseType.__delitem__(self, h) #don't duplicate effort (will discard in_vertices below)
                    else: head.remove(h) #for faster tail removal in next loop
                for h in self:   #visit remaining vertices and remove occurances of head items in edge lists
                    self[h].discard(head)
        else:   #edge deletions only
            if not isinstance(head, list): head = [head] #quick and dirty to avoid extra code
            for h in head:
                if h in self:
                    self[h].discard(tail)
        if _DEBUG: self.validate()

    #alternate syntax for various items
    out_vertices = GraphBaseType.__getitem__  #XXX returns dict, unlike in_vertices() which returns iterator
    vertices = GraphBaseType.iterkeys
    order = GraphBaseType.__len__
    #__setitem__ #for some reason is called for self[v] -= [tails] so can't remove from interface

    def popitem(self):
        """Remove and return one arbitrary vertex-edge tuple.  Preserve graph invariants."""
        for v, tails in self.iteritems(): break  #XXX any better way?
        tails = tails.copy()  #must make copy since we have the actual object which is about to be deleted.
        del self[v]  #removes any edges as necessary
        return (v, tails)

    def update(self, other, default=None, collision=OVERWRITE):
        """Merges one graph with another.  Takes union of edge lists."""
        assert isinstance(other, Graph), "Can only merge Graph types."
        for h in other:
            if h in self:  #do union of edge sets
                self[h].update(other[h], collision=collision)
            else:   #otherwise just copy the set
                self[h] = other[h].copy() #XXX copy or deepcopy?

    def __delitem__(self, head):
        """Delete a single vertex and associated edges.
        Raises LookupError if given non-existant vertex."""
        self[head].clear() #removes out vertices
        for v in self[head].in_vertices():
            del self[v][head]
        super(Graph. self).__delitem__(head)

    def __str__(self):
        if _DEBUG: self.validate()
        return super(Graph, self).__str__()
        #return '{' + ', '.join(map(str, self.itervalues())) + '}'

    #__repr__ = __str__

    def validate(self):
        """Check graph invariants."""
        #NOTE:  calling this after each insert/remove slows things down considerably!
        for v in self.vertices():
            assert isinstance(self[v], self.VertexType), "vertex type not found on " + str(v)
            self[v].validate()

# }}} Graph

def test(g, size=100):
    import time
    if _PROFILE:
        print "Profiling (ignoring debug)..."
        _DEBUG = 0
        for i in [1,2]:
            start=time.clock()
            g.add(range(1000),range(100,1100))
            finish=time.clock()
            print "Add 1000, 100-1100; pass %i: %5.2fs" %  (i, (finish-start))
        for i in [1,2]:
            start=time.clock()
            g.discard(range(1050), range(100))#, range(1000))
            finish=time.clock()
            print "Discard 1050, 100; pass %i:  %5.2fs" % (i, (finish-start))
        g.clear()
        g.add(0)
        for i in [1,2]:
            start=time.clock()
            g[0].update(range(1000))
            finish=time.clock()
            print "Update 1000, 1000; pass %i:  %5.2fs" % (i, (finish-start))
        g.clear()

def _test():
    import doctest, graphdef
    return doctest.testmod(graphdef)

if __name__ == '__main__':
#    g=Graph(VertexType=Vertex)
#    test(g, 100)
    _test()
#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> February 5, 2001

"""Graph class."""

__version__ = "$Revision: 1.11 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2001/11/04 04:56:08 $"

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

from __future__ import generators

EdgeBaseType = int
VertexBaseType = dictionary
GraphBaseType = dictionary
EDGEVALUE = 1

_DEBUG = 1
_PROFILE = 1

#XXX look at graphnew.py and graphpreprenew.py for unincorporated updates
#XXX perhaps weight parameter should be set to None then edge_value is only changed when non-None

# {{{ BaseVertex
class BaseVertex(VertexBaseType):
    """BaseVertex holds the set of the vertices of its own outward directed edges.
    Edge values are user-settable and use overwrite semantics."""

    __slots__ = ['_graph', '_id']  #Put all Vertex attributes here.  Uses base class' dictionary, instead of creating duplicate

    def __init__(self, graph, id):
        """Create a vertex object in graph, populated with optional tail(s)."""
        VertexBaseType.__init__(self)
        self._graph = graph  #graph to which this vertex belongs
        self._id = id

    def add(self, tail, edge_value=EDGEVALUE):
        """Add the tails to vertex with optional edge value.  Add tails to graph if neeed."""
        try:  #single tail addition
            if tail not in self._graph:  #"in" raises TypeError if non-hashable
                self._graph.add(tail)    #add tail vertices to graph if necessary
        except TypeError:  #multiple tail addition
            self.update(tail, edge_value)
        else:
            self[tail] = edge_value

    def discard(self, tail):
        """Removes tail(s) if present, otherwise does nothing."""
        try: #single tail removal
            del self[tail]
        except LookupError:  return
        except TypeError: #must have been given a tail list
            if not isinstance(tail, list): raise TypeError("argument must be hashable type or a list object.")
            self -= tail

    def update(self, tails, edge_value=EDGEVALUE):
        """Add list of tails from iterable object to vertex with optional edge value.
        Adds tails to graph if needed."""
        for t in tails:
            if t not in self._graph:
                self._graph.add(t)    #add tail vertices to graph if necessary
            self[t] = edge_value #appears to be just as fast or faster then checking for existence first (plus keeps standard dict semantics)

    def in_vertices(self):
        """Return iterator over the vertices where self is the tail vertex."""
        return self._graph.in_vertices(self._id)

    out_vertices = VertexBaseType.iterkeys
    out_degree = VertexBaseType.__len__

    def _fastupdate(self, tails, edge_value=EDGEVALUE):
        """Add list of tails without checking for existence in graph."""
        try: #simple tail
            self[tails] = edge_value #XXX v2.2b1 seems to allow subclassed dictionarys to be hashable
        except TypeError:  #must be unhashable: list or dict
            try:  #check if given dictionary with tails, then do super-fast addition of tails
                #XXX Note: if BaseVertex values are non-simple objects, then update will copy same objects to other vertices.
                dictionary.update(self, tails)
            except AttributeError:
                for t in tails:
                    self[t] = edge_value

    def __isub__(self, other):
        """Remove the given tail vertices.  Other can be any iterable object."""
        for tail in other:  #XXX inefficient if self is near empty
            try:
                del self[tail]
            except LookupError:
                if not len(self): break  #good place to check if self is empty yet...
        return self

    def __str__(self):
        """Return string of tail vertices in set notation."""
        if _DEBUG: self.validate()
        return "{%s| %s}" % (self._id, `self.keys()`[1:-1])

    def __copy__(self):
        """Make a copy of the vertex tail set."""
        result = self.__class__(self._graph, self._id)
        dictionary.update(result, self) #XXX shallow copy assumes EDGEVALUE is simple type!
        return result

    copy = __copy__

    def __hash__(self): #XXX shouldn't be needed but in 2.2b1 subclassed dicts appear to be hashable!
        raise TypeError("unhashable type")

    def validate(self):
        """Assert Vertex invariants."""
        assert isinstance(self._graph, BaseGraph)
        hash(self._id) #id should be hashable
        for t in self:
            assert t in self._graph, "Non-existant tail %s in vertex %s" % (t, self._id)
            assert type(self[t]) is type(EDGEVALUE), "Bad value on tail %s in vertex %s" % (t, self._id)
# }}} BaseVertex
# {{{ Vertex
class Vertex(BaseVertex):
    """Vertex expands on BaseVertex class by allowing user to set a policy function
    to be called with a tail is added to the vertex that already exists.
    Users can derive from this class and override collide_edge() to
    set different policies."""

    def collide_edge(self, tail, other_value):
        """This functions determines the policy for tail additions
        when tail is already in vertex."""
        self[tail] += other_value

    def add(self, tail, edge_value=EDGEVALUE):
        """Add the tails to Vertex with optional edge value.  Add tails to graph if neeed."""
        try:  #single tail addition
            if tail in self:  #"in" raises TypeError if tail non-hashable
                self.collide_edge(tail, edge_value)
            else:
                self._graph.add(tail)    #add tail vertices to graph if necessary
                self[tail] = edge_value
        except TypeError:  #multiple tail addition
            self.update(tail, edge_value)

    def update(self, tails, edge_value=EDGEVALUE):
        """Add list of tails from iterable object to Vertex with optional edge value.
        Adds tails to graph if needed."""
        for t in tails:
            if t in self:
                self.collide_edge(t, edge_value)
            else:
                self._graph.add(t)    #add tail vertices to graph if necessary
                self[t] = edge_value #appears to be just as fast or faster then checking for existence first (plus keeps standard dict semantics)

    def _fastupdate(self, tails, edge_value=EDGEVALUE):
        """Add list of tails without checking for existence in graph."""
        try: #simple tail
            if tails in self:
                self.collide_edge(tails, edge_value)
            else:
                self[tails] = edge_value #XXX v2.2b1 seems to allow subclassed dictionarys to be hashable
        except TypeError:  #must be unhashable: list or dict
            collide = self.collide_edge
            for t in tails:
                if t in self:
                    collide(t, edge_value)
                else:
                    self[t] = edge_value

# }}} Vertex

# {{{ BaseGraph class
class BaseGraph(GraphBaseType):
    """Basic class implementing a directed Graph.  Vertices without edges are allowed.
    Self-referencing vertices are allowed."""
    #Basic data structure {vertex id: {t1: edge; t2: edge}

    __slots__ = ['VertexType']

    def __init__(self, initgraph=None, VertexType=BaseVertex):
        """Create the graph, optionally initializing from another graph.
        Optional VertexType parameter can be passed to specify default vertex type."""
        GraphBaseType.__init__(self)
        self.VertexType = VertexType
        if initgraph is not None:
            assert isinstance(initgraph, BaseGraph)
            initgraph.validate()
            dictionary.update(self, initgraph)  #XXX this will create shared Vertex objects!

    def add(self, head, tail=[], edge_value=EDGEVALUE):
        """Add the vertices and/or edges.
        Parameters can be single vertex or list of vertices.
        If only one parameter is given, then only vertex additions are made.
        If both parameter are given, then edge additions are made setting optional edge value.
        Vertices are added as necessary.
        """

        try:  #simplest possibility first:  single head addition
            if head not in self:
                self[head] = self.VertexType(self, head)
        except TypeError:  #multiple head addition
            if not isinstance(head, list): raise TypeError("argument must be hashable type or a list object.")
            tmp = self.VertexType(self, "__dummy")
            tmp.add(tail, edge_value)  #will also add tail vertices
            for h in head:
                if h not in self:
                    self[h] = self.VertexType(self, h)
                self[h]._fastupdate(tmp) #tail values already in temp, edge_value)
        else: #single head addition succeeded, now add tail(s)
            if tail != []:
                self[head].add(tail, edge_value)  #will also add tail vertices
        if _DEBUG: self.validate()

    def count(self, head, tail=[]):
        return len(self.select(head, tail))

    def select(self, head, tail=[]):
        """Return list of vertices or edge tuples that satisfy constraints given.
        Parameters can be either single vertex names or list of vertices.
        select(All) returns all vertices in graph.
        select(All, All) returns all edges in graph.
        select(h, ALL) returns all edges where h is the head vertex.
        select(ALL, t) return all edges where t is the tail vertex.
        select(v) returns intersection of v and graph.
        select(h,t) returns intersection of (h,t) and all graph edges.
        """
        #XXX if self.vertices() is passed as both parameters, it appears that each affect the other...
        #XXX returns duplicates if parameters contain duplicates
        if not isinstance(head, list) and type(head)!=type(self.iterkeys()): head = [head] #XXX isinstance(head, generator) not work in v2.2a4
        if tail==[]:
            return [h for h in head if h in self]
        else:
            if not isinstance(tail, list) and type(tail)!=type(self.iterkeys()): tail = [tail] #XXX
            return [(h, t) for h in head if h in self for t in tail if t in self[h]]

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
    out_vertices = GraphBaseType.__getitem__  #XXX returns dictionary, unlike in_vertices() which returns iterator
    vertices = GraphBaseType.iterkeys
    order = GraphBaseType.__len__
    #__setitem__ #for some reason is called for self[v] -= [tails] so can't remove from interface
    setdefault = None  #XXX this defines an attribute, not re-defines method

    def in_vertices(self, vertex):  #O(n)
        """Return iterator over the vertices where vertex is tail."""
        if vertex not in self:
            raise LookupError(vertex)
        for h in self:
            if vertex in self[h]:
                yield h

    def popitem(self):
        """Remove and return one arbitrary vertex-edge tuple.  Preserve graph invariants."""
        for v, tails in self.iteritems(): break  #XXX any better way?
        tails = tails.copy()  #must make copy since we have the actual object which is about to be deleted.
        del self[v]  #removes any edges as necessary
        return (v, tails)

    def update(self, other):
        """Merges one graph with another.  Takes union of edge lists."""
        assert isinstance(other, BaseGraph), "Can only merge Graph types."
        for h in other:
            if h in self:  #do union of edge sets
                self[h].update(other[h])  #XXX update doesn't currently preserve values
            else:   #otherwise just copy the set
                self[h] = other[h].copy() #XXX copy or deepcopy?

    def __delitem__(self, head):
        """Delete a single vertex and associated edges.
        Raises LookupError if given non-existant vertex."""
        self[head].clear() #removes out vertices
        for v in self.in_vertices(head):
            del self[v][head]
        GraphBaseType.__delitem__(self, head)

    def __str__(self):
        self.validate()
        return '{' + ', '.join(map(str, self.itervalues())) + '}'

    #__repr__ = __str__

    def validate(self):
        """Check graph invariants."""
        #NOTE:  calling this after each insert/remove slows things down considerably!
        for v in self.vertices():
            assert isinstance(self[v], self.VertexType), "vertex type not found on " + str(v)
            self[v].validate()

# }}} BaseGraph

def test(g, size=100):
    import time
#    from graphsupport2 import *
    #FIXME:  should exercise every function in graph...
    #FIXME:  should try removing non-existent things too
    #FIXME:  should try excercise graph.update()
    g.add(0)
    g.add(0,0)
    g.add(1)
    print g.select(g.keys(), g.keys())
    g.add(1)
    g.add(1,0)
    g.add(1,0)
    g.discard(1,0)
    print g
    print "Creating graph of size",size,"..."
    g.add(range(size),range(size))
    g.add(range(size+20,size+40,2))
    g.add(size+1, [1,2,3])
    g.add([3,4,5], size+1)
    print g.select(size+1, g.vertices())
    print g.select(g.vertices(), size+1)
    print len(g)
    print len(g[size+1])
    g.discard(range(50))
    g.discard(1,2)
    g.discard(g.vertices(),3)
    g.validate()
    print "Erasing graph..."
    g.clear()
#    generate(g, "random",30)
#    generate(g, "random",30)
    print g
    if _PROFILE:
        print "Profiling (ignoring debug)..."
        global _DEBUG
        previous = _DEBUG
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
        _DEBUG = previous
        g.clear()

if __name__ == '__main__':
    g=BaseGraph(VertexType=Vertex)
    test(g, 100)

#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> February 5, 2001

"""Graph class."""

#change a lot of these for loops to use faster map() function (see FAQ and QuickReference)
#remember reduce(lambda x,y: x+y, [1,2,3,4,5]) works for summing all elements...
#add persistence
#implementation options:  { id: Vertex(id).{tail:Edge(tail)}}, {Vertex(id):kjSet(Edges)
#  {id: vertex(id)}{id:{Edge(proxy(Vertex(tail)))}; g.add(vertex, VertType=BaseVert), etc..
#having second thoughts about design:  maybe should use a SparseMatrix class (in Numeric module?) for holding
#  connection matrix:  0 for no connection 1 for unweighted graph, or the actual weight in case of weighted graph
#  a separate dictionary (or list/vector?)  for holding actual vertices and indices
#  a second vector would hold the action energy (for Network type)
#  but remember:  premature optimization...
#Replace uses of setdefault with DictSet.update, see DictSet notes for further ideas (update() can be pass function parameter (lambda s, o: s|o)

from __future__ import nested_scopes

import dictset

SetType = dictset.DictSet
BaseType = dictset.DictSet
_DEBUG = 1

# {{{ Graph class
class BaseGraph(BaseType):
    """Basic class implementing a directed Graph.  Vertices without edges are allowed.  Self-referencing vertices are allowed."""
    #Basic data structure {vertex: SetType(tail vertices)}

    def __init__(self, initgraph=None):
        if initgraph is not None:
            assert isinstance(initgraph, BaseGraph)
            initgraph.validate()
            BaseType.__init__(self, initgraph)
        else:
            BaseType.__init__(self)

    def add(self, head, tail=[]):
        try:    #most common operation first:  single vertex addition  ##FIXME: results in code duplication--is this really
            self.setdefault(head)   #will raise exception if given a list (or other unhashable type!)
            try:    #head added, now check to see if tail given, next most common operation second: single edge addition
                self.setdefault(tail)
                self[head].add(tail)      #will add actual object reference as tail
            except TypeError:   #must of been given a tail list (or no tail specified)
                if not isinstance(tail, list): raise "Second argument must be hashable type or a list object."
                map(self.setdefault, tail)  #add all tail vertices first
                self[head].update(tail)
        except TypeError:   #must of been given a head list
            if not isinstance(head, list): raise "First argument must be hashable type or a list object."
            if not isinstance(tail, list):  tail = [tail]
            map(self.setdefault, head+tail) #add all vertices first #FIXME: would intersection of head+tail help much?, also: setdefault mightl raise TypeError
            if tail!=[]:    #perhaps unuseful test, may speedup things in default case though (tail=[])
                for h in head:  #append tail list to each head
                    self[h].update(tail)
        if _DEBUG: self.validate()

    def count(self, head, tail=[]):
        return len(self.select(head, tail))

    def select(self, head, tail=[]):
        """
        select(All) returns g.vertices
        select(All, All) returns g.edges
        select(h, ALL) returns g[h].out_edges
        select(ALL, t) return g[t].in_edges
        select(v) returns v in g
        select(h,t) returns (h,t) if in g"""
        if not isinstance(head, list): head = [head]
        if tail==[]:
            return [h for h in head if h in self]
        else:
            if not isinstance(tail, list): tail = [tail]
            return [(h, t) for h in head if h in self for t in tail if t in self[h]]

    def discard(self, head, tail=[]):
        """Remove the vertex and all associated edges."""   ##FIXME
        if tail==[]:    #vertex deletions
            try:
                del self[head]
            except TypeError:   #given head list
                if not isinstance(head, list): raise "First argument must be hashable type or a list object."
                for h in head:
                    if h in self:
                        self[h].clear()
                        #for v in self.in_vertices(h):  #if v not in head: self[v].discard(h)?  #ignore edge lists on vertices about to be discarded
                        #   self[v].discard(h)          #this is really slow O(N^2); maybe at end iterate through remaining vertices and discard everything in head list
                        BaseType.__delitem__(self, h) #don't duplicate effort
                    #else head -= h #for faster tail removal in next loop
                headset = SetType(head)
                for h in self:   #visit remaining vertices and remove occurances of head items in edge lists
                    self[h] -= headset     #set subtraction
            except LookupError: pass   #do nothing if given non-existent vertex
        else:   #edge deletions
            if not isinstance(head, list): head = [head]
            if not isinstance(tail, list): tail = [tail]
            for h in head:
                if h in self:
                    head_discard = self[h].discard  #for efficiency's sake
                    for t in tail:  #tail[:]?
                        head_discard(t)
        if _DEBUG: self.validate()

    out_vertices = BaseType.__getitem__

    def in_vertices(self, vertex):
        if vertex not in self:
            raise LookupError, vertex
        return [h for h in self if vertex in self[h]]

    def setdefault(self, vertex, failobj=None): #don't put SetType() here as default parameter since then only evaluated once-->all vertices get same Set!
        if vertex not in self:
            self[vertex] = SetType(failobj)
        return self[vertex]

    def popitem(self):
        vertex, edges = BaseType.popitem(self)
        del self[vertex]
        return

    def clear(self):
        for h in self.keys():    #make copy of keys since modifying below
            self[h].clear()
            del self[h]

    def update(self, other):  #XXX what will happen to Set's use of update?
        """Merges one graph with another.  Takes union of edge lists."""
        assert isinstance(other, BaseGraph), "Can only merge Graph types."
        for h in other:
            if h in self:  #do union of edge sets
                self[h] |= other[h]
            else:   #otherwise just copy the set
                self[h] = other[h].copy()

    #alternate syntax for various items
    vertices = BaseType.keys
    order = BaseType.__len__

    #def __setitem__(self): pass #not allowed
    def __delitem__(self, head):
        """Delete a single vertex and associated edges.
        Raises LookupError if given non-existant vertex."""
        self[head].clear()
        for v in self.in_vertices(head):
            self[v].discard(head)
        BaseType.__delitem__(self, head)

    def __str__(self):
        self.validate()
        s = "{"
        s += ", ".join(map(lambda head: "%s: %s" % (head, self[head]), self))
        return s + "}"

    __repr__ = __str__

    def validate(self):
        """Check graph invariants."""
        #NOTE:  calling this after each insert/remove slows things down considerably!
        for v in self.vertices():
            assert isinstance(self[v], SetType), "Set type not found for edge list on " + str(v)
            assert len(self[v]) <= len(self), "Edge list larger that vertex list on " + str(v)  #this important since select function below will only return valid edges
            for t in self[v]:
                assert t in self, "Non-existant tail %s in vertex %s" % (t, v)
        for e in self.select(self.keys(),self.keys()):
            assert e[0] in self, "Edge %s pointing to non-existent vertex: " % (e, e[0])
            assert e[1] in self, "Edge %s pointing to non-existent vertex: " % (e, e[1])

# }}} Graph

def test(g, size=100):
#    from graphsupport2 import *
    #FIXME:  should exercise every function in graph...
    #FIXME:  should try removing non-existent things too
    #FIXME:  should try excercise graph.update()
    g.add(0)
    g.add(0,0)
    g.add(1)
    print g.select(g.vertices(), g.vertices())
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

if __name__ == '__main__':
    g=BaseGraph()
    test(g, 100)

#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 7, 2002

"""Network class for flow networks."""

__version__ = "$Revision: 2.8 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/08/12 22:52:23 $"

#Add Network.time to track how many ticks

from __future__ import generators

import random, operator
from graph import *
from bag import *

DEFAULT_CAPACITY = 1

class Node(bag, VMixin):
    """Node in a flow network."""
    
    __slots__ = ['flow', 'last_tick', '_graph', '_id']
    
    def __init__(self, network, id, init={}):
        super(Node, self).__init__(init)
        self._graph = network
        self._id = id
        self.flow = imbag()
        if init: network.add(list(init))    #XXX may add sinks to network multiple times

    def add(self, sink, capacity=DEFAULT_CAPACITY):
        """Add connection to sink with given capacity (defaults to 1).
        >>> n = Network()
        >>> n[1].add([2, 3], 5)
        >>> print n[1]
        0 {2: 5, 3: 5}

        If sink already connected, capacity is accumulates.
        >>> n[1].add(2, 2)
        >>> n[1].add(2)     #will use default cap=1
        >>> print n[1]
        0 {2: 8, 3: 5}
        """
        try:
            self[sink] += capacity
        except TypeError:
            if not isinstance(sink, list): raise TypeError("argument must be hashable type or a list object.")
            self += (sink*capacity)     #XXX slow if capacity large
    
    def update(self, sinks, add_sinks=1):
        """Update arcs leaving node.  If arc already exists, capacity is
        add to existing value; if not, it is created with default capacity.
        >>> n = Network()
        >>> n[1] += [1, 1, 2, 3, 1]
        >>> print n[1]
        0 {1: 3, 2: 1, 3: 1}
        >>> n[1].update({2: 3, 4: 2})
        >>> print n[1]
        0 {1: 3, 2: 4, 3: 1, 4: 2}
        >>> n[1] += ([5, 1] * 3)
        >>> print n[1]
        0 {1: 6, 2: 4, 3: 1, 4: 2, 5: 3}
        >>> assert 1 in n and 2 in n and 3 in n and 4 in n and 5 in n
        """
        super(Node, self).update(sinks)
        if add_sinks:
            g = self._graph
            for s in sinks:
                if s not in g:
                    g.add(s)
                    
    def __iadd__(self, sinks, add_sinks=1):
        """Add list of sinks to node, adding sinks to graph as necessary."""
        if add_sinks:
            g = self._graph
            for s in sinks:
                if s not in g:
                    g.add(s)
        return super(Node, self).__iadd__(sinks)

    def in_vertices(self):  #O(n)
        """Return iterator over the nodes that point to self.
        >>> n = Network()
        >>> n.add(1, [2, 3, 4])
        >>> n.add(2, [3, 2])
        >>> list(n[2].in_vertices())       #XXX arbitrary order
        [1, 2]
        """
        for head in self._graph.itervalues():
            if self._id in head:
                yield head._id

    out_vertices = bag.iterkeys
    
    def in_degree(self):
        """Return number of edges pointing into vertex.
        >>> n = Network()
        >>> n.add(1, [2, 3, 4])
        >>> n.add(2, [3, 2])
        >>> n[1].in_degree(), n[2].in_degree(), n[4].in_degree()
        (0, 2, 1)
        """
        return len(list(self.in_vertices()))
    
    out_degree = dict.__len__

    def __setitem__(self, sink, capacity):
        """Set arc capacity.  If sink does not exist and capacity>0, 
        sink is created and added to network.
        >>> n = Network()
        >>> n[1][3]
        0
        >>> n[1][2] = 3
        >>> print n
        {1: 0 {2: 3}, 2: 0 {}}
        """
        super(Node, self).__setitem__(sink, capacity)
        if sink not in self._graph:
            self._graph.add(sink)
        
    def _push(self, bits, tick):
        """Advance node 1 time increment. Returns amount of energy remaining.
        Should not be run except through Network().
        >>> n = Network()
        >>> n[1][2] = 2
        >>> n.energy[1] = 3
        >>> n[1]._push(n.energy[1], n.ticks)
        1
        
        Negative energy values make energy flow in reverse direction.
        >>> n = Network()
        >>> n[1][2] = 2
        >>> n.energy[2] = -3
        >>> n()
        >>> print n
        {1: -2 {2: 2}, 2: -1 {}}
        """
        assert bits #should not get called with 0 bits
        paths = self.paths(bits)
        self.last_tick = tick   #XXX would like to set last_tick and clear flow only if paths!=[]
        self.flow.clear()       #clear old flow values
        if paths:                   #if no paths, then no bits to move
            if bits>=len(paths):    #all paths saturated
                self.flow += paths
                bits -= len(paths)
            else:                   #pick which paths to send bits
                bit = (bits>=0 and 1 or -1)
                while bits and paths:
                    path = paths.pop(int(random.random()*len(paths))) 
                    self.flow[path] += bit
                    bits -= bit
        return bits   #return remaining bits for next round

    def paths(self, bits):
        if bits >= 0:
            return reduce(operator.add, [[tail]*capacity for tail, capacity in self.iteritems()], [])
        else:
            g = self._graph     #this optimization needed in a list comprehension?
            return reduce(operator.add, [[head]*g[head][self._id] for head in self.in_vertices()], [])

    def _energy_out(self):
        return len(self.flow)
        
    def _energy_read(self):
        return self._graph.energy[self._id]
        
    def _energy_write(self, value):
        self._graph.energy[self._id] = value
        
    energy_out = property(_energy_out, None, None, "Energy out of node.")
    energy = property(_energy_read, _energy_write, None, "Energy at node. Slow -- use network.energy[id]")

    def clear(self):
        super(Node, self).clear()
        self.flow.clear()

    def __str__(self):
        """Returns string with energy level and arc info.
        >>> n = Network()
        >>> n.add(1, 2)
        >>> n[1].energy += 5
        >>> print n[1]
        5 {2: 1}
        """
        return "%r %r" % (self.energy, self)

    def validate(self):
        """Assert Node invariants."""
        hash(self._id) #id should be hashable
        assert isinstance(self._graph, Network)
        assert self._id in self._graph
        for node, cap in self.iteritems():
            assert node in self._graph, "Non-existant tail %r in node %r" % (node, self._id)
            assert cap > 0, "Invalid capacity at node %r: %r" % (node, cap)


def MERGE_NODE(net, node, sinks): 
    net[node].update(sinks)
    try: net[node].energy += sinks.energy
    except AttributeError: pass

class Network(Graph):
    """Flow network class."""

    __slots__ = ['energy', 'io', 'ticks']

    def __init__(self, init={}, VertexType=Node):
        if not isinstance(VertexType, type(Node)): raise TypeError, "Invalid vertex type"
        super(Network, self).__init__(init, VertexType)
        if isinstance(init, Network): self.energy = imbag(init.energy)
        else: self.energy = imbag()   #stores energy values at each node
        self.io = imbag()       #energy entering and leaving the network
        self.ticks = 0          #number of network clock ticks since creation

    def add(self, source, sink=[], capacity=DEFAULT_CAPACITY):
        """Like Graph.add, but will accumulate edge values, instead of
        overwriting them.  See Graph.add.__doc__.
        >>> n = Network()
        >>> n.add(1, [2, 3], 2)
        >>> n.add(1, 2)
        >>> n.add(4, 1)
        >>> print n
        {1: 0 {2: 3, 3: 2}, 2: 0 {}, 3: 0 {}, 4: 0 {1: 1}}
        """
        if not isinstance(sink, list): sink = [sink]
        try:  #single node addition
            self[source] += (sink * capacity)   #XXX inefficient if capacity large
        except TypeError:  #multiple node addition
            if not isinstance(source, list): raise "source must be hashable object or list type"
            if sink: self.add(sink)
            for s in source:  #XXX will add same tails multiple times
                self[s].__iadd__(sink*capacity, 0)

    def update(self, other, default=None, collision=MERGE_NODE):
        """Merges one graph with another.  All vertices will be convertex to VertexType.  Takes union of edge
        >>> n, g = Network(), Graph()
        >>> n.add(1, [1, 2])
        >>> g.add(3, [2, 3]); g.add(1, 2, 3); g.add(1, 4, 2)
        >>> n.update(g)
        >>> print n
        {1: 0 {1: 1, 2: 4, 4: 2}, 2: 0 {}, 3: 0 {2: 1, 3: 1}, 4: 0 {}}
        >>> g.add(3, 5)  #changes to g should not affect n
        >>> n.validate()
        >>> n2 = Network(g)
        >>> n2.energy.update({1: 5, 3: 1})
        >>> print n2
        {1: 5 {2: 3, 4: 2}, 2: 0 {}, 3: 1 {2: 1, 3: 1, 5: 1}, 4: 0 {}, 5: 0 {}}
        >>> n.energy[1] += 2
        >>> n.update(n2)
        >>> print n
        {1: 7 {1: 1, 2: 7, 4: 4}, 2: 0 {}, 3: 1 {2: 2, 3: 2, 5: 1}, 4: 0 {}, 5: 0 {}}
        
        """
        assert isinstance(other, Graph), "Can only merge Graph types."
        for nid, node in other.iteritems():
            if nid in self:  #do union of edge sets
                collision(self, nid, node)
            else:   #otherwise need to copy the set
                self[nid] = self.VertexType(self, nid, node)
                try:  self.energy[nid] += node.energy
                except AttributeError: pass

    def __call__(self, ticks=1):
        """Advance network for specified ticks, defaults to 1.
        >>> n = Network()
        >>> n.add(1, [2, 4], 2)
        >>> n.add([2, 4], 3)
        >>> n.add(3, 1)
        >>> n.energy[1] += 4
        >>> n()
        >>> assert n.energy == {2: 2, 4: 2}
        >>> n()
        >>> assert n.energy == {2: 1, 3: 2, 4: 1}
        >>> n.energy[1] += 9
        >>> n(2)
        >>> assert n.energy == {1: 3, 2: 3, 3: 4, 4: 3}
        >>> n.ticks
        4

        Also aborts once flow reaches zero.
        >>> n.discard(3, 1)
        >>> n(100)
        >>> assert n.energy == {3: 13}
        >>> n.ticks
        9
        """
        assert ticks>=0     #may desire ticks<0 to run in reverse
        energy = self.energy
        for tic in xrange(ticks):
            flow = 0
            energy.update(self.io)
            active_nodes = map(operator.getitem, [self]*len(energy.keys()), energy.iterkeys())
            for node in active_nodes:
                energy[node._id] = node._push(energy[node._id], self.ticks)
                #f = (energy[node._id] != start_energy)
                #if not f: active_nodes.remove(node) #don't update in next loop
                flow |= (node.flow != {})
            for node in active_nodes:   #have to wait until all flow calculations done to avoid adding energy to unvisited nodes.
                energy.update(node.flow)
            if flow: self.ticks += 1
            else: break

    def node_energy(self):
        """Returns total amount of energy in nodes.
        >>> n = Network()
        >>> n.energy[1] = 4
        >>> n.energy[3] = -1
        >>> n.total_energy
        3
        """
        return len(self.energy)
        
    total_energy = property(node_energy, None, None, "Total energy in network.")

    def _flow(self):
        """Returns total amount of energy moved in last tick.
        >>> n = Network()
        >>> n[1][2] = 2
        >>> n[2][3] = 1
        >>> n.energy[1] = 4
        >>> n()
        >>> n.flow
        2
        >>> n()
        >>> n.flow
        3
        """
        sum = 0
        for n in self.itervalues():
            sum += n.energy_out
        return sum

    flow = property(_flow, None, None, "Total energy moved on last tick.")

    def clear(self):
        super(Network, self).clear()
        self.energy.clear()
        self.ticks = 0
        
    def validate(self):
        for node in self.itervalues():
            node.validate()
        for energy in self.energy.itervalues():
            assert energy!=0    #should should be in imbag.validate()
        super(Network, self).validate()

        
def _test():
    import doctest, network
    return doctest.testmod(network, isprivate=lambda i, j: 0)
          
if __name__ == '__main__': _test()
               
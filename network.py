#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 7, 2002

"""Network class for flow networks."""

__version__ = "$Revision: 2.5 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/08/08 22:15:58 $"

#Add Network.time to track how many ticks

import random
from graph import *
from bag import *

DEFAULT_CAPACITY = 1

class Node(WVertex):
    """Node in a flow network."""
    
    __slots__ = ['flow']
    
    def __init__(self, network, id, init={}, capacity=DEFAULT_CAPACITY, collision=ADD):
        super(Node, self).__init__(network, id, init, capacity, collision)
        self.flow = imbag()

    def add(self, sink, capacity=DEFAULT_CAPACITY, collision=ADD):
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
        super(Node, self).add(sink, capacity, collision)
    
    def update(self, sinks, capacity=DEFAULT_CAPACITY, collision=ADD):
        """Update arcs leaving node.  If arc already exists, capacity is
        add to existing value; if not, it is created with default capacity.
        >>> n = Network()
        >>> n[1].update([1, 1, 2, 3, 1])
        >>> print n[1]
        0 {1: 3, 2: 1, 3: 1}
        >>> n[1].update({2: 3, 4: 2})
        >>> print n[1]
        0 {1: 3, 2: 4, 3: 1, 4: 2}
        >>> n[1].update([5, 1], 3)
        >>> print n[1]
        0 {1: 6, 2: 4, 3: 1, 4: 2, 5: 3}
        """
        super(Node, self).update(sinks, capacity, collision)
    
    def __call__(self, bits):
        """Advance node 1 time increment. Returns amount of energy transferred.
        Should not be run except through Network().
        >>> n = Network()
        >>> n[1][2] = 2
        >>> n.energy[1] = 3
        >>> n[1](n.energy[1])
        2
        
        Negative energy values make eneryg flow in reverse direction.
        >>> n = Network()
        >>> n[1][2] = 2
        >>> n[2].energy = -3
        >>> n()
        >>> print n
        {1: -2 {2: 2}, 2: -1 {}}
        """
        assert bits #should not be called with 0 bits
        paths = [] #self.flow.clear()
        startbits = bits
        if bits >= 0:
            paths = reduce(operator.add, [[tail]*capacity for tail, capacity in self.iteritems()], [])
            bit = 1
            assert len(paths) == self.sum_out()
        else:
            g = self._graph     #this optimization needed in a list comprehension?
            paths = reduce(operator.add, [[head]*g[head][self._id] for head in self.in_vertices()], [])
            bit = -1
            assert len(paths) == self.sum_in()
        while bits and paths:
            path = random.choice(paths)     #faster than doing one shuffle at the beginning (v2.2)
            self.flow[path] += bit
            bits -= bit
            paths.remove(path)
        #self.energy = bits     #give back left-over energy, if any, for next round
        return startbits-bits   #bit flow

    def _energy_out(self):
        return len(self.flow)
        
    def _energy_read(self):
        return self._graph.energy[self._id]
        
    def _energy_write(self, value):
        self._graph.energy[self._id] = value
        
    energy_out = property(_energy_out, None, None, "Energy out of node.")
    energy = property(_energy_read, _energy_write, None, "Energy at node. Slow -- use network.energy[id]")

    def __str__(self):
        """Returns string with energy level and arc info.
        >>> n = Network()
        >>> n.add(1, 2)
        >>> n[1].energy += 5
        >>> print n[1]
        5 {2: 1}
        """
        return str(self.energy) + " " + super(Node, self).__str__("%r: %s")
        
    def validate(self):
        #assert self.energy >= 0, "Invalid energy value %r at node %r" % (self.energy, self._id)
        for node, cap in self.iteritems():
            assert cap >= 0, "Invalid capacity at node %r: %r" % (node, cap)
        super(Node, self).validate()
        

class Network(Graph):
    """Flow network class."""

    __slots__ = ['energy', 'ticks']

    def __init__(self, init={}, VertexType=Node):
        super(Network, self).__init__(init, VertexType)
        self.energy = imbag()
        self.ticks = 0

    def add(self, head, tail=[], capacity=DEFAULT_CAPACITY, edge_collision=ADD):
        """Like Graph.add, but will accumulate edge values, instead of
        overwriting them.  See Graph.add.__doc__.
        >>> n = Network()
        >>> n.add(1, [2, 3], 2)
        >>> n.add(1, 2)
        >>> print n
        {1: 0 {2: 3, 3: 2}, 2: 0 {}, 3: 0 {}}
        """
        super(Network, self).add(head, tail, capacity, edge_collision)
                    
    def __call__(self, count=1):
        """Advance network count time increments, defaults to 1.
        >>> n = Network()
        >>> n.add(1, 2, 2)
        >>> n.add(2, 3)
        >>> n.add(3, 1)
        >>> n.energy[1] += 4
        >>> n()
        >>> assert n.energy == {1: 2, 2: 2}
        >>> n()
        >>> assert n.energy == {2: 3, 3: 1}
        >>> n.energy[1] += 4
        >>> n(2)
        >>> assert n.energy == {1: 2, 2: 5, 3: 1}
        >>> n.discard(3, 1)
        >>> n.add(2, 1)
        >>> n(100)
        >>> assert n.energy == {3: 8}
        """
        assert count>=0     #may desire count<0 to run in reverse
        energy = self.energy
        for tic in range(count):
            self.ticks += 1
            flow = 1
            active_nodes = map(operator.getitem, [self]*len(energy.keys()), energy.iterkeys())
            for node in active_nodes:
                node.flow.clear()
                energy[node._id] -= node(energy[node._id])
                #energy[node._id] -= flow
            for node in active_nodes:
                energy.update(node.flow)
            if flow == 0: break

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
        
    def validate(self):
        for node in self.itervalues():
            node.validate()
        for energy in self.energy.itervalues():
            assert energy!=0    #should should be in imbag.validate()
        super(Network, self).validate()
        
def _test():
    import doctest, network
    return doctest.testmod(network)
          
if __name__ == '__main__': _test()
               
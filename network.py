#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 7, 2002

"""Network class for flow networks."""

__version__ = "$Revision: 2.1 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2002/07/08 23:57:13 $"

import random
from graph import *

DEFAULT_CAPACITY = 1

class Node(WVertex):
    """Node in a flow network."""
    
    __slots__ = ['_energy', 'energy_out']
    
    def __init__(self, network, id, init={}, capacity=DEFAULT_CAPACITY):
        super(Node, self).__init__(network, id, init, capacity)
        self.energy_out = 0
        self._energy = [0, 0]
        
    def tick(self):
        """Advance node 1 time increment. Returns amount of energy transferred."""
        if not self.energy: return   #nothing to do
        paths = [] 
        for tail, capacity in self.iteritems():
            paths.extend([tail]*capacity)
        assert len(paths) == self.sum_out()
        while paths and self.energy:
            path = random.choice(paths)
            paths.remove(path)
            self._transfer(path)    #move 1 bit of energy
        self._transfer(self._id, self.energy)    #give back left-over energy, if any
            
    def _transfer(self, tail, energy=1):
        g = self._graph
        g[tail]._energy[not g._current_state] += energy
        self._energy[g._current_state] -= energy
    
    def read(self):
        return self._energy[self._graph._current_state]
    
    def write(self, energy):
        self._energy[self._graph._current_state] = energy
    
    energy = property(read, write, None, "Energy at node.")
        
    def __str__(self):
        """Returns string with energy level and edge info.
        >>> n = Network()
        >>> n.add(1, 2)
        >>> n.source(1, 5)
        >>> print n[1]
        5 {2: 1}
        """
        return str(self.energy) + " " + super(Node, self).__str__("%r: %s")
        

class Network(Graph):
    """Flow network class."""

    __slots__ = ['_current_state']

    def __init__(self, init={}, VertexType=Node):
        super(Network, self).__init__(init, VertexType)
        self._current_state=0

    def tick(self, count=1):
        """Advance network count time increments, defaults to 1.
        >>> n = Network()
        >>> n.add([1, 2], 3, 2)
        >>> n.add(3, 2)
        >>> n.source(1, 4)
        >>> n.tick()
        >>> print n
        {1: 2 {3: 2}, 2: 0 {3: 2}, 3: 2 {2: 1}}
        >>> n.tick()
        >>> print n
        {1: 0 {3: 2}, 2: 1 {3: 2}, 3: 3 {2: 1}}
        """
        assert count>=0
        for tic in range(count):
            for node in self.itervalues():
                node.tick()
        self._current_state = not self._current_state
    
    def source(self, node, energy=1):
        """Add energy to node.  Defaults to 1 energy unit.
        >>> n = Network()
        >>> n.add([1, 2], [2, 3, 1])
        >>> n[2].energy
        0
        >>> n.source(2)     #defaults to 1 energy unit
        >>> n[2].energy
        1
        >>> n.source(2, 8)  #input 8 energy units into node 2
        >>> n[2].energy
        9
        """
        assert isinstance(energy, int)
        assert energy >= 0
        self[node].energy += energy
        
    def node_energy(self):
        """Returns total amount of energy in nodes."""
        
    def flow(self):
        """Returns total amount of energy moved."""
        
def _test():
    import doctest, network
    return doctest.testmod(network)
          
if __name__ == '__main__': _test()
               
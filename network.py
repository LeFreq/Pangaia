#!/usr/bin/env python
# Mark Janssen, <average@mit.edu> July 7, 2002

"""Network class for flow networks."""

__version__ = "$Revision: 2.11 $"
__author__  = "$Author: average $"
__date__    = "$Date: 2003/06/18 09:48:11 $"

#Add Network.time to track how many ticks
#Have Network.add(v), add +1 to v.energy, may need to split function for
#separate add_edge(h,t) function

from __future__ import generators

import random, operator
from graph import *
from bag import *

_DEBUG = True
DEFAULT_CAPACITY = 1
DEFAULT_FLOW = 1

NodeBaseType = IntegerBag
FlowType = IntegerBag

class Node(NodeBaseType, WeightedEdgeMixin):
    """Node in a flow network."""

    __slots__ = ['flow', 'last_tick', '_graph', '_id'] #XXX have to define _graph and _id since aren't inheriting from Vertex!

    def __init__(self, network, id, init={}):  #XXX parent class should do most of this
        self._graph = network
        self._id = id
        self.flow = FlowType()
        super(Node, self).__init__(init)  #parent class should call Node.__setitem__ to add Nodes to Network if necessary.

    def add(self, sink, capacity=DEFAULT_CAPACITY): #should be able to use Vertex.add()??
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
        try:    #single sink addition
            self[sink] += capacity
        except TypeError, error:  #list of sinks given
            if not isinstance(sink, list): raise TypeError(error)
            for s in sink: #XXX should be able to use new bag.update_fromkeys()
                self[s] += capacity

    def discard(self, sink):
        """Removes sink from vertex, if exists, and flow value.

        >>> n = Network({1: {}, 2: {}, 3: {}})
        >>> #n.discard([2, 3])  #XXX fails
        >>>
        """
        super(Node, self).discard(sink) #FIXME this does not call Vertex.discard but bag.discard!! (can't discard list of tails)
        self.flow.discard(sink)

    def __setitem__(self, sink, capacity):  #XXX should be able to use Vertex.__setitem__()
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

        Negative capacity reverses the sign (positive/negative) of the energy.
        >>> n[3][1] = -2
        >>> n()
        >>> n.energy
        {1: -1, 3: 2}
        """
        assert bits #should not get called with 0 bits
        paths = self.paths(bits)
        self.last_tick = tick   #XXX would like to set last_tick and clear flow only if paths!=[]
        self.flow.clear()       #clear old flow values
        bit = (bits>=0 and 1 or -1)
        while bits and paths:   #this could be faster by checking for path saturation (see rev2.8)
            path = paths.pop(int(random.random()*len(paths)))
            #change sign of bit transferred if path has negative capacity
            if bit>0: self.flow[path] += (bit*(self[path]>=0 and 1 or -1))      #XXX what about negative weights?
            else: self.flow[path] += (bit*(self._graph[path][self._id] >=0 and 1 or -1))
            bits -= bit
        return bits   #return remaining bits for next round

    def paths(self, bits):
        if bits >= 0:       #forward flow
            return list(self)   #reduce(operator.add, [[tail]*capacity for tail, capacity in self.iteritems()], [])
        else:               #backward flow
            g = self._graph     #this optimization needed in a list comprehension?
            return reduce(operator.add, [[head]*abs(g[head][self._id]) for head in self.in_vertices()], [])

    def flow_in(self):
        """Return bag with incoming flow.

        >>> n = Network()
        >>> n[1][2] = 2
        >>> n.energy[1] = 3
        >>> n() #n[1]._push(n.energy[1]. n.ticks)
        >>> n[1].flow_in()
        {}
        >>> n[2].flow_in()
        {1: 2}
        """
        b = FlowType()
        for n in self._graph.itervalues():
            if self._id in n.flow:
                b[n._id] += n.flow[self._id]
        return b

    def flow_out(self): return self.flow

    def _energy_out(self):  return sum(self.flow.itervalues())
    def _energy_in(self): return sum(self.flow_in().itervalues())
    def _energy_read(self): return self._graph.energy[self._id]
    def _energy_write(self, value):  self._graph.energy[self._id] = value

    energy_out = property(_energy_out, None, None, "Energy out of node.")
    energy_in = property(_energy_in, None, None, "Energy in to node.")
    energy = property(_energy_read, _energy_write, None, "Energy at node. Slow -- use network.energy[id]")

    def clear(self):
        super(Node, self).clear()
        self.flow.clear()
        self.energy = 0

    def __str__(self):
        """Returns string with energy level and arc info.
        >>> n = Network()
        >>> n.add(1, 2)
        >>> n[1].energy += 5
        >>> print n[1]
        5 {2: 1}
        """
        #perhaps list arcs sorted by capacity
        return "%r %s" % (self.energy, super(Node,self).__str__())

    def _validate(self):
        """Call all base class validation methods.

        >>> n = Network()
        >>> n.add(1, 2, 3)
        >>> n[1]._id = 2  #vertex 1 given id of 2
        >>> n[1]._validate()
        Traceback (most recent call last):
        AssertionError: _graph[_id] is not self
        >>> n[1]._id = 1
        >>> n[1].flow[3] = 7  #n[1][3] non-existent
        >>> n[1]._validate()
        Traceback (most recent call last):
        AssertionError: flow encountered on non-existent edge
        """
        for dest in self.flow:
            assert dest in self or dest in self.in_vertices(), "flow encountered on non-existent edge"
        super(Node, self)._validate()
        super(WeightedEdgeMixin, self)._validate() #FIXME


class Source(Node):
    """Special node that produces flow to other nodes.

    >>> n = Network({1: {2: 2}})
    >>> n.attach('source', Source)
    >>> n['source'][1] = 1  #capacity determines how much energy transferred at each tick
    >>> n['source'][2] = 4
    >>> n(2)  #2 ticks
    >>> print n
    {1: 1 {2: 2}, 2: 9 {}, 'source': 5 {1: 1, 2: 4}}

    If energy is set negative, then negative flow flows back into in-vertices.
    >>> n['source'].energy = -100   #XXX must set high to offset any positive incoming flow
    >>> n[2].energy = 0             #XXX this shouldn't be necessary
    >>> n[2]['source'] = 5
    >>> n()
    >>> print n
    {1: 0 {2: 2}, 2: -4 {'source': 5}, 'source': -5 {1: 1, 2: 4}}
    """

    __slots__ = []

    def __init__(self, network, id, init={}):
        super(Source, self).__init__(network, id, init)
        self.energy = self.sum_out() or DEFAULT_FLOW

    def _pull(self):
        return 'As_Much_As_Needed'

    def _push(self, bits, tick):
        assert bits == self.energy
        self.flow.clear()
        bit_id = self._pull()
        if bit_id:
            if bits >= 0:
                self.flow += self #flow will be equal to out vertices' capacity
                return self.sum_out()
            else: #XXX find better way to do this -- should WVertex have a method for this?
                self.flow -= FlowType([(tail, self._graph[tail][self._id]) for tail in self.in_vertices()])
                return -self.sum_in()
        return 0


class FileSource(Source): #cannot multiple inherit from file also
    """Special node that produces flow to other nodes from file source.

    Files can be used to specify specific intervals for incoming energy to designated nodes.
    Whitespace characters designate skipped network ticks.
    >>> fn = '/tmp/network.tmp'
    >>> f = file(fn, 'w')
    >>> f.write('a1 Aq'); f.close()
    >>> n = Network()
    >>> n.attach(fn, FileSource)
    >>> print n, type(n[fn])
    {'/tmp/network.tmp': 1 {}} <class 'network.FileSource'>
    >>> n()
    >>> print n
    {'/tmp/network.tmp': 1 {'A': 1}, 'A': 1 {}}

    The amount of energy for each character is determined by the the source energy value
    >>> n[fn].energy = 5  #add 5 bits to each node[character]
    >>> n(100)
    >>> print n
    {'/tmp/network.tmp': 0 {'A': 2, 'Q': 1}, 'A': 6 {}, 'Q': 5 {}}
    >>> n.ticks
    3
    >>> n[fn].source.closed
    True
    """

    #interesting thing to consider network making connections to Source.
    #  when Source is absent, edges are left dangling waiting for it to return.
    #perhaps a way to make source.energy automatic: network gets to say when it wants input
    #  (by sending energy to it? NO: by retrieving its out_flow (i.e. downstream neuron has expectation>reality?).)

    __slots__ = ['source']

    def __init__(self, network, filename, init={}):
        super(FileSource, self).__init__(network, filename, init)
        self.source = open(filename, 'r')
        #perhaps self.energy == self.source.size()

    def _pull(self):
        bit_id = self.filter(self.source.read(1)) #read one character at a time
        return bit_id or self.source.close() #XXX relies on close() returning None

    def _push(self, bits, tick):
        """Reads information from source, propagates to downstream nodes."""
        assert bits == self.energy, "Unexpected bits value: " % bits
        self.flow.clear()
        bit_id = self._pull() #XXX should make Network call this
        if bit_id:
            if bit_id.isalpha():     #skip non-alpha
                self.add(bit_id)     #add edge, will also add bit_id to network
                self.flow[bit_id] += bits
                self.last_tick = tick
            return bits        #XXX could return filesize - 1
        else: return 0  #EOF:  nothing left for this source

    def filter(self, bit_id):
        """Converts alphabetic characters to uppercase, empty string to None, all others returns a space."""
        if bit_id.isalpha(): return bit_id.upper()
        elif not bit_id: return None #EOF
        else: return " " #all non-alphabetic treat as space

    def __del__(self):
        #super(FileSource, self).__del__()
        self.energy = 0
        self.source.close()

    def _validate(self):
        assert self._id == self.source.name, "Mismatched id: %s != %s" % (self._id, self.source.name)
        assert len(self.flow_in()) == 0, "Unexpected flow_in: %s" % self.flow_in()
        assert self.in_degree() == 0, "Unexpected in_vertices: %s" % list(self.in_vertices())
        super(FileSource, self)._validate()


class Sink(Node):
    """Special node type.  Energy leaves network out of here.

    >>> n = Network({1: {2: 1}})
    >>> n[1].energy += 1
    >>> n.attach('sink', Sink)
    >>> n[2]['sink'] = 2
    >>> n()
    >>> print n
    {1: 0 {2: 1}, 2: 1 {'sink': 2}, 'sink': 0 {}}
    >>> n()
    >>> print n
    {1: 0 {2: 1}, 2: 0 {'sink': 2}, 'sink': 1 {}}
    >>> n()
    sink: 1
    >>> print n
    {1: 0 {2: 1}, 2: 0 {'sink': 2}, 'sink': 0 {}}
    """

    #XXX what if energy is negative?

    __slots__ = []

    def _push(self, bits, tick):
        assert bits
        print "%s: %s" % (self._id, bits)  #all bits sent to screen
        return 0

    def _validate(self):
        assert len(self.flow) == 0, "Unexpected flow_out: %s" % self.flow_out()
        assert self.out_degree() == 0
        super(Sink, self)._validate()


class Network(Graph):
    """Flow network class."""
    #XXX need way to synchronize changes to Network.energy with graph; i.e. n.energy[non-existent-node] += x.
    #perhaps have Network derive from bag and have the graph be an attribute of the network; i.e. n.graph[1][2]==capacity, n[1][2]==flow

    __slots__ = ['energy', 'ticks']

    def __init__(self, init={}, VertexType=Node):
        """Create the network, optionally initializing from other graph type.

        >>> n = Network({1: {2: 1, 3: 2}})
        >>> n.energy[1] += 2
        >>> print n
        {1: 2 {2: 1, 3: 2}, 2: 0 {}, 3: 0 {}}
        >>> n2 = Network(n)
        >>> n.energy[2] += 4   #should not affect n2
        >>> print n2
        {1: 2 {2: 1, 3: 2}, 2: 0 {}, 3: 0 {}}
        """
        if not issubclass(VertexType, Node): raise TypeError("Invalid node type")
        self.energy = FlowType()   #stores energy values at each node
        self.ticks = 0           #number of network clock ticks since creation
        super(Network, self).__init__(init, VertexType) #will call update()

    def update(self, other, default=USE_DEFAULT, collision=MERGE_VERTEX):
        """Merges one graph with another.  All vertices will be convertex to VertexType.  Takes union of edge
        >>> n, g = Network(), Graph(VertexType=WVertex)
        >>> n.add(1, [1, 2])
        >>> g.add(3, [2, 3]); g.add(1, 2, 3); g.add(1, 4, 2)
        >>> n.update(g)
        >>> print n
        {1: 0 {1: 1, 2: 4, 4: 2}, 2: 0 {}, 3: 0 {2: 1, 3: 1}, 4: 0 {}}
        >>> g.add(3, 5)  #changes to g should not affect n
        >>> n._validate()
        >>> n2 = Network(g)
        >>> n2.energy.update({1: 5, 3: 1})
        >>> print n2
        {1: 5 {2: 3, 4: 2}, 2: 0 {}, 3: 1 {2: 1, 3: 1, 5: 1}, 4: 0 {}, 5: 0 {}}
        >>> n.energy[1] += 2
        >>> n.update(n2)
        >>> print n
        {1: 7 {1: 1, 2: 7, 4: 4}, 2: 0 {}, 3: 1 {2: 2, 3: 2, 5: 1}, 4: 0 {}, 5: 0 {}}
        """
        #XXX if other has invalid (non-Integer) values then exception raised midway through!
        super(Network, self).update(other, default, collision)
        if isinstance(other, Network): #what about other.io?
            self.energy += other.energy

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
        for tic in xrange(ticks):  #XXX active_nodes does not include nodes with flow but no energy.
            active_nodes = [self[nid] for nid in self.energy.iterkeys()] #XXX will add nodes that have no edges and cannot transfer flow
            flow = self._push(active_nodes)
            self._pull(active_nodes)
            if flow: self.ticks += 1
            #else: break

    def _push(self, active_nodes):
        flow = 0
        for node in active_nodes:
            self.energy[node._id] = node._push(self.energy[node._id], self.ticks)
            #f = (energy[node._id] != start_energy)
            #if not f: active_nodes.remove(node) #don't update in next loop
            flow += (abs(node.flow))
        return flow

    def _pull(self, active_nodes):  #XXX should call node._pull() so node can have info on who gave energy
        for node in active_nodes:   #have to wait until all flow calculations done to avoid adding energy to unvisited nodes.
            self.energy.update(node.flow)

    def node_energy(self):
        """Returns total amount of energy in nodes.
        >>> n = Network()
        >>> n.energy[1] = 4
        >>> n.energy[3] = -1
        >>> n.total_energy
        3
        """
        return sum(self.energy.itervalues()) #bag should have method for this already

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

    total_energy = property(node_energy, None, None, "Total energy in network.")
    flow = property(_flow, None, None, "Total energy moved on last tick.")

    def attach(self, name, node_type):
        """Attach a special node type to the network with given name. """
        self[name] = node_type(self, name)

    def __delitem__(self, key):
        """Remove node and associated energy from network.

        >>> n = Network()
        >>> n.add([1,2],[2,3])
        >>> n.energy += [1, 2, 2]
        >>> del n[2]
        >>> n._validate()
        """
        #XXX haven't checked if everything done here...
        super(Network, self).__delitem__(key)
        self.energy.discard(key) #Note: may be called with list from discard() so do this last

    def display_energy(self):
        """Display energy and flow values across network.

        >>> n = Network()
        >>> n.add(range(3), 2)
        >>> n.energy[1] += 2
        >>> n.display_energy()
        1: 2 {}
        >>> n()
        >>> n.display_energy()
        1: 1 {2: 1}
        2: 1 {}
        >>> n()
        >>> n.display_energy()  #will show nodes with either energy or flow
        1: 0 {2: 1}
        2: 2 {2: 1}
        """
        if _DEBUG: self._validate()
        for nid, n in self.iteritems():
            if self.energy[nid] or n.flow:
                print "%s: %s %s" % (nid, self.energy[nid], self[nid].flow)

    def clear(self):
        super(Network, self).clear()
        self.energy.clear()
        self.ticks = 0

    def _validate(self):
        """Assert Network invariants.

        >>> n = Network()
        >>> n.add([1, 2, 3])
        >>> n.energy[2] += 5
        >>> dict.__delitem__(n, 2)
        >>> print n
        Traceback (most recent call last):
        AssertionError: Energy exists on non-existant node
        """
        super(Network, self)._validate()
        self.energy._validate()
        assert self.ticks >= 0, "Invalid tick value"
        for vid in self.energy:
            assert vid in self, "Energy exists on non-existant node"


def _test():
    """Miscellaneous tests...

    Check Node.update() and Node.__iadd__() add sinks to network.
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

    >>> n = Network()
    >>> n.add(1, [2, 3], 2)
    >>> n.add(1, 2)
    >>> n.add(4, 1)
    >>> print n
    {1: 0 {2: 3, 3: 2}, 2: 0 {}, 3: 0 {}, 4: 0 {1: 1}}
    """

    import doctest, network
    return doctest.testmod(network, isprivate=lambda i, j: 0)

if __name__ == '__main__': _test()


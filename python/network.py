#!/usr/bin/env python
# Copyright 2010 Mark Janssen
# This file is licensed under the GNU Public License.
# email: dreamingforward@gmail.com

"""Network class for flow networks.  An exploration for Digital Mechanics."""

#Add Network.time to track how many ticks
#Have Network.add(v), add +1 to v.energy, may need to split function for
#separate add_edge(h,t) function
#use logging.debug to record all reads, logging.info to record all writes, logging.error to record TypeError issues, logging.critical for assertions...?

from graph import *
from bag import *

_DEBUG = True

NodeBaseType = IntegerBag
FlowType = IntegerBag


class Node(reverse_edge_mixin, WVertex, NodeBaseType): #order needed for Vertex.discard to override bag.discard
    """Node in a flow network."""

    __slots__ = ['reverse', 'flow_out', 'last_tick']

    def __init__(self, network, id, init={}):
        self.flow_out = FlowType()
        super(Node, self).__init__(network, id, init)  #parent class should call Node.__setitem__ to add Nodes to Network if necessary.
        self.reverse = NodeBaseType(self.reverse)

    def update(self, sinks, capacity=1):
        """Add sinks to node.  If sinks is type Node, then add Node energy too.

        >>> n = Network({1: {1: 1, 2: 4, 3: 9}})
        >>> n[1].energy = 10
        >>> n[2].update(n[1])
        >>> print n[2]
        10 {1: 1, 2: 4, 3: 9}
        """
        NodeBaseType.update(self, sinks, capacity)
        if isinstance(sinks, Node): self.energy += sinks.energy

    add = update
    __getitem__ = NodeBaseType.__getitem__

    def __delitem__(self, sink):
        """Removes outgoing sink and clears any associated flow."""
        super(Node, self).__delitem__(sink)
        self.flow_out.discard(sink)

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
        assert bits                 #shouldn't get called with 0 bits
        self.last_tick = tick       #XXX would like to set last_tick and clear flow only if paths!=[]
        self.flow_out.clear()       #clear old flow values
        if bits >= 0:   #forward flow
            self.flow_out += self.pick(bits, False) #slower than necessary if bits = self.size
            return bits - self.flow_out.size
        else:           #backward flow
            self.flow_out -= self.reverse.pick(abs(bits), False) #pick returns negative values if given negative count
            return bits + self.flow_out.size

    def _flow_in(self):
        """Return bag with incoming flow.

        >>> n = Network()
        >>> n[1][2] = 2
        >>> n[2][3] = 1
        >>> n.energy.update({1: 3, 3: -2})
        >>> n()
        >>> n[1].flow_in
        {}
        >>> n[2].flow_in
        {1: 2, 3: -1}

        Attempts to change flow_in values are ignored, as this value is calculated dynamically:
        >>> n[2].flow_in[1] = 99
        >>> n[2].flow_in
        {1: 2, 3: -1}
        """
        flow_in = FlowType()
        for nid, node in self._graph.iteritems(): #flow may come from out_vertices if energy < 0
            if self._id in node.flow_out:
                flow_in[nid] += node.flow_out[self._id]
        return flow_in

    def _energy_read(self): return self._graph.energy[self._id]
    def _energy_write(self, value):  self._graph.energy[self._id] = value

    flow_in = property(_flow_in, None, None, "Dictionary type containing incoming flow values.")
    energy = property(_energy_read, _energy_write, None, "Energy at node. Faster to use network.energy[id]")

    def clear(self):
        super(Node, self).clear()
        self.flow_out.clear()
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
        >>> n[1].flow_out[3] = 7  #n[1][3] non-existent
        >>> n[1]._validate()
        Traceback (most recent call last):
        AssertionError: flow encountered on non-existent edge
        """
        for dest in self.flow_out:
            assert dest in self or dest in self.reverse, "flow encountered on non-existent edge"
        super(Node, self)._validate()


class Source(Node):  #Crown
    """Special node that produces flow to other nodes.

    >>> n = Network({1: {2: 2}})
    >>> n.attach(Source, 'mysource')
    'mysource'
    >>> n['mysource'][1] = 1  #capacity determines how much energy transferred at each tick
    >>> n['mysource'][2] = 4
    >>> n(2)  #2 ticks
    >>> print n
    {1: 1 {2: 2}, 2: 9 {}, 'mysource': 5 {1: 1, 2: 4}}

    If energy is set negative, then negative flow flows back into in-vertices.
    >>> n['mysource'].energy = -100   #XXX must set high to offset any positive incoming flow
    >>> n[2].energy = 0             #XXX this shouldn't be necessary
    >>> n[2]['mysource'] = 5
    >>> n();  print n
    {1: 0 {2: 2}, 2: -4 {'mysource': 5}, 'mysource': -5 {1: 1, 2: 4}}

    Negative capacities change sign of the energy:
    >>> n[2]['mysource'] = -5
    >>> del n['mysource'][2]
    >>> n();  print n
    {1: -2 {2: 2}, 2: 3 {'mysource': -5}, 'mysource': -5 {1: 1}}

    """

    __slots__ = []

    def __init__(self, *args):
        super(Source, self).__init__(*args)
        self.energy = self.sum_out() or 1  #default flow is the unit integer.

    def _push(self, bits, tick):
        if bits >= 0:
            #if self.size == 0: return bits  #nothing to push (no out edges)
            bits = self.size or bits
            super(Source, self)._push(bits, tick)
            return self.flow_out.size or bits
        else:
            #if self.reverse.size == 0: return bits  #nothing to push (no in edges)
            bits = -self.reverse.size or bits
            super(Source, self)._push(bits, tick)
            return -self.flow_out.size or bits


class FileSource(Source): #cannot multiple inherit from file also
    """Special node that produces flow to other nodes from file source.

    Files can be used to specify specific intervals for incoming energy to designated nodes.
    Whitespace characters designate skipped network ticks.
    >>> fn = '/tmp/network.tmp'
    >>> f = file(fn, 'w')
    >>> f.write('a1 Aq'); f.close()
    >>> n = Network()
    >>> n.attach(FileSource, open(fn))
    '/tmp/network.tmp'
    >>> print n
    {'/tmp/network.tmp': 1 {}}
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

    def __init__(self, network, source_file, init={}):
        """Creates a FileSource node with the name of the source file as it's node id."""
        if not isinstance(source_file, file): raise TypeError("Must be file type")
        self.source = (not source_file.closed) and source_file or open(source_file.name, 'r')
        super(FileSource, self).__init__(network, source_file.name, init)
        #perhaps self.energy == self.source.size

    def _pull(self):
        bit_id = self.filter(self.source.read(1)) #read one character at a time
        return bit_id or self.source.close() #XXX relies on close() returning None

    def _push(self, bits, tick):
        """Reads information from source, propagates to downstream nodes."""
        assert bits == self.energy, "Unexpected bits value: " % bits
        self.flow_out.clear()
        bit_id = self._pull() #XXX should make Network call this
        if bit_id:
            if bit_id.isalpha():     #skip non-alpha
                self[bit_id] += 1    #add edge, will also add bit_id to network
                self.flow_out[bit_id] += bits
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
        assert len(self.flow_in) == 0, "Unexpected flow_in: %s" % self.flow_in
        assert self.in_degree() == 0, "Unexpected in_vertices: %s" % self.reverse
        super(FileSource, self)._validate()


class KeySource(FileSource):
    """Source that takes input from keyboard.  Non-blocking code taken from activestate python cookbook.

    >>> n = Network()
    >>> n.attach(KeySource)
    '<stdin>'
    >>> print n
    {'<stdin>': 1 {}}
    """

    import sys, tty, select

    __slots__ = ['_save_attr']

    def __init__(self, network, tty_source=sys.stdin, init={}):
        if not tty_source.isatty(): raise TypeError("KeySource must be be passed a tty.")
        self._save_attr = KeySource.tty.tcgetattr(tty_source)
        super(KeySource, self).__init__(network, tty_source, init) #XXX skip FileSource init which opens stdin with error

    def _pull(self):
        tty, select = KeySource.tty, KeySource.select.select
        newattr = self._save_attr[:]
        newattr[3] &= ~tty.ECHO & ~tty.ICANON
        tty.tcsetattr(self.source, tty.TCSANOW, newattr)
        if select([self.source], [], [], 0)[0]:  #while select...: self.flow_in[bit]+=1 --read all characters that are ready, not just 1
            bit_id = self.source.read(1)
            if bit_id == '~': #special key to indicate "stop this source"
                self.stop()   #close this source
                return 0
            else: bit_id = self.filter(bit_id)
        else:
            bit_id = ' '
        return bit_id

    def _push(self, bits, tick):
        bits = super(KeySource, self)._push(bits, tick)
        self.stop()
        return bits

    def stop(self):
        KeySource.tty.tcsetattr(self.source, KeySource.tty.TCSADRAIN, self._save_attr)

    __del__ = stop


class Sink(Node):  #root
    """Special node type.  Energy leaves network out of here.

    >>> n = Network({1: {2: 1}})
    >>> n[1].energy += 1
    >>> n.attach(Sink, 'mysink')
    'mysink'
    >>> n[2]['mysink'] = 2
    >>> n()
    >>> print n
    {1: 0 {2: 1}, 2: 1 {'mysink': 2}, 'mysink': 0 {}}
    >>> n()
    >>> print n
    {1: 0 {2: 1}, 2: 0 {'mysink': 2}, 'mysink': 1 {}}
    >>> n()
    mysink: 1
    >>> print n
    {1: 0 {2: 1}, 2: 0 {'mysink': 2}, 'mysink': 0 {}}
    """

    #XXX what if energy is negative?

    __slots__ = []

    def _push(self, bits, tick):
        assert bits
        print "%s: %s" % (self._id, bits)  #all bits sent to screen
        return 0

    def _validate(self):
        assert len(self.flow_out) == 0, "Unexpected flow_out: %s" % self.flow_out()
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
        >>> print n.energy
        {1: 3, 2: 3, 3: 4, 4: 3}
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
            active_nodes = [self[nid] for nid in self.energy] #XXX will add nodes that have no edges and cannot transfer flow
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
            flow += (node.flow_out.size)
        return flow

    def _pull(self, active_nodes):  #XXX should call node._pull() so node can have info on who gave energy
        for node in active_nodes:   #have to wait until all flow calculations done to avoid adding energy to unvisited nodes.
            self.energy.update(node.flow_out)

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
        for node in self.itervalues():
            sum += node.flow_out.size
        return sum

    total_energy = property(node_energy, None, None, "Total energy in network.")
    flow = property(_flow, None, None, "Total energy moved on last tick.")

    def attach(self, node_type, *args):
        """Construct node_type with given arguments and add to the network.  Returns id of node.

        >>> n = Network()
        >>> id = n.attach(KeySource)
        >>> type(n[id]) is KeySource
        True
        """
        node = node_type(self, *args)  #network parameter is automatically passed
        self[node._id] = node
        return node._id

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
            if self.energy[nid] or n.flow_out:
                print "%s: %s %s" % (nid, self.energy[nid], self[nid].flow_out)

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


def run(net, count=10, interval=1):
    """Simple simulation runner, will run for count time-steps on a given network net.
    Use a network with a KeySource attached.  See KeySource doc on how to do that.
    """
    import time
    for i in range(count):
        net()
        net.display()
        time.sleep(interval)


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

    >>> n = Network({1: {}, 2: {}, 3: {}})
    >>> n.discard([2, 3])

    #Test that arbitrary attributes can't be assigned.
    #>>> n[1].test = "BAD"
    #Traceback (most recent call last):
    #AttributeError: 'Node' object has no attribute 'test'
    >>> n.test = "BAD"
    Traceback (most recent call last):
    AttributeError: 'Network' object has no attribute 'test'

    Node.__setitem__():
    >>> n = Network()
    >>> n[1][3]
    0
    >>> n[1][2] = 3
    >>> print n
    {1: 0 {2: 3}, 2: 0 {}}
    >>> n[1][2] = "must be int" #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: invalid literal for int(): must be int

    From Network.add:
    >>> n = Network()
    >>> n[1].add([2, 3], 5)
    >>> print n[1]
    0 {2: 5, 3: 5}

    If sink already connected, capacity is accumulates.

    From Network.update():
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

if __name__ == '__main__':
    import doctest
    print doctest.testmod() # network, isprivate=lambda *args: 0)

    #note doctests for keysource don't work within VIDLE shell for some reason (proxy object used for stdin, I think).

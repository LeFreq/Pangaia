#!/usr/bin/env python
# Mark Janssen, <maj64@antisocial.com> June 1, 2003

from network import *

GraphList = []

class SerialIn:

    def __init__(self, network=None):
        if network==None: network=LayerNet()
        self.attach(network)

    def pull(self, info):
        if isinstance(info, list):  #XXX Note recursion: what if info is list in list?
            for bit in info:
                self.pull(bit)
            return
        elif isinstance(info, file):
            for line in info:
                for bit in line:
                    self.pull(bit)
            return
        bit = self.filter(info)
        if bit:
            self.upnet.pull(bit)

    def filter(self, bit):
        if not isinstance(bit, str):
            return bit
        elif bit.isalpha() or bit.isspace():
            return bit.upper()
        else: return None

    def attach(self, network):
        self.upnet = network

    def __str__(self):
        net = self.upnet
        s = ''
        while net is not None:
            net.display() #s += str(net) + '\n'
            net = net.upnet
        return s

class LayerNet(Network):

    def __init__(self):
        super(LayerNet, self).__init__()
        self.upnet = None
        self.lastbit = None
        self.link_threshold = 4
        self.toggle = 0

    def pull(self, bit):
        if bit.isspace():
            self.lastbit = None
            return
        self.add(bit)
        self[bit].energy += 1 #note v.sum_out() == v.energy
        if self.lastbit:
            self[self.lastbit][bit] += 1
            if self[self.lastbit][bit] >= self.link_threshold:
                self.create(self.lastbit, bit)
            elif self.upnet:
                self.upnet.pull(" ")
            self.lastbit = bit
        else: self.lastbit = bit

    def create(self, first, second):
        self.toggle = not self.toggle
        if not self.toggle: return
        if not self.upnet: self.upnet = self.__class__()
        self.upnet.pull(first+second) #XXX could check if both chars and send concat string


#n=LayerNet()
#f=open('/home/average/rent','r')
#last_ch=None
#for line in f:
#    for ch in line:
#        if not ch.isalpha(): continue
#        ch=ch.upper()
#    if last_ch:
#            n.add(last_ch, ch)
#            last_ch = ch
#        else: last_ch=ch
#
#f.close()

import time
import simpy
import random
import sys
import ltecpricalcs as calc
import logging as log
import simtime as l

class ODN(object):
    """This class represents optical distribution Network."""
    #{'lambda':{active: int,Bside_node_id: int, Aside_node_dict: {oid,distance}, }}
    def __init__(self, env,monitoring,name="None"):
        self.env = env
        self.wavelengths = {}
        self.monitoring = monitoring
        self.Bside_nodes = None
        self.Aside_nodes = None
        self.lightspeed = float(200000)
        self.name = name
        #self.upstream = simpy.Store(self.env)
        #self.downstream = simpy.Store(self.env)
        #self.up_proc = self.env.process(self.UpStream())
        #self.down_proc = self.env.process(self.DownStream())

    def set_Aside_nodes(self,Aside_nodes):
        self.Aside_nodes = Aside_nodes

    def set_Bside_nodes(self,Bside_nodes):
        self.Bside_nodes = Bside_nodes

    def create_wavelength(self,wavelength,Bside_node=None):
        self.wavelengths[wavelength] = {"active": 0, "Bside_node": Bside_node,
            "upstream": simpy.Store(self.env), "downstream": simpy.Store(self.env),
            "up_proc": self.env.process(self.UpStream(wavelength)), "down_proc": self.env.process(self.DownStream(wavelength)) }

    def activate_wavelength(self, wavelength, Bside_node=None):
        self.wavelengths[wavelength]["active"] = 1
        if Bside_node != None:
            self.wavelengths[wavelength]["Bside_node"] = Bside_node

    def propagation_delay(self,Aside_node):
        #print "LEN Aside_nodes: %d" % len(self.Aside_nodes)
        #print "ODN NAME: %s - ASIDE NODE= %d" % (self.name,Aside_node)
        #print self.Aside_nodes
        #print "ODN NAME: %s - ASIDE NODE[2] = %d" % (self.name, self.Aside_nodes[2].oid)
        #print "BLI %d" % self.Aside_nodes[Aside_node].distance

        distance = self.Aside_nodes[Aside_node].distance

        delay = distance/self.lightspeed
        #print("p delay={}".format(delay))
        yield self.env.timeout(delay) #propagation delay

    def splitter_up(self,Aside_node,wavelength,pkt):
        prop = self.env.process( self.propagation_delay(Aside_node) )
        yield prop
        #print "ASIDENODE: %d" % Aside_node
        Bside_node = self.wavelengths[wavelength]["Bside_node"]
        #print "BSIDENODE: %d" % Bside_node
        #print(" {} - pkt exit at {}".format(Aside_node,self.env.now))
        try:
            self.Bside_nodes[Bside_node].ULInput.put(pkt)
        except Exception as e:
            print "ODN NAME %s - BSIDE NODE - %d - %s" % (self.name,Bside_node, e)
            sys.exit(0)

    def splitter_down(self,msg):
        prop = self.env.process( self.propagation_delay(msg['id']) )
        yield prop
        #print(" {} - grant exit at {}".format(msg['id'],self.env.now))
        self.Aside_nodes[msg['id']].DLInput.put(msg)

    def UpStream(self,wavelength):
        while True:
            Aside_node,pkt,wavelength = yield self.wavelengths[wavelength]['upstream'].get()

            #print("{} - up at {}".format(Aside_node,self.env.now))
            self.monitoring.pkt_sent(pkt.size,wavelength)
            self.monitoring.set_UL_bw(pkt.src,wavelength,pkt.size,self.env.now)
            self.env.process( self.splitter_up(Aside_node,wavelength,pkt))

    def DownStream(self,wavelength):
        while True:
            msg = yield self.wavelengths[wavelength]['downstream'].get()
            print self.env.now
            #print("{} - down".format(msg['id']))
            self.env.process(self.splitter_down(msg))

    # def ethernetBW(self,pkt):
    #     pkt.size
    #     calc = ((BW_bits * interval_pkt_sec) / 8) / eth_pktsize_byte

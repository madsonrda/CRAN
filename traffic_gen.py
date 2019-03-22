import time
import simpy
import random
import logging as log
import ltecpricalcs as calc
import simtime as l
import math

class Packet(object):
    """ This class represents a network packet """
    def __init__(self, time, size,id, cpri_option,cell,split=1,coding=23,src="a", dst="z", interval=0.004, mtu=1500, qos=1):
        self.time = time# creation time
        self.id = id # packet id
        self.src = src #packet source address
        self.dst = dst #packet destination address
        self.cell = cell
        self.size = size
        self.interval = interval
        # if id % 2 == 0:
        #     self.qos = 1
        # else:
        #     self.qos = 4

        #self.qos = qos # if qos==4 it goes to extended slot table
        self.qos = 1 # if qos==1 it goes to normal slots and (eventually) grant slots
        
        #BRUNO
        self.mtu = mtu
        self.split = split
        self.cpri_option = cpri_option 
        self.coding = coding 
        size_mbps=(calc.UL_splits[str(self.cpri_option)][split]['bw']) * interval
        self.cpri_size = calc.size_bits(size_mbps)
        #print "SIZE PKT: %f" % self.size
        #BRUNO

    def __repr__(self):
        return "id: {}, src: {}, time: {}, size: {}".\
            format(self.id, self.src, self.time, self.size)

class PacketGenerator(object):
    """This class represents the packet generation process """
    def __init__(self, env, id, ONU, bbu_store,cell,cpri_option=1,interval=0.004, finish=float("inf"), qos=4, split=1):
        self.id = id # packet id
        self.ONU = ONU
        self.cell = cell
        self.bbu_store = bbu_store
        self.env = env # Simpy Environment
        self.cpri_option = None # Fixed packet size
        self.finish = finish # packe end time
        self.qos = qos
        self.split = split

        self.packets_sent = 0 # packet counter
        self.eth_overhead = 0.0
        self.pkt_size = 1500 # ethernet MTU SIZE
        self.number_of_burst_pkts = 0
        self.interval = interval #intervalo entres os Ack
        self.CpriConfig(cpri_option,self.pkt_size)# set CPRI configurations
        self.action = env.process(self.run())  # starts the run() method as a SimPy process

    def CpriConfig(self, cpri_option,pkt_size,split=1):

        self.cpri_option = cpri_option
        #print("{}:{} - my cpri is {}".format(self.env.now,self.id,self.cpri_option))

        # ETH PKTs CALCULATION
        #BW= ((BW_bits * interval_pkt_sec) / 8) / eth_pktsize_byte
        MTU_size = pkt_size
        bw_bytes = calc.get_bytes_cpri_split(cpri_option,split,self.interval)

        n_pkts, last_pkt_size = calc.num_eth_pkts(cpri_option,split,self.interval,MTU_size)
        
        #last_pkt_size= bw_bytes % MTU_size

        self.eth_overhead = 26.0/pkt_size
        self.number_of_burst_pkts = n_pkts
        
        self.last_pkt_size=last_pkt_size

        print "CPRI OPTION %d SPLIT %d: %f \
        BYTES EM %dms: %f \
        NUM ETH PKTS (MTU 1500): %d " % \
        (cpri_option,split, calc.get_bw_cpri_split(cpri_option,split), self.interval*1000, bw_bytes, n_pkts)
        #print self.number_of_burst_pkts
        #print bw_bytes
        #print math.ceil(n_pkts)


    def run(self):
        """The traffic generator function used in simulations.
        """
        while self.env.now < self.finish:
            # wait for next transmission
            yield self.env.timeout(self.interval)

			#creating a list with the pkts that will be sent
            p_list = []
            #npkt = (self.number_of_burst_pkts*4)/10
            for i in range(self.number_of_burst_pkts):
                self.packets_sent += 1
                p = Packet(self.env.now,self.pkt_size ,self.packets_sent, self.cpri_option,\
                self.cell,src=self.id,interval=self.interval,mtu=self.pkt_size,qos=self.qos)
                p_list.append(p)
            if self.last_pkt_size>0:
                self.packets_sent += 1
                p = Packet(self.env.now,self.last_pkt_size ,self.packets_sent, self.cpri_option,\
                self.cell,src=self.id,interval=self.interval,mtu=self.pkt_size,qos=self.qos)
                p_list.append(p)

			#Cpri over Ethernet overhead timeout
            #self.env.timeout(self.eth_overhead)
            #alloc_signal{ONU,pkt,burst}
            if self.last_pkt_size > 0:
                print "NUMBER OF BURST PACKETS ANTES DO ALLOC ########################################"
                burst_with_extra_pkt=self.number_of_burst_pkts + 1
                print "BURST: %d\n" % burst_with_extra_pkt
                alloc_signal = {'onu':self.ONU,'burst':burst_with_extra_pkt,'pkt':p_list[0]}
            else:
                print "NUMBER OF BURST PACKETS ANTES DO ALLOC ########################################"
                print "BURST: %d\n" % self.number_of_burst_pkts
                alloc_signal = {'onu':self.ONU,'burst':self.number_of_burst_pkts,'pkt':p_list[0]}
            
            self.bbu_store.put(alloc_signal)
                
            #send pkt forward
            for p in p_list:
                self.ONU.ULInput.put(p) # put the packet in ONU port

    def set_split(self,split):
        self.split = split
        self.CpriConfig(self.cpri_option,self.pkt_size,split)
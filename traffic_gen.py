import time
import simpy
import random

import ltecpricalcs as calc

class Packet(object):
    """ This class represents a network packet """
    def __init__(self, time, size,id, cpri_option,split=1,coding=28,src="a", dst="z", interval=0.004):
        self.time = time# creation time
        self.id = id # packet id
        self.src = src #packet source address
        self.dst = dst #packet destination address
        self.size = size
        self.interval = interval

        #BRUNO
        self.split = split
        self.cpri_option = cpri_option # Fixed packet size
        self.coding = coding #same as MCS        
        #pkt_size=(calc.splits_info[self.coding][self.cpri_option][1]['bw'])
        #self.size = calc.size_byte(pkt_size,self.interval)
        #self.prb = calc.CPRI[self.cpri_option]['PRB']
        #BRUNO

    def __repr__(self):
        return "id: {}, src: {}, time: {}, size: {}".\
            format(self.id, self.src, self.time, self.size)

class PacketGenerator(object):
    """This class represents the packet generation process """
    def __init__(self, env, id, ONU, bbu_store ,cpri_option=1,interval=0.004, finish=float("inf")):
        self.id = id # packet id
        self.ONU = ONU
        self.bbu_store = bbu_store
        self.env = env # Simpy Environment
        self.cpri_option = None # Fixed packet size
        self.finish = finish # packe end time
        self.packets_sent = 0 # packet counter
        self.eth_overhead = 0.0
        #self.pkt_size = 306000  #CPRI 1 pkt size
        self.pkt_size = 1250
        self.number_of_burst_pkts = 1
        self.interval = interval #intervalo entres os Ack
        self.CpriConfig(cpri_option)# set CPRI configurations
        self.action = env.process(self.run())  # starts the run() method as a SimPy process

    def CpriConfig(self, cpri_option):

        self.cpri_option = cpri_option
        print("{}:{} - my cpri is {}".format(self.env.now,self.id,self.cpri_option))
        if self.cpri_option == 1:
            self.eth_overhead = 0.00001562
            self.number_of_burst_pkts = 18
        elif self.cpri_option == 2:
            self.eth_overhead = 0.00003004
            self.number_of_burst_pkts = 35
        elif self.cpri_option == 3:
            self.eth_overhead = 0.00005887
            self.number_of_burst_pkts = 70
        elif self.cpri_option == 4:
            self.eth_overhead = 0.00007329
            self.number_of_burst_pkts = 87
        elif self.cpri_option == 5:
            self.eth_overhead = 0.00003004
            self.number_of_burst_pkts = 139
        elif self.cpri_option == 6:
            self.eth_overhead = 0.00005887
            self.number_of_burst_pkts = 173
        elif self.cpri_option == 7:
            self.eth_overhead = 0.00007329
            self.number_of_burst_pkts = 277
        elif self.cpri_option == 8:
            self.eth_overhead = 0.00003004
            self.number_of_burst_pkts = 286
        elif self.cpri_option == 9:
            self.eth_overhead = 0.00005887
            self.number_of_burst_pkts = 343
        elif self.cpri_option == 10:
            self.eth_overhead = 0.00007329
            self.number_of_burst_pkts = 685
        else: #
            self.eth_overhead = 0
            self.number_of_burst_pkts = 1
            self.pkt_size = 9422

    def run(self):
        """The generator function used in simulations.
        """
        while self.env.now < self.finish:
            # wait for next transmission
            yield self.env.timeout(self.interval)

			#creating a list with the pkts that will be sent
            p_list = []
            #npkt = (self.number_of_burst_pkts*4)/10
            for i in range(self.number_of_burst_pkts):
                self.packets_sent += 1
                p = Packet(self.env.now,self.pkt_size ,self.packets_sent, self.cpri_option, src=self.id)
                p_list.append(p)
			#Cpri over Ethernet overhead timeout
            #self.env.timeout(self.eth_overhead)
            #alloc_signal{ONU,pkt,burst}
            alloc_signal = {'onu':self.ONU,'burst':self.number_of_burst_pkts,'pkt':p_list[0]}
            self.bbu_store.put(alloc_signal)
            #send pkt to ONU

            for p in p_list:
                self.ONU.ULInput.put(p) # put the packet in ONU port

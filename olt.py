import time
import simpy
import random
from dba import *
import logging as log
import simtime as l

class OLT(object):
    """Optical line terminal"""
    def __init__(self,env,monitoring,olt_number,odn,ONUs,wavelengths,dba,output=None,output_wavelength=None):
        self.env = env
        self.monitoring = monitoring
        self.olt_number = olt_number
        self.wavelengths = wavelengths
        self.ONUs = ONUs
        self.distance = 0
        self.odn = odn
        self.output = output
        self.output_wavelength = output_wavelength
        self.grant_store = simpy.Store(self.env) # grant communication between processes
        self.ULInput = simpy.Store(self.env)
        self.AllocInput = simpy.Store(self.env)
        self.dba = None
        self.set_dba(dba)

        self.count= 0 

        self.datareceiver = self.env.process(self.OLT_ULDataReceiver()) # process for receiving requests
        self.allocreceiver = self.env.process(self.OLT_AllocationReceiver())
        self.sender = self.env.process(self.OLT_GrantSender()) # process for sending grant

    def set_dba(self,dba):
        #choosing algorithms
        if dba['name'] == "Nakayama_DWBA":
            self.dba = Nakayama_DWBA(self.env,self.monitoring,self.grant_store, self.wavelengths, self.ONUs)
        elif dba['name'] == "M_DWBA" :
            self.dba = M_DWBA(self.env,self.monitoring,self.grant_store, self.wavelengths, self.ONUs)
        elif dba['name'] == "PM_DWBA" :
            self.dba = PM_DWBA(self.env,self.monitoring,self.grant_store, self.wavelengths, self.ONUs)
        else:
            pass
            #self.dba = IPACT(self.env, max_grant_size, self.grant_store)

    def get_dba(self):
        return self.dba            

    def OLT_GrantSender(self):
        """A process which sends a grant message to ONU"""
        while True:
            msg = yield self.grant_store.get() # receive grant from dba
            self.count+=1
            if self.env.now > 1:
                print "!>!> CHEGARAM %d pkts na OLT apos 1 segundo. TOTAL: %d Mbps" % (self.count,((self.count*1500*8))/1000**2)
            #print("{} - grant enviado - {}".format(msg['id'],self.env.now))
            #print msg
            self.odn.activate_wavelength(msg['wavelength'],self.olt_number)
            self.odn.wavelengths[msg['wavelength']]['downstream'].put(msg) # send grant to odn

    def OLT_ULDataReceiver(self):
        while True:
            msg = yield self.ULInput.get()
            #print msg
            self.monitoring.fronthaul_delay(msg.time)
            msg = (self.olt_number,msg,self.output_wavelength)
            self.output.wavelengths[self.output_wavelength]['upstream'].put(msg)


    def OLT_AllocationReceiver(self):
        """A process which receives a request message from the ONUs."""
        while True:
            alloc_signal = yield self.AllocInput.get() #get a request message
            #print("Received Request from ONU {} at {}".format(request['ONU'].oid, self.env.now))
            # send request to DBA
            self.env.process(self.dba.dba(alloc_signal))

import time
import simpy
import random

class OLT(object):
    """Optical line terminal"""
    def __init__(self,env,olt_number,odn,ONUs,wavelengths,dba):
        self.env = env
        self.wavelengths = wavelengths
        self.ONUs = ONUs
        self.odn = odn
        self.grant_store = simpy.Store(self.env) # grant communication between processes
        self.ULInput = simpy.Store(self.env)
        self.AllocInput = simpy.Store(self.env)
        self.set_dba(dba)

        self.datareceiver = self.env.process(self.OLT_ULDataReceiver()) # process for receiving requests
        self.allocreceiver = self.env.process(self.OLT_AllocationReceiver())
        self.sender = self.env.process(self.OLT_GrantSender()) # process for sending grant

    def set_dba(self,dba):
        #choosing algorithms
        if dba['name'] == "pd_dba":
            pass
        else:
            pass
            #self.dba = IPACT(self.env, max_grant_size, self.grant_store)



    def OLT_GrantSender(self):
        """A process which sends a grant message to ONU"""
        while True:
            msg = yield self.grant_store.get() # receive grant from dba
            self.odn.downstream.put(msg) # send grant to odn

    def OLT_ULDataReceiver(self):
        while True:
            msg = yield self.ULInput.get()
            print msg


    def OLT_AllocationReceiver(self):
        """A process which receives a request message from the ONUs."""
        while True:
            alloc_signal = yield self.AllocInput.get() #get a request message
            #print("Received Request from ONU {} at {}".format(request['ONU'].oid, self.env.now))
            # send request to DBA
            self.env.process(self.dba.dba(alloc_signal,self.grant_store))

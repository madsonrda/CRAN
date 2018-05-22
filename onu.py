import time
import simpy
import random


class ONU(object):
    def __init__(self,oid,env,wavelengths,odn):
        self.oid = oid
        self.bandwidth = 10000000000 #10Gbs
        self.env = env
        self.wavelengths = wavelengths
        self.active_GateReceivers = {}
        self.odn= odn
        self.ULInput = simpy.Store(self.env) #Simpy RRH->ONU Uplink input port
        self.buffer = simpy.Store(self.env) #Simpy ONU pkt buffer
        self.buffer_size = 0
        self.ReceiverULDataFromRRH = self.env.process(self.ONU_ReceiverULDataFromRRH())

        for w in wavelengths:
            self.active_GateReceivers[w] = self.env.process(self.ONU_ReceiverGateFromOLT(w))



    def ONU_ReceiverULDataFromRRH(self):
        while True:
            # Grant stage
            pkt = (yield self.ULInput.get() )
            self.buffer_size =  self.buffer_size + pkt.size
            self.buffer.put(pkt)

    def ONU_ReceiverGateFromOLT(self,wavelength):
        while True:
            gate = ( yield self.odn.Get_Gate(self.oid, wavelength) )

            for grant in gate['grant']:
                try:
                    #print("{} : grant time in onu {} = {}".format(self.env.now,self.oid,grant['grant_final_time'] - self.env.now))
                    next_grant = grant['start'] - self.env.now #time until next grant begining
                    #print("next_grant timeout {}".format(next_grant))
                    yield self.env.timeout(next_grant)  #wait for the next grant
                except Exception as e:
                    pass

                    sent_pkt = self.env.process(self.SendUpDataToOLT()) # send pkts during grant time
                    yield sent_pkt # wait grant be used

    def SendUpDataToOLT():
        pkt = yield self.buffer.get()
        self.buffer_size -= pkt.size
        bits = pkt.size * 8
        sending_time = 	bits/float(self.bandwidth)
        yield self.env.timeout(sending_time)

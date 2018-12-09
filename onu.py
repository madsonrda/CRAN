import time
import simpy
import random
import logging as log
import simtime as l

class ONU(object):
    def __init__(self,oid,env,monitoring,wavelengths,distance,odn,fog_odn=None,fog_distance=3):
        self.oid = oid
        self.monitoring = monitoring
        self.bandwidth = 25000000000 #25Gbs
        self.env = env
        self.distance = distance
        self.fog_distance = fog_distance
        #self.wavelengths = wavelengths
        #self.active_GateReceivers = {}
        self.odn= odn
        self.grant_usage = 0
        self.fog_odn = fog_odn
        self.ULInput = simpy.Store(self.env) #Simpy RRH->ONU Uplink input port
        self.buffer = simpy.Store(self.env) #Simpy ONU pkt buffer
        self.buffer_size = 0
        self.ReceiverULDataFromRRH = self.env.process(self.ONU_ReceiverULDataFromRRH())
        self.ReceiverFromOLT = self.env.process(self.ONU_ReceiverFromOLT())
        self.DLInput = simpy.Store(self.env) #Simpy OLT->ONU Downlink input port

        # for w in wavelengths:
        #     self.active_GateReceivers[w] = self.env.process(self.ONU_ReceiverGateFromOLT(w))



    def ONU_ReceiverULDataFromRRH(self):
        while True:
            # Grant stage
            pkt = (yield self.ULInput.get() )
            self.buffer_size =  self.buffer_size + pkt.size
            self.buffer.put(pkt)

    def ONU_ReceiverFromOLT(self):
        while True:
            #print(" {} - waiting gate at {}".format(self.oid,self.env.now))
            msg = ( yield self.DLInput.get() )
            #print(" {} -gate arrived at {}".format(self.oid,self.env.now))
            grant_dict = {}
            for grant in msg['grant']:

                if grant['wavelength'] in grant_dict.keys():

                    grant_dict[grant['wavelength']].append(grant)
                else:
                    grant_dict[grant['wavelength']]= [grant]

            for w in grant_dict:
                self.env.process(self.grant_processing(grant_dict[w]))

    def grant_processing(self,grant_list):
        #print("{}-{}".format(self.oid,grant_list))
        for grant in grant_list:
            try:
                #print("{} : grant time in onu {} = {}".format(self.env.now,self.oid,grant['grant_final_time'] - self.env.now))
                next_grant = grant['start'] - self.env.now #time until next grant begining
                #print next_grant
                #print("next_grant timeout {}".format(next_grant))
                yield self.env.timeout(next_grant)  #wait for the next grant
            except Exception as e:
                print self.env.now
                print( "{} - tempo negativo".format(self.oid))
                print grant['start']
                print("next_grant timeout {}".format(next_grant))
                pass
            #print(" {} -grant start at {}".format(self.oid,self.env.now))
            #print("{}-{}".format(self.oid,self.env.now))
            #print("{} - grant end {}".format(self.oid,grant['end']))
            while self.env.now < grant['end']:
                sent_pkt = self.env.process(self.SendUpDataToOLT(grant['wavelength'])) # send pkts during grant time
                yield sent_pkt # wait grant be used
                if self.buffer_size <= 0:
                    break
            #print("{} - time left {} ".format(self.oid,(grant['end'] - self.env.now)))
            #print("{:.10f}".format(grant['end'] - grant['start']))
            #print self.grant_usage
            self.monitoring.grant_usage(grant['start'],grant['end'],self.grant_usage)
            self.grant_usage = 0

    def SendUpDataToOLT(self,wavelength):
        pkt = yield self.buffer.get()
        self.buffer_size -= pkt.size

        bits = pkt.size * 8
        sending_time = 	bits/float(self.bandwidth)
        self.grant_usage += sending_time
        yield self.env.timeout(sending_time)
        msg = (self.oid,pkt,wavelength)
        #print("{} - buffer {} at {}".format(self.oid,self.buffer_size,self.env.now))
        self.odn.wavelengths[wavelength]['upstream'].put(msg)
        #self.fog_odn.wavelengths[wavelength]['upstream'].put(msg)

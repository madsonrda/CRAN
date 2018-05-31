import time
import simpy
import random


class ONU(object):
    def __init__(self,oid,env,wavelengths,distance,odn):
        self.oid = oid
        self.bandwidth = 10000000000 #10Gbs
        self.env = env
        self.distance = distance
        #self.wavelengths = wavelengths
        #self.active_GateReceivers = {}
        self.odn= odn
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
            print(" {} - waiting grant at {}".format(self.oid,self.env.now))
            msg = ( yield self.DLInput.get() )
            print(" {} -grant arrived at {}".format(self.oid,self.env.now))

            for grant in msg['grant']:
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
                print(" {} -grant start at {}".format(self.oid,self.env.now))
                #print("{}-{}".format(self.oid,self.env.now))
                print("{} - grant end {}".format(self.oid,grant['end']))
                while self.env.now <= grant['end']:
                    sent_pkt = self.env.process(self.SendUpDataToOLT(grant['wavelength'])) # send pkts during grant time
                    yield sent_pkt # wait grant be used
                    if self.buffer_size <= 0:
                        break
                print("{} - time left {} ".format(self.oid,(grant['end'] - self.env.now)))

    def SendUpDataToOLT(self,wavelength):
        pkt = yield self.buffer.get()
        self.buffer_size -= pkt.size

        bits = pkt.size * 8
        sending_time = 	bits/float(self.bandwidth)
        yield self.env.timeout(sending_time)
        msg = (self.oid,pkt,wavelength)
        print("{} - buffer {} at {}".format(self.oid,self.buffer_size,self.env.now))
        self.odn.wavelengths[wavelength]['upstream'].put(msg)

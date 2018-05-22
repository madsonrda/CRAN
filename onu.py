import time
import simpy
import random


class ONU(object):
    def __init__(self,oid,env,lambdas,odn):
        self.env = env
        self.odn= odn
        self.ULInput = simpy.Store(self.env) #Simpy RRH->ONU Uplink input port
        self.buffer = simpy.Store(self.env) #Simpy ONU pkt buffer
        self.buffer_size = 0
        self.ReceiverFromRRH = self.env.process(self.ONU_ReceiverFromRRH(odn))


    def ONU_ReceiverFromRRH(self):
        while True:
            # Grant stage
            pkt = (yield self.ULInput.get() )
            self.buffer_size =  self.buffer_size + pkt.size
            self.buffer.put(pkt)




        #
        # self.grant_report_store = simpy.Store(self.env) #Simpy Stores grant usage report
        # self.request_container = simpy.Container(env, init=2, capacity=2)
        # self.grant_report = []
        # self.distance = distance #fiber distance
        # self.oid = oid #ONU indentifier
        # self.delay = self.distance/float(200000) # fiber propagation delay
        # self.excess = 0 #difference between the size of the request and the grant
        # self.newArrived = 0
        # self.last_req_buffer = 0
        # self.request_counter = 0
        # self.pg = packet_gen(self.env, "bbmp", self, **pg_param) #creates the packet generator
        # if qlimit == 0:# checks if the queue has a size limit
        #     queue_limit = None
        # else:
        #     queue_limit = qlimit
        # self.port = ONUPort(self.env, self, qlimit=queue_limit)#create ONU PORT
        # self.pg.out = self.port #forward packet generator output to ONU port
        # if not (DBA_ALGORITHM == "mdba" or DBA_ALGORITHM == "mpd_dba"):
        #     self.sender = self.env.process(self.ONU_sender(odn))
        # self.receiver = self.env.process(self.ONU_receiver(odn))
        # self.bucket = bucket #Bucket size
        # self.lamb = lamb # wavelength lambda

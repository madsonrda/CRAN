class DBA(object):
    """DBA Parent class, heritated by every kind of DBA"""
    def __init__(self,env,grant_store):
        self.env = env
        self.grant_store = grant_store
        self.guard_interval = 0.000001

class Nakayama_DWBA(DBA):
    def __init(self,env,grant_store,wavelengths):
        DBA.__init__(self,env,grant_store)
        self.delay_limit
        self.num_slots


class IPACT(DBA):
    def __init__(self,env,max_grant_size,grant_store):
        DBA.__init__(self,env,max_grant_size,grant_store)
        self.counter = simpy.Resource(self.env, capacity=1)#create a queue of requests to DBA


    def dba(self,ONU,buffer_size):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            time_stamp = self.env.now # timestamp dba starts processing the request
            delay = ONU.delay # oneway delay

            # check if max grant size is enabled
            if self.max_grant_size > 0 and buffer_size > self.max_grant_size:
                buffer_size = self.max_grant_size
            bits = buffer_size * 8
            sending_time = 	bits/float(10000000000) #buffer transmission time
            grant_time = delay + sending_time
            grant_final_time = self.env.now + grant_time # timestamp for grant end
            counter = Grant_ONU_counter[ONU.oid] # Grant message counter per ONU
            # write grant log
            grant_time_file.write( "{},{},{},{},{},{},{},{}\n".format(MAC_TABLE['olt'], MAC_TABLE[ONU.oid],"02", time_stamp,counter, ONU.oid,self.env.now,grant_final_time) )
            # construct grant message
            grant = {'ONU':ONU,'grant_size': buffer_size, 'grant_start_time': self.env.now, 'grant_final_time': grant_final_time, 'prediction': None}
            self.grant_store.put(grant) # send grant to OLT
            Grant_ONU_counter[ONU.oid] += 1

            # timeout until the end of grant to then get next grant request
            yield self.env.timeout(delay+grant_time + self.guard_interval)

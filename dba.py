import time
import simpy
import random
import math
import sys

class DBA(object):
    """DBA Parent class, heritated by every kind of DBA"""
    def __init__(self,env,grant_store):
        self.env = env
        self.grant_store = grant_store
        self.guard_interval = 0.000001


class Nakayama_DWBA(DBA):
    def __init(self,env,grant_store,wavelengths,ONUs):
        DBA.__init__(self,env,grant_store)
        self.ONUs = ONUs
        self.delay_limit = 0.000250
        self.wavelengths = wavelengths
        self.bandwidth = 10000000000
        self.active_wavelenghts = []
        self.time_limit = self.delay_limit
        self.granting_start = 0
        self.lightspeed = float(200000)
        self.num_slots = 0
        self.alloc_list = []
        self.counter = simpy.Resource(self.env, capacity=1)#create a queue of requests to DBA
        self.dwba_proc = self.env.process(self.dwba())
        self.AllocGathering = self.env.event()
        self.alloc_counter = 0

    def dwba(self):
        #alloc_signal{ONU,pkt,burst}
        while True:
            yield self.AllocGathering
            self.alloc_list = sorted(self.alloc_list, key=lambda x: x['onu'].distance, reverse=True)

            self.granting_start = self.env.now + (self.alloc_list[0]['onu'].distance/self.lightspeed)
            self.time_limit = self.env.now + self.delay_limit

            max_alloc = max(self.alloc_list, key=lambda x : x['busrt'])
            bits = (max_alloc['pkt'].size * max_alloc['burst']) * 8
            slot_time = bits/float(self.bandwidth)

            self.num_slots = math.floor((self.time_limit - self.granting_start)/float(slot_time))
            if self.num_slots < 1:
                print "NUM SLOTS leq 1"
            w = 0
            self.active_wavelenghts.append(self.wavelengths[w])
            slot = 1
            start = self.granting_start
            Gate = []
            for alloc in self.alloc_list:
                end = start + slot_time
                grant = {'start': start, 'end': end, 'wavelength': self.wavelengths[w]}
                gate = {'name': 'gate', 'onu': alloc['onu'].oid, 'wavelength': self.wavelengths[w], 'grant': [grant]}
                Gate.append(gate)

                slot +=1
                start = end
                if slot > self.num_slots:
                    w +=1
                    try:
                        self.active_wavelenghts.append(self.wavelengths[w])
                        slot = 1
                        start = self.granting_start
                    except Exception as e:
                        print e
                         sys.exit(0)

            for gate in Gate:
                self.grant_store.put(gate)




    def dba(self,alloc_signal):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            self.alloc_counter += 1
            self.alloc_list.append(alloc_signal)

            if self.alloc_counter == len(self.ONUs):
                self.alloc_counter = 0
                self.active_wavelenghts = []
                self.AllocGathering.succeed()
                self.AllocGathering = self.env.event()

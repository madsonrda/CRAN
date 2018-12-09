import time
import simpy
import random
import math
import sys
import logging as log
import simtime as l

class DBA(object):
    """DBA Parent class, heritated by every kind of DBA"""
    def __init__(self,env,monitoring,grant_store,bandwidth,delay_limit):
        self.env = env
        self.grant_store = grant_store
        self.guard_interval = 0.000001
        self.monitoring = monitoring
        self.bandwidth = bandwidth
        self.delay_limit = delay_limit
        self.time_limit = self.delay_limit
        self.lightspeed = float(200000)


class Nakayama_DWBA(DBA):
    #problema: ultrapassa limite de delay se o tamanho do slot ou delay prop for grande
    def __init__(self,env,monitoring,grant_store,wavelengths,ONUs,bandwidth=25000000000,delay_limit=0.000250):
        DBA.__init__(self,env,monitoring,grant_store,bandwidth,delay_limit)
        self.ONUs = ONUs
        self.wavelengths = wavelengths
        #self.bandwidth = 10000000000
        self.active_wavelengths = []
        self.granting_start = 0
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
            #print self.env.now
            self.alloc_list = sorted(self.alloc_list, key=lambda x: x['onu'].distance, reverse=True)

            self.granting_start = self.env.now + (self.alloc_list[0]['onu'].distance/self.lightspeed)
            print self.env.now
            print "------------------------------------------"
            print self.granting_start
            self.time_limit = self.env.now + self.delay_limit
            print("time_limit = {}".format(self.time_limit))

            max_alloc = max(self.alloc_list, key=lambda x : x['burst'])
            bits = (max_alloc['pkt'].size * max_alloc['burst']) * 8
            #print("Bits={:.10f".format(bits))
            print "Bits= %f" % bits
            slot_time = bits/float(self.bandwidth)
            print("slot_time={:.10f}".format(slot_time))

            self.num_slots = math.floor((self.time_limit - self.granting_start)/float(slot_time))
            if self.num_slots < 1:
                print "NUM SLOTS leq 1"
            print("num_slots={}".format(self.num_slots))
            w = 0
            self.active_wavelengths.append(self.wavelengths[w])
            slot = 1
            start = self.granting_start
            Gate = []
            #print("tam_alloclist={}".format(len(self.alloc_list)))
            for alloc in self.alloc_list:
                end = start + slot_time
                grant = {'start': start, 'end': end, 'wavelength': self.wavelengths[w]}
                gate = {'name': 'gate', 'id': alloc['onu'].oid, 'wavelength': self.wavelengths[w], 'grant': [grant]}
                Gate.append(gate)

                slot +=1
                start = end
                if slot > self.num_slots:
                    w +=1
                    try:
                        self.active_wavelengths.append(self.wavelengths[w])
                        slot = 1
                        start = self.granting_start
                    except Exception as e:
                        print w
                        print("ERROR {}".format(e))
                        print self.env.now
                        sys.exit(0)

            self.monitoring.fronthaul_active_wavelengths(len(self.active_wavelengths))
            for gate in Gate:
                self.grant_store.put(gate)
            self.alloc_list = []




    def dba(self,alloc_signal):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            self.alloc_counter += 1
            self.alloc_list.append(alloc_signal)

            if self.alloc_counter == len(self.ONUs):
                self.alloc_counter = 0
                self.active_wavelengths = []
                self.AllocGathering.succeed()
                self.AllocGathering = self.env.event()

class M_DWBA(DBA):
    def __init__(self,env,monitoring,grant_store,wavelengths,ONUs,bandwidth=25000000000,delay_limit=1.001250):
        DBA.__init__(self,env,monitoring,grant_store,bandwidth,delay_limit)
        self.ONUs = ONUs
        self.wavelengths = wavelengths
        self.active_wavelengths = []
        self.granting_start = 0
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
            #print self.env.now
            self.alloc_list = sorted(self.alloc_list, key=lambda x: x['onu'].distance, reverse=True)

            self.granting_start = self.env.now + (self.alloc_list[0]['onu'].distance/self.lightspeed)
            print self.env.now
            print "------------------------------------------"
            print self.granting_start
            self.time_limit = self.env.now + self.delay_limit
            print("time_limit = {}".format(self.time_limit))

            #max_alloc = max(self.alloc_list, key=lambda x : x['burst'])

            print self.alloc_list[0]['pkt']
            bits = self.alloc_list[0]['pkt'].size  * 8
            print "Bits= %f" % bits
            slot_time = bits/float(self.bandwidth)
            print("slot_time={:.10f}".format(slot_time))

            self.num_slots = math.floor((self.time_limit - self.granting_start)/float(slot_time))
            if self.num_slots < 1:
                #print "Time limit - % (self.time_limit - self.granting_start)
                print "NUM SLOTS leq 1"
            print("num_slots={}".format(self.num_slots))
            w = 0
            self.active_wavelengths.append(self.wavelengths[w])
            slot = 1
            start = self.granting_start
            Gate = []
            #print("tam_alloclist={}".format(len(self.alloc_list)))
            for alloc in self.alloc_list:
                gate = {'name': 'gate', 'id': alloc['onu'].oid, 'wavelength': self.wavelengths[w], 'grant': []}
                for burst in range(alloc['burst']):
                    end = start + slot_time
                    grant = {'start': start, 'end': end, 'wavelength': self.wavelengths[w]}
                    gate['grant'].append(grant)
                    slot +=1
                    start = end
                    if slot > self.num_slots:
                        w +=1
                        try:
                            self.active_wavelengths.append(self.wavelengths[w])
                            slot = 1
                            start = self.granting_start
                        except Exception as e:

                            print "Exception"
                            print "NUM_SLOTS: %d" % self.num_slots
                            print "SLOT: %d" % slot
                            print w
                            print self.wavelengths
                            print("ERROR {}".format(e))
                            print "TIME: %f" % self.env.now
                            sys.exit(0)
                Gate.append(gate)

            self.monitoring.fronthaul_active_wavelengths(len(self.active_wavelengths))
            for gate in Gate:
                self.grant_store.put(gate)
            self.alloc_list = []




    def dba(self,alloc_signal):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            self.alloc_counter += 1
            self.alloc_list.append(alloc_signal)

            if self.alloc_counter == len(self.ONUs):
                self.alloc_counter = 0
                self.active_wavelengths = []
                self.AllocGathering.succeed()
                self.AllocGathering = self.env.event()

class SM_DBA(DBA):
    def __init__(self,env,monitoring,grant_store,wavelengths,ONUs,bandwidth=25000000000,delay_limit=1.001250):
        DBA.__init__(self,env,monitoring,grant_store,bandwidth,delay_limit)
        self.ONUs = ONUs
        self.wavelengths = wavelengths
        self.active_wavelengths = []
        self.granting_start = 0
        self.num_slots = 0
        self.alloc_list1 = []
        self.alloc_list2 = []
        self.alloc_list3 = []
        self.alloc_list4 = []
        self.counter = simpy.Resource(self.env, capacity=1)#create a queue of requests to DBA
        self.dwba_proc = self.env.process(self.dwba())
        self.AllocGathering = self.env.event()
        self.alloc_counter = 0

    def dwba(self):
        #alloc_signal{ONU,pkt,burst}
        while True:
            yield self.AllocGathering
            #print self.env.now
            self.alloc_list = sorted(self.alloc_list, key=lambda x: x['onu'].distance, reverse=True)

            self.granting_start = self.env.now + (self.alloc_list[0]['onu'].distance/self.lightspeed)
            print self.env.now
            print "------------------------------------------"
            print self.granting_start
            self.time_limit = self.env.now + self.delay_limit
            print("time_limit = {}".format(self.time_limit))

            #max_alloc = max(self.alloc_list, key=lambda x : x['burst'])

            print self.alloc_list[0]['pkt']
            bits = self.alloc_list[0]['pkt'].size  * 8
            print "Bits= %f" % bits
            slot_time = bits/float(self.bandwidth)
            print("slot_time={:.10f}".format(slot_time))

            self.num_slots = math.floor((self.time_limit - self.granting_start)/float(slot_time))
            if self.num_slots < 1:
                #print "Time limit - % (self.time_limit - self.granting_start)
                print "NUM SLOTS leq 1"
            print("num_slots={}".format(self.num_slots))
            w = 0
            self.active_wavelengths.append(self.wavelengths[w])
            slot = 1
            start = self.granting_start
            Gate = []
            #print("tam_alloclist={}".format(len(self.alloc_list)))
            for alloc in self.alloc_list:
                gate = {'name': 'gate', 'id': alloc['onu'].oid, 'wavelength': self.wavelengths[w], 'grant': []}
                for burst in range(alloc['burst']):
                    end = start + slot_time
                    grant = {'start': start, 'end': end, 'wavelength': self.wavelengths[w]}
                    gate['grant'].append(grant)
                    slot +=1
                    start = end
                    if slot > self.num_slots:
                        w +=1
                        try:
                            self.active_wavelengths.append(self.wavelengths[w])
                            slot = 1
                            start = self.granting_start
                        except Exception as e:

                            print "Exception"
                            print "NUM_SLOTS: %d" % self.num_slots
                            print "SLOT: %d" % slot
                            print w
                            print self.wavelengths
                            print("ERROR {}".format(e))
                            print "TIME: %f" % self.env.now
                            sys.exit(0)
                Gate.append(gate)

            self.monitoring.fronthaul_active_wavelengths(len(self.active_wavelengths))
            for gate in Gate:
                self.grant_store.put(gate)
            self.alloc_list = []




    def dba(self,alloc_signal):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            self.alloc_counter += 1
            if alloc_signal['pkt'].qos = 1:
                self.alloc_list1.append(alloc_signal)
            elif alloc_signal['pkt'].qos = 2:
                self.alloc_list2.append(alloc_signal)
            elif alloc_signal['pkt'].qos = 3:
                self.alloc_list3.append(alloc_signal)
            elif alloc_signal['pkt'].qos = 4:
                self.alloc_list4.append(alloc_signal)

            if self.alloc_counter == len(self.ONUs):
                self.alloc_counter = 0
                self.active_wavelengths = []
                self.AllocGathering.succeed()
                self.AllocGathering = self.env.event()

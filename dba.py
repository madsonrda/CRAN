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
        self.cycle = 0

    def dwba(self):
        #alloc_signal{ONU,pkt,burst}
        while True:
            yield self.AllocGathering
            #print self.env.now
            if len(self.alloc_list1) > 0:
                self.alloc_list1 = sorted(self.alloc_list1, key=lambda x: x['onu'].distance, reverse=True)
            if len(self.alloc_list2) > 0:
                self.alloc_list2 = sorted(self.alloc_list2, key=lambda x: x['onu'].distance, reverse=True)
            if len(self.alloc_list3) > 0:
                self.alloc_list3 = sorted(self.alloc_list3, key=lambda x: x['onu'].distance, reverse=True)
            if len(self.alloc_list4) > 0:
                self.alloc_list4 = sorted(self.alloc_list4, key=lambda x: x['onu'].distance, reverse=True)

            propagation_delay = (self.alloc_list[0]['onu'].distance/self.lightspeed)
            self.granting_start = self.env.now + propagation_delay
            #print self.env.now
            #print "------------------------------------------"
            #print self.granting_start
            self.time_limit = self.env.now + self.delay_limit
            #print("time_limit = {}".format(self.time_limit))

            #max_alloc = max(self.alloc_list, key=lambda x : x['burst'])

            #print self.alloc_list[0]['pkt']
            bits = self.alloc_list[0]['pkt'].size  * 8
            #print "Bits= %f" % bits
            slot_time = bits/float(self.bandwidth)
            #print("slot_time={:.10f}".format(slot_time))


            self.num_slots = math.floor((self.time_limit - self.granting_start - propagation_delay)/float(slot_time))
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
            self.cycle +=1
            self.monitoring.cycle = self.cycle




    def dba(self,alloc_signal):
        with self.counter.request() as my_turn:
            """ DBA only process one request at a time """
            yield my_turn
            self.alloc_counter += 1
            if alloc_signal['pkt'].qos == 1:
                self.alloc_list1.append(alloc_signal)
            elif alloc_signal['pkt'].qos == 2:
                self.alloc_list2.append(alloc_signal)
            elif alloc_signal['pkt'].qos == 3:
                self.alloc_list3.append(alloc_signal)
            elif alloc_signal['pkt'].qos == 4:
                self.alloc_list4.append(alloc_signal)

            if self.alloc_counter == len(self.ONUs):
                self.alloc_counter = 0
                self.active_wavelengths = []
                self.AllocGathering.succeed()
                self.AllocGathering = self.env.event()

class slot_table(object):
    def __init__(self,n_slots,extra_slots,start_extra, start_grant, slot_time,wavelengths):
        self.n_slots = n_slots
        self.extra_slots = extra_slots
        self.start_extra = start_extra
        self.start_grant  = start_grant
        self.slot_time = slot_time
        self.wavelengths = wavelengths
        self.table = None
        self.w = 0
        self.slot = 0
        self.construct()

    def construct(self):

        self.table =  [[{}]*(self.extra_slots + self.n_slots)]*len(self.wavelengths)
        #construct extra area
        print "----"*10
        print self.start_extra
        print "----"*10
        for i in range(len(self.wavelengths)):
            next_time = self.start_extra
            for j in range(self.extra_slots):
                self.table[i][j] = {"onu": None, "start": next_time, "end": next_time + self.slot_time}
                next_time = next_time + self.slot_time
        for i in range(len(self.wavelengths)):
            next_time = self.start_grant
            for j in range(self.extra_slots,self.extra_slots + self.n_slots):
                self.table[i][j] = {"onu": None, "start": next_time, "end": next_time + self.slot_time}
                next_time = next_time + self.slot_time
    def allocate(self,onu):
        if self.w == len(self.wavelengths):
            print "acabou w"
            sys.exit(0)
        if self.slot == self.extra_slots + self.n_slots:
            self.w += 1
            self.slot = self.extra_slots
        #print self.table[self.w][self.slot]
        self.table[self.w][self.slot]["onu"] = onu
        slot = self.slot
        self.slot += 1
        return {'start': self.table[self.w][slot]["start"],
            'end': self.table[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}

    def allocate_pred(self,onu):
        if self.w == len(self.wavelengths):
            print "acabou w"
            sys.exit(0)
        if self.slot == self.extra_slots + self.n_slots:
            self.w += 1
            self.slot = 0
        #print self.table[self.w][self.slot]
        self.table[self.w][self.slot]["onu"] = onu
        slot = self.slot
        self.slot += 1
        print("alloc pred next slot is {}, extra is {}".format(self.slot,self.extra_slots))
        return {'start': self.table[self.w][slot]["start"],
            'end': self.table[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}





class PM_DWBA(M_DWBA):
    def __init__(self,env,monitoring,grant_store,wavelengths,ONUs):
        M_DWBA.__init__(self,env,monitoring,grant_store,wavelengths,ONUs)
        # self.window = 5    # past observations window size
        # self.predict = 10 # number of predictions
        self.grant_history = range(len(self.ONUs)) #grant history per ONU (training set)
        # self.predictions_array = []
        for i in range(len(self.ONUs)):
        #     # training unit
            self.grant_history[i] = {'cycle': [],  'slots': []}
        self.slot_time = self.calc_slot_time()
        self.num_slots = int(math.floor((self.time_limit - 0.0002)/float(self.slot_time)))
        if self.num_slots < 1:
            print "NUM SLOTS leq 1"
        self.tot_slots = int(math.floor((self.time_limit - 0.0001)/float(self.slot_time)))
        self.extra_slots = self.tot_slots - self.num_slots
        self.cycle_tables = {}
        self.cycle = 0
        self.predictions_list = []
        for i in range(len(self.ONUs)):
            self.predictions_list.append([])


    def calc_slot_time(self):

        bits = 1250  * 8
        #bits = 9422  * 8
        slot_time = bits/float(self.bandwidth)
        return slot_time

    def predictor(self,onu):
        if len( self.grant_history[onu]['cycle']) > 5:
            #return [req_slots] * 20
            self.grant_history[onu]['cycle'] = self.grant_history[onu]['cycle'][-5:]
            self.grant_history[onu]['slots'] = self.grant_history[onu]['slots'][-5:]
            df_tmp = pd.DataFrame(self.grant_history[onu]) # temp dataframe w/ past grants
            X_pred = np.arange(self.grant_history[onu]['cycle'][-1] +1,
                self.grant_history[onu]['cycle'][-1] + 1 + 20).reshape(-1,1)

            # model fitting
            model = linear_model.LinearRegression()
            model.fit( np.array( df_tmp['cycle'] ).reshape(-1,1) , df_tmp['slots'] )
            pred = model.predict(X_pred) # predicting start and end
            return map(int,pred)

        else :
            return []


    def dwba(self):
        while True:
            yield self.AllocGathering
            print("{} starts cycle {}".format(self.env.now,self.cycle))
            self.granting_start = self.env.now + (self.alloc_list[0]['onu'].distance/self.lightspeed)

            if not ( self.cycle in self.cycle_tables.keys() ):
                self.cycle_tables[self.cycle] = {"table": slot_table(self.num_slots,
                    self.extra_slots,self.env.now, self.granting_start, self.slot_time,self.wavelengths)}
                self.cycle_tables[self.cycle]["table"].slot = self.extra_slots
                print "entrei aqui"
            elif self.cycle_tables[self.cycle]["table"].slot < self.extra_slots:
                print "XXXX"*10
                print "kk   "
                print "XXXX"*10
                self.cycle_tables[self.cycle]["table"].slot = self.extra_slots





            Gate = []
            #pred_increment = 0
            for alloc in self.alloc_list:
                self.monitoring.required_slots(self.cycle,alloc['burst'],alloc['onu'].oid)
                self.grant_history[alloc['onu'].oid]['cycle'].append(self.cycle)
                self.grant_history[alloc['onu'].oid]['slots'].append(alloc['burst'])
                pred_grants = []
                print("{} - onu {} preds {}".format(self.env.now,alloc['onu'].oid,self.predictions_list[alloc['onu'].oid]))
                if len(self.predictions_list[alloc['onu'].oid]) == 0:
                    pred = self.predictor(alloc['onu'].oid)
                    if len(pred) > 0:
                        start_next_c = self.env.now + 0.004

                        self.predictions_list[alloc['onu'].oid] += pred
                        print("{} - onu {} preds {}".format(self.env.now,alloc['onu'].oid,self.predictions_list))
                        for i,p in enumerate(pred):
                            if not ( self.cycle +( i+1) in self.cycle_tables.keys() ):
                                granting_start_next_c = start_next_c + (self.alloc_list[0]['onu'].distance/self.lightspeed)
                                print("{} - create cycle {} table by pred, onu {}".format(self.env.now,self.cycle +( i+1),alloc['onu'].oid))
                                self.cycle_tables[self.cycle +( i+1)] = {"table": slot_table(self.num_slots,
                                    self.extra_slots,start_next_c, granting_start_next_c, self.slot_time,self.wavelengths)}
                                start_next_c += 0.004
                            for burst in range(p):
                                grant = self.cycle_tables[self.cycle +( i+1)]["table"].allocate_pred(alloc['onu'].oid)
                                pred_grants.append(grant)
                    gate = {'name': 'gate', 'onu': alloc['onu'].oid, 'wavelength': self.wavelengths[0], 'grant': []}

                    print("next free slot is {}".format(self.cycle_tables[self.cycle]["table"].slot))
                    for burst in range(alloc['burst']):
                        grant = self.cycle_tables[self.cycle]["table"].allocate(alloc['onu'].oid)
                        gate['grant'].append(grant)
                    gate['grant'] += pred_grants
                    Gate.append(gate)
                else:
                    if alloc['burst'] > self.predictions_list[alloc['onu'].oid][0]:
                        print "is greater"
                        pred_increment = alloc['burst'] - self.predictions_list[alloc['onu'].oid][0]
                        gate = {'name': 'gate', 'onu': alloc['onu'].oid, 'wavelength': self.wavelengths[0], 'grant': []}
                        for burst in range(pred_increment):

                            grant = self.cycle_tables[self.cycle]["table"].allocate(alloc['onu'].oid)
                            #grant = {'start': start, 'end': end, 'wavelength': self.wavelengths[w]}
                            gate['grant'].append(grant)
                        Gate.append(gate)
                        self.predictions_list[alloc['onu'].oid].pop(0)
                    elif alloc['burst'] < self.predictions_list[alloc['onu'].oid][0]:
                        print "is less"
                        self.predictions_list[alloc['onu'].oid].pop(0)
                    else:
                        print "is equal"
                        print("{} - onu {} - cycle {}".format(self.env.now,alloc['onu'].oid,self.cycle))
                        self.predictions_list[alloc['onu'].oid].pop(0)

            print "####" *10
            print self.predictions_list
            print "####" *10



            for w in range(self.cycle_tables[self.cycle]["table"].w):
                self.active_wavelenghts.append(self.wavelengths[w])

            self.monitoring.fronthaul_active_wavelengths(len(self.active_wavelenghts))
            for gate in Gate:
                self.grant_store.put(gate)
            self.alloc_list = []
            self.cycle +=1
            self.monitoring.cycle = self.cycle

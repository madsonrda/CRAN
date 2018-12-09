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


class slot_table(object):
    def __init__(self,n_slots,g_slots,e_slots, start_g,start_n, slot_time, wavelengths):
        self.n_slots = n_slots
        self.g_slots = g_slots
        self.e_slots = e_slots
        self.start_g = start_g
        self.start_n = start_n
        self.slot_time = slot_time
        self.wavelengths = wavelengths
        self.table_g = None
        self.table_n = None
        self.table_e = None
        self.w = 0
        self.slotg = 0
        self.slotn = 0
        self.slote = 0
        self.next_time = 0
        self.construct(self.table_g,self.g_slots,self.start_g)
        self.construct(self.table_n,self.n_slots,self.start_n)
        self.construct(self.table_e,self.e_slots,self.next_time)

    def construct(self,table,num_slots,start):

        table =  [[{}]*(num_slots)]*len(self.wavelengths)
        #construct extra area
        print "----"*10
        print start
        print "----"*10
        for i in range(len(self.wavelengths)):
            self.next_time = start
            for j in range(num_slots):
                table[i][j] = {"onu": None, "start": self.next_time, "end": self.next_time + self.slot_time}
                self.next_time = self.next_time + self.slot_time

    def update_w(self):
        self.w +1
        if self.w == len(self.wavelengths):
            print "acabou slots w"
            self.w -=1

    def allocate_g(self,onu):
        # if self.w == len(self.wavelengths):
        #     print "acabou slots w"
        #     sys.exit(0)
        if self.slotg == self.g_slots:
            return {}
        #print self.table[self.w][self.slot]
        self.table_g[self.w][self.slotg]["onu"] = onu
        slot = self.slotg
        self.slotg += 1
        return {'start': self.table_g[self.w][slot]["start"],
            'end': self.table_g[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}

    def check_avail_n(self):
        slot = self.slotn +1
        if slot == self.n_slots:
            return False
        else:
            return True

    def check_avail_e(self):
        slot = self.slote +1
        if slot == self.e_slots:
            return False
        else:
            return True

    def check_avail_g(self):
        slot = self.slotg +1
        if slot == self.g_slots:
            return False
        else:
            return True

    def allocate_n(self,onu):
        # if self.w == len(self.wavelengths):
        #     print "acabou slots w"
        #     sys.exit(0)
        if self.slotn == self.n_slots:
            return {}
        #print self.table[self.w][self.slot]
        self.table_n[self.w][self.slotn]["onu"] = onu
        slot = self.slotn
        self.slotn += 1
        return {'start': self.table_n[self.w][slot]["start"],
            'end': self.table_n[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}

    def allocate_e(self,onu):
        # if self.w == len(self.wavelengths):
        #     print "acabou slots w"
        #     sys.exit(0)
        if self.slote == self.e_slots:
            return {}
        #print self.table[self.w][self.slot]
        self.table_e[self.w][self.slote]["onu"] = onu
        slot = self.slote
        self.slote += 1
        return {'start': self.table_e[self.w][slot]["start"],
            'end': self.table_e[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}

    # def allocate_pred(self,onu):
    #     if self.w == len(self.wavelengths):
    #         print "acabou w"
    #         sys.exit(0)
    #     if self.slot == self.extra_slots + self.n_slots:
    #         self.w += 1
    #         self.slot = 0
    #     #print self.table[self.w][self.slot]
    #     self.table[self.w][self.slot]["onu"] = onu
    #     slot = self.slot
    #     self.slot += 1
    #     print("alloc pred next slot is {}, extra is {}".format(self.slot,self.extra_slots))
    #     return {'start': self.table[self.w][slot]["start"],
    #         'end': self.table[self.w][slot]["end"], 'wavelength': self.wavelengths[self.w]}





class PM_DWBA(M_DWBA):
    def __init__(self,env,monitoring,grant_store,wavelengths,ONUs,bandwidth=25000000000,delay_limit=1.001250,distance=20):
        DBA.__init__(self,env,monitoring,grant_store,bandwidth,delay_limit)
        self.ONUs = ONUs
        self.distance= distance
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

        # self.window = 5    # past observations window size
        # self.predict = 10 # number of predictions
        self.grant_history = range(len(self.ONUs)) #grant history per ONU (training set)
        self.GATE = range(len(self.ONUs))
        # self.predictions_array = []
        self.cycle_interval = 0.004
        self.propagation_delay = (distance/self.lightspeed)
        for i in range(len(self.ONUs)):
        #     # training unit
            self.grant_history[i] = {'cycle': [],  'slots': []}
            self.GATE[i] = {'name': 'gate', 'onu': i, 'wavelength': self.wavelengths[0], 'grant': []}
        self.slot_time = self.calc_slot_time()
        self.normal_slots = int(math.floor((self.time_limit - 2*self.propagation_delay)/float(self.slot_time)))
        if self.normal_slots < 1:
            print "NUM SLOTS leq 1"
        self.tot_slots = int(math.floor((self.time_limit - self.propagation_delay)/float(self.slot_time)))
        self.grant_slots = self.tot_slots - self.normal_slots
        self.tot_slots = int(math.floor(( self.cycle_interval - (self.time_limit + 2*self.propagation_delay))/float(self.slot_time)))
        self.higher_delay_slots = self.tot_slots - self.normal_slots - self.grant_slots
        if self.higher_delay_slots < 1:
            print "Higher SLOTS leq 1"
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

    def check_pred(self,alloc_list):
        pq = {}
        q = []
        if len( self.alloc_list) > 0:
            for alloc in self.alloc_list:
                self.monitoring.required_slots(self.cycle,alloc['burst'],alloc['onu'].oid)
                self.grant_history[alloc['onu'].oid]['cycle'].append(self.cycle)
                self.grant_history[alloc['onu'].oid]['slots'].append(alloc['burst'])
                print("{} - onu {} preds {}".format(self.env.now,alloc['onu'].oid,self.predictions_list[alloc['onu'].oid]))
                if len(self.predictions_list[alloc['onu'].oid]) == 0:
                    pred = self.predictor(alloc['onu'].oid)
                    if len(pred) > 0:
                        self.predictions_list[alloc['onu'].oid] += pred
                        print("{} - onu {} preds {}".format(self.env.now,alloc['onu'].oid,self.predictions_list))
                        for i,p in enumerate(pred):
                            if not ( self.cycle +( i+1) in pq1.keys() ):
                                pq[self.cycle +( i+1)] = []
                            for burst in range(p):
                                pq[self.cycle +( i+1)].append(alloc['onu'].oid)
                    for burst in range(alloc['burst']):
                        q.append(alloc['onu'].oid)
                else:
                    if alloc['burst'] > self.predictions_list[alloc['onu'].oid][0]:
                        print "is greater"
                        pred_increment = alloc['burst'] - self.predictions_list[alloc['onu'].oid][0]
                        gate = {'name': 'gate', 'onu': alloc['onu'].oid, 'wavelength': self.wavelengths[0], 'grant': []}
                        for burst in range(pred_increment):
                            q.append(alloc['onu'].oid)
                        self.predictions_list[alloc['onu'].oid].pop(0)
                        #falta remover das tabelas de slot
                        #falta remover das ONUs
                    elif alloc['burst'] < self.predictions_list[alloc['onu'].oid][0]:
                        print "is less"
                        self.predictions_list[alloc['onu'].oid].pop(0)
                    else:
                        print "is equal"
                        print("{} - onu {} - cycle {}".format(self.env.now,alloc['onu'].oid,self.cycle))
                        self.predictions_list[alloc['onu'].oid].pop(0)
        return pq,q



    def dwba(self):
        while True:
            yield self.AllocGathering
            print("{} starts cycle {}".format(self.env.now,self.cycle))
            self.granting_start = self.env.now + (self.distance/self.lightspeed)

            if not ( self.cycle in self.cycle_tables.keys() ):
                self.cycle_tables[self.cycle] = slot_table(self.normal_slots,
                    self.grant_slots,self.higher_delay_slots,self.env.now,
                    self.granting_start, self.slot_time,self.wavelengths)
                print "entrei aqui"
            pq1,q1 = self.check_pred(self.alloc_list1)
            pq2,q2 = self.check_pred(self.alloc_list2)
            pq3,q3 = self.check_pred(self.alloc_list3)
            pq4,q4 = self.check_pred(self.alloc_list4)

            Gate = []
            queues = [q1,q2,q3,q4]
            i = 0
            while self.cycle_tables[self.cycle].check_avail_n() and i < len(queues):
                if len(queues[i]) > 0:
                    grant = self.cycle_tables[self.cycle].allocate_n(queues[i][0])
                    if len(grant) > 0:
                        self.GATE[queues[i][0]]['grant'].append( grant )
                        queues[i].pop(0)
                    else:
                        break

                else:
                    i=+1

            i = 0
            while self.cycle_tables[self.cycle].check_avail_e() and i < len(queues):
                if len(q4) > 0:
                    grant = self.cycle_tables[self.cycle].allocate_n(q4[0])
                    if len(grant) > 0:
                        self.GATE[q4[0]]['grant'].append( grant )
                        q4.pop(0)
                    else:
                        break

                else:
                    i=+1

            pq = pq1+pq2+pq3
            if len(pq) > 0:
                for c in pq:
                    for onu in pq[c]:
                        if not ( c in self.cycle_tables.keys() )
                            print("{} - create cycle {} table by pred, onu {}".format(self.env.now,self.cycle +( i+1),onu))
                            c_start = self.cycle_tables[c-1] + self.cycle_interval
                            self.cycle_tables[c] = slot_table(self.normal_slots,
                                self.grant_slots,self.higher_delay_slots,c_start,
                                c_start + (self.distance/self.lightspeed), self.slot_time,self.wavelengths)
                        if self.cycle_tables[c].check_avail_g():
                            grant = self.cycle_tables[c].allocate_g(onu)
                            if len(grant) > 0:
                                self.GATE[onu]['grant'].append( grant )
                                continue
                            else:
                                print("DEU MERDA AQUI")
                                continue
                        if self.cycle_tables[c].check_avail_n():
                            grant = self.cycle_tables[c].allocate_n(onu)
                            if len(grant) > 0:
                                self.GATE[onu][grant].append( grant )
                                continue
                            else:
                                print("DEU MERDA CARALHO AQUI")
                                continue

            if len(pq4) > 0:
                for c in pq4:
                    for onu in pq4[c]:
                        if not ( c in self.cycle_tables.keys() )
                            print("{} - create cycle {} table by pred, onu {}".format(self.env.now,self.cycle +( i+1),onu))
                            c_start = self.cycle_tables[c-1] + self.cycle_interval
                            self.cycle_tables[c] = slot_table(self.normal_slots,
                                self.grant_slots,self.higher_delay_slots,c_start,
                                c_start + (self.distance/self.lightspeed), self.slot_time,self.wavelengths)
                        if self.cycle_tables[c].check_avail_e():
                            grant = self.cycle_tables[c].allocate_e(onu)
                            if len(grant) > 0:
                                self.GATE[onu]['grant'].append( grant )
                                continue
                            else:
                                print("DEU MERDA AQUI")
                                continue


            print "####" *10
            print self.predictions_list
            print "####" *10



            for w in range(self.cycle_tables[self.cycle].w):
                self.active_wavelenghts.append(self.wavelengths[w])

            self.monitoring.fronthaul_active_wavelengths(len(self.active_wavelenghts))
            for i,gate in enumerate(self.GATE):
                self.grant_store.put(gate)
                self.GATE[i]['grant']=[]
            self.alloc_list1 = []
            self.alloc_list2 = []
            self.alloc_list3 = []
            self.alloc_list4 = []
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

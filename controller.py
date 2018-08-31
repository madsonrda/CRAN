import time
import simpy
import random
import sys

class traffic_ctl(object):
    def __init__(self,env,traffic_gen_list,tempo):
        self.env = env
        self.traffic_gen_list = traffic_gen_list
        self.tempo = tempo
        self.cpri_option =2
        self.fases = [self.increase,self.constant,self.decrease]
        self.action = self.env.process(self.run())


    def increase(self,end):
        print "ENTREI   "
        dist = zip(range(len(self.traffic_gen_list))*4,[ random.expovariate(500) for i in range(len(self.traffic_gen_list))*4])
        for i,j in dist:
            yield self.env.timeout(j)
            gen = self.traffic_gen_list[i]
            gen.CpriConfig(gen.cpri_option +1 )
            if self.env.now > 0.499:
                break


        # while self.env.now < end:
        #     print "--"*5
        #     print end
        #     print self.cpri_option
        #     print self.env.now
        #     print "--"*5
        #     if self.env.now > 0.49:
        #         break


            #yield self.env.timeout(self.tempo/4.0)
            # for gen in self.traffic_gen_list:
            #     yield self.env.timeout((self.tempo/4.0)/float(len(self.traffic_gen_list)))
            #     gen.CpriConfig(self.cpri_option)
            # self.cpri_option += 1
            # print("aumentei para {}".format(self.cpri_option))
            # print self.env.now
            # if self.cpri_option > 6:
            #     print "maior que 6"
            #     self.cpri_option = 6

    def constant(self,end):
        # for gen in self.traffic_gen_list:
        #     gen.CpriConfig(self.cpri_option)
        yield self.env.timeout(self.tempo)
        self.cpri_option -= 1

    def decrease(self,end):

        dist = zip(range(len(self.traffic_gen_list))*4,[ random.expovariate(500) for i in range(len(self.traffic_gen_list))*4])
        for i,j in dist:
            yield self.env.timeout(j)
            gen = self.traffic_gen_list[i]

            cpri = gen.cpri_option -1
            if cpri < 1:
                cpri = 1
            gen.CpriConfig(cpri)


        # while self.env.now < end:
        #
        #
        # #    yield self.env.timeout(self.tempo/4.0)
        #     self.cpri_option -= 1
        #     print "--"*5
        #     print end
        #     print self.cpri_option
        #     print self.env.now
        #     print "--"*5
        #     print("reduzi para {}".format(self.cpri_option))
        #     if self.cpri_option < 1:
        #         print "menor que 1"
        #         self.cpri_option = 1
        #     for gen in self.traffic_gen_list:
        #         yield self.env.timeout((self.tempo/4.0)/float(len(self.traffic_gen_list)))
        #         gen.CpriConfig(self.cpri_option)



    def run(self):
        print "desg"
        for fase in self.fases:
            print fase
            end = self.env.now + self.tempo
            proc = self.env.process(fase(end))
            yield proc

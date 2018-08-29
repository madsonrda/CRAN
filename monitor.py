import time
import simpy
import random
import os

class monitor(object):
    """class for gathering statistics"""
    def __init__(self,env,FILENAME):
        self.env = env
        self.fronthaul_delay_file = open("{}-delay.csv".format(FILENAME),"w")
        self.fronthaul_delay_file.write("delay,timestamp\n")
        self.fronthaul_dwba_wavelengths = open("{}-dwba-wave.csv".format(FILENAME),"w")
        self.fronthaul_dwba_wavelengths.write("active,timestamp\n")
        self.grant_idle_file = open("{}-grant-usage.csv".format(FILENAME),"w")
        self.grant_idle_file.write("idle,slot,usage,timestamp\n")
        self.required_slots_file = open("{}-required-slots.csv".format(FILENAME),"w")
        self.required_slots_file.write("onu,cycle,slots,timestamp\n")


    def get_delay(self,pkt_time):
        return (self.env.now - pkt_time)
    def fronthaul_delay(self,pkt_time):
        #print self.env.now
        delay = self.get_delay(pkt_time)
        #print delay < 0.000250
        #print 'delay'
        #print delay
        self.fronthaul_delay_file.write("{},{}\n".format(delay,self.env.now))
    def fronthaul_active_wavelengths(self,wavelengths):
        self.fronthaul_dwba_wavelengths.write("{},{}\n".format(wavelengths,self.env.now))
    def grant_usage(self,start,end,consumption):
        slot = end - start
        idle = slot - consumption
        usage = (consumption * 100)/float(slot)
        #if usage == 0 or usage > 100:
            #print "usage"
            #print usage
            #print slot
            #print consumption
            #print "XXXXX"
        self.grant_idle_file.write("{},{},{},{}\n".format(idle,slot,usage,self.env.now))

    def required_slots(self,cycle,slots,onu):
        self.required_slots_file.write("{},{},{},{}\n".format(onu,cycle,slots,self.env.now))

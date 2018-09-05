import time
import simpy
import random
import os

class monitor(object):
    """class for gathering statistics"""
    def __init__(self,env,FILENAME):
        self.env = env
        self.fronthaul_delay_file = open("{}-delay.csv".format(FILENAME),"w")
        self.fronthaul_delay_file.write("delay,timestamp,cycle\n")
        self.fronthaul_dwba_wavelengths = open("{}-dwba-wave.csv".format(FILENAME),"w")
        self.fronthaul_dwba_wavelengths.write("active,timestamp,cycle\n")
        self.grant_idle_file = open("{}-grant-usage.csv".format(FILENAME),"w")
        self.grant_idle_file.write("idle,slot,usage,timestamp,cycle\n")
        self.required_slots_file = open("{}-required-slots.csv".format(FILENAME),"w")
        self.required_slots_file.write("onu,cycle,slots,timestamp\n")
        self.pkt_sent_file = open("{}-pkt-sent.csv".format(FILENAME),"w")
        self.pkt_sent_file.write("wavelength,size,timestamp,cycle\n")
        self.cycle = 0


    def get_delay(self,pkt_time):
        return (self.env.now - pkt_time)
    def fronthaul_delay(self,pkt_time):
        #print self.env.now
        delay = self.get_delay(pkt_time)
        if delay > 0.000250:
            print "..."*10
            print self.env.now
            print ""
            print delay
            print "..."*10
        #print delay
        self.fronthaul_delay_file.write("{},{},{}\n".format(delay,self.env.now,self.cycle))
    def fronthaul_active_wavelengths(self,wavelengths):
        self.fronthaul_dwba_wavelengths.write("{},{},{}\n".format(wavelengths,self.env.now,self.cycle))
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
        self.grant_idle_file.write("{},{},{},{},{}\n".format(idle,slot,usage,self.env.now,self.cycle))

    def required_slots(self,cycle,slots,onu):
        self.required_slots_file.write("{},{},{},{}\n".format(onu,cycle,slots,self.env.now))
    def pkt_sent(self,pkt_size,wavelength):
        self.pkt_sent_file.write("{},{},{},{}\n".format(wavelength,pkt_size,self.env.now,self.cycle))

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

    def get_delay(self,pkt_time):
        return self.env.now - pkt_time
    def fronthaul_delay(self,pkt_time):
        delay = self.get_delay(pkt_time)
        self.fronthaul_delay_file.write("{},{}\n".format(delay,self.env.now))

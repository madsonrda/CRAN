import time
import simpy
import random
import os
#from collections import deque

class monitor(object):
    """class for gathering statistics"""
    def __init__(self,env,FILENAME, interval = 1):
        self.env = env
        self.interval = interval
        self.fronthaul_delay_file = open("{}-delay.csv".format(FILENAME),"w")
        self.fronthaul_delay_file.write("delay,timestamp\n")
        self.fronthaul_dwba_wavelengths = open("{}-dwba-wave.csv".format(FILENAME),"w")
        self.fronthaul_dwba_wavelengths.write("active,timestamp\n")
        self.grant_idle_file = open("{}-grant-usage.csv".format(FILENAME),"w")
        self.grant_idle_file.write("idle,slot,usage,timestamp\n")
        
        self.bandwidth_UL_file = open("{}-bandwidth-UL.csv".format(FILENAME),"w")
        self.bandwidth_UL_file.write("wavelength,oid,size,timestamp\n")
#        self.monit_interval = self.env.process(self.monit_interval())

        self.wavelengths = {}

        #self.bw_wave_list = [0] * wavelengths
        #self.last_bw_wave_list = [0] * wavelengths

    def get_delay(self,pkt_time):
        return (self.env.now - pkt_time)
    def fronthaul_delay(self,pkt_time):
        delay = self.get_delay(pkt_time)
        self.fronthaul_delay_file.write("{},{}\n".format(delay,self.env.now))
    def fronthaul_active_wavelengths(self,wavelengths):
        self.fronthaul_dwba_wavelengths.write("{},{}\n".format(wavelengths,self.env.now))
    def grant_usage(self,start,end,usage):
        slot = end - start
        idle = slot - usage
        usage = (usage * 100)/float(slot)
        self.grant_idle_file.write("{},{},{},{}\n".format(idle,slot,usage,self.env.now))

    def set_UL_bw(self,oid, wavelength, pkt_size, timestamp):
        """Increment UL bandwidth usage in wavelength X. Flushes after a second"""
        try: 
            aux = self.wavelengths[wavelength]
        except:
            print "CREATED WAVELENGTH %d" %wavelength
            self.create_wavelength(wavelength)

        sec_before = self.wavelengths[wavelength]['sec_UL_timestamp']
        if self.env.now > (sec_before + 1):
            #Then a second has passed. Time to flush counter
            print "MONITOR - passou 1 segundo - %f > %f" % (self.env.now, sec_before)
            print "WAVELENGTH %d - SECOND BPS == %f" % (wavelength,self.wavelengths[wavelength]['UL_bps'])
            self.wavelengths[wavelength]['last_UL_bps'] = self.wavelengths[wavelength]['UL_bps']
            self.wavelengths[wavelength]['UL_bps'] = 0
            self.wavelengths[wavelength]['sec_UL_timestamp'] = self.env.now
        
        self.wavelengths[wavelength]['UL_bps']+=pkt_size
        self.wavelengths[wavelength]['last_UL_timestamp'] = self.env.now

        self.bandwidth_UL_file.write("{},{},{},{}\n".format(wavelength,oid,pkt_size,timestamp))

    def get_UL_bw(self,wavelength):
        """Returns last UL usage in bps"""
        sec_before = self.wavelengths[wavelength]['sec_UL_timestamp']
        if self.env.now > (sec_before + 2):
            # IF its 2 seconds ahead of last timestamp, it means no more pkts arrived since then
            return 0
        return self.wavelengths[wavelength]['last_UL_bps']

    def create_wavelength(self,wavelength):
        # TODO: Minute average --> "avg_min_UL_bps": 0.0, "last_avg_min_UL_bps": 0.0, 

        self.wavelengths[wavelength] = {"active": 0, "UL_bps": 0, "last_UL_bps": 0, 
        "last_UL_timestamp": 0.0, "sec_UL_timestamp": self.env.now, "min_UL_timestamp": self.env.now}

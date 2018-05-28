import time
import simpy
import random

class ODN(object):
    """This class represents optical distribution Network."""
    #{'lambda':{active: int,OLT_id: int, ONU_dict: {oid,distance}, }}
    def __init__(self, env):
        self.env = env
        self.wavelengths = {}
        self.OLTs = None
        self.ONUs = None
        self.lightspeed = float(200000)
        self.upstream = simpy.Store(self.env)
        self.downstream = simpy.Store(self.env)
        self.up_proc = self.env.process(self.UpStream())
        self.down_proc = self.env.process(self.DownStream())

    def set_ONUs(self,ONUs):
        self.ONUs = ONUs

    def set_OLTs(self,OLTs):
        self.OLTs = OLTs

    def create_wavelength(self,wavelength):
        self.wavelengths[wavelength] = {"active": 0, "OLT": -1}

    def activate_wavelenght(self, wavelength,olt):
        self.wavelengths[wavelength]["active"] = 1
        self.wavelengths[wavelength]["OLT"] = olt

    def propagation_delay(self,onu):
        distance = self.ONUs[onu].distance
        delay = distance/self.lightspeed
        yield self.env.timeout(delay) #propagation delay

    def UpStream(self):
        while True:
            onu,pkt,wavelength = yield self.upstream.get()
            self.env.process( self.propagation_delay(onu) )
            olt = self.wavelengths[wavelength]["OLT"]
            self.OLTs[olt].ULInput.put(pkt)

    def DownStream(self):
        while True:
            msg = yield self.downstream.get()
            self.env.process( self.propagation_delay(msg['onu']) )
            self.ONUs[msg['onu']].DLInput.put(msg)

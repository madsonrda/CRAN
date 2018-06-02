import time
import simpy
import random
import sys
from cable import ODN
from olt import OLT
from dba import DBA, Nakayama_DWBA
from onu import ONU
from traffic_gen import PacketGenerator, Packet
from bbu import BBU
from bbupool import BBUPool

#criar env
random.seed(50)
env = simpy.Environment()
bbu_store = simpy.Store(env)
#criar ODN
odn = ODN(env)
#criar wavelengths
wavelengths = []
for i in range(100):
    wavelengths.append(i)

for w in wavelengths:
    odn.create_wavelength(w)
#criar ONU
ONUs = []
for i in range(3):
    ONUs.append(ONU(i,env,wavelengths,100,odn))

#criar PacketGenerator

pkt_gen = []
for i in range(3):
    pkt_gen.append(PacketGenerator(env,i,ONUs[i],bbu_store,1))

#####BRUNO
BBUPool1= BBUPool(env,0,odn)

proc_buffer = BBUPool1.post_proc_buffer
print proc_buffer
bbu1 = BBU(env,0,proc_buffer,3)

BBUPool1.BBU_list.append(bbu1)
#####

#criar OLT
dba = {'name':"Nakayama_DWBA"}
olt = OLT(env,0,odn,ONUs,wavelengths,dba,BBUPool1)
odn.set_ONUs(ONUs)
odn.set_OLTs([olt])

def bbu_sched(olt,bbu_store):
    while True:
        alloc_signal = yield bbu_store.get()
        olt.AllocInput.put(alloc_signal)
bbu = env.process(bbu_sched(olt,bbu_store))

#start simulation
env.run(until=2)

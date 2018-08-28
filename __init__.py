import time
import simpy
import random
import sys
from cable import ODN
from olt import OLT
from dba import DBA, Nakayama_DWBA
from onu import ONU
from bbupool import BBUPool
from traffic_gen import PacketGenerator, Packet
from monitor import monitor
from controller import traffic_ctl as tc




#criar env
random.seed(50)
env = simpy.Environment()
#criar monitor
monitoring = monitor(env,"PM_DWBA")
bbu_store = simpy.Store(env)
#criar ODN
odn = ODN(env)
#criar wavelengths
wavelengths = []
for i in range(1000):
    wavelengths.append(i)

for w in wavelengths:
    odn.create_wavelength(w)
#criar ONU
ONUs = []
for i in range(3):
    ONUs.append(ONU(i,env,monitoring,wavelengths,20,odn))

#criar PacketGenerator

pkt_gen = []
for i in range(3):
    #pkt_gen.append(PacketGenerator(env,i,ONUs[i],bbu_store,random.randint(1,2)))
    pkt_gen.append(PacketGenerator(env,i,ONUs[i],bbu_store,1))

#criar dc local
dc_local = BBUPool(env,0,2000)
for i in range(3):
    dc_local.add_bbu(i)

#criar link entre a OLT e o BBU POOL
link_dc_local = ODN(env)
link_dc_local.create_wavelength(1500)#wavelength = 150
link_dc_local.activate_wavelenght(1500,0)#wavelength e bbupoll_id
link_dc_local.set_OLTs([dc_local])

#criar OLT
#dba = {'name':"Nakayama_DWBA"}
dba = {'name':"PM_DWBA"}
olt = OLT(env,monitoring,0,odn,ONUs,wavelengths,dba,link_dc_local,1500)
odn.set_ONUs(ONUs)
odn.set_OLTs([olt])
def bbu_sched(olt,bbu_store):
    while True:
        alloc_signal = yield bbu_store.get()
        olt.AllocInput.put(alloc_signal)
bbu = env.process(bbu_sched(olt,bbu_store))
link_dc_local.set_ONUs([olt])

tc(env,pkt_gen,0.5)
#start simulation
env.run(until=1.5)

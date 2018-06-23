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




#criar env
random.seed(50)
env = simpy.Environment()
#criar monitor
monitoring = monitor(env,"teste")
bbu_store = simpy.Store(env)
#criar ODN
odn = ODN(env,monitoring)
#criar wavelengths
wavelengths = []
for i in range(100):
    wavelengths.append(i)

for w in wavelengths:
    odn.create_wavelength(w)
#criar ONU
ONUs = []
for i in range(30):
    ONUs.append(ONU(i,env,monitoring,wavelengths,20,odn))

#criar PacketGenerator

pkt_gen = []
for i in range(30):
    pkt_gen.append(PacketGenerator(env,i,ONUs[i],bbu_store,random.randint(1,3)))

# #criar dc central
# dc_central = BBUPool(env,0,250)
# for i in range(3):
#     dc_central.add_bbu(i)

# #criar link entre a DC-LOCAL e o DC-CENTRAL
# link_midhaul = ODN(env)
# link_midhaul.create_wavelength(200)#wavelength = 150
# link_midhaul.activate_wavelenght(200,0)#wavelength e bbupoll_id
# link_midhaul.set_OLTs([dc_central])

#criar dc local
dc_local = BBUPool(env,0,200)
for i in range(30):
    dc_local.add_bbu(i)

#criar link entre a OLT e o BBU POOL
link_dc_local = ODN(env,monitoring)
link_dc_local.create_wavelength(150)#wavelength = 150
link_dc_local.activate_wavelenght(150,0)#wavelength e bbupoll_id
link_dc_local.set_Bside_nodes([dc_local])

#set ONU and OLT for midhaul
ONUs.append(ONU(i,env,monitoring,wavelengths,20,odn))


#criar OLT
#dba = {'name':"Nakayama_DWBA"}
dba = {'name':"M_DWBA"}
olt = OLT(env,monitoring,0,odn,ONUs,wavelengths,dba,link_dc_local,150)
odn.set_Aside_nodes(ONUs)
odn.set_Bside_nodes([olt])
def bbu_sched(olt,bbu_store):
    while True:
        alloc_signal = yield bbu_store.get()
        olt.AllocInput.put(alloc_signal)
bbu = env.process(bbu_sched(olt,bbu_store))
link_dc_local.set_Aside_nodes([olt])

#start simulation
env.run(until=2)

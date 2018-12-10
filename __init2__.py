import arguments
from logcontrol import *
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
#from spliting_ctl import Orchestrator as Splitter

log.basicConfig(filename='example.log',level=log.DEBUG) # filemode='w'

DURATION = DURATION/1000.0 # transforming second to ms
BWMID = BWMID * 1000 # transforming GB to MB
INTERVAL = INTERVAL * 1000 # transforming second to ms
LTHOLD = LTHOLD/100.0
HTHOLD = HTHOLD/100.0

##### SIMULATION FLAGS: #####

#Disable logging by uncommenting below
log.disable(True)

#############################

#pega sinalizacao pro grant do mdba
def bbu_sched(olt,bbu_store):
    while True:
        alloc_signal = yield bbu_store.get()
        olt.AllocInput.put(alloc_signal)

#criar env
random.seed(50)
env = simpy.Environment()

#criar monitor
monitoring = monitor(env,"teste")

#criar dc central
#dc_central_id = 0
#dc_central = BBUPool(env,dc_central_id,250)

#######
#DC LOCAL 1

cell1=1

#for i in range(N_RRHS):
#    dc_central.add_bbu(i)

wavelength1 = 200

#criar link entre a EDGE e o DC-LOCAL
#link_midhaul1 = ODN(env,monitoring,"midhaul1")
#link_midhaul1.create_wavelength(wavelength1,dc_central_id)#wavelength = 200
#link_midhaul1.activate_wavelength(wavelength1,dc_central_id)#wavelength e bbupoll_id

#criar dc local 1
split1=1
distance1 = 1
dc_local1 = BBUPool(env,1,wavelength1,split1,distance1)


#dc_local1_cells = 30

for i in range(N_RRHS):
    dc_local1.add_bbu(i)

#link_midhaul1.set_Bside_nodes({0:dc_central})
#link_midhaul1.set_Aside_nodes({1:dc_local1})

bbu_store1 = simpy.Store(env)

#criar ODN
fronthaul1 = ODN(env,monitoring,"fronthaul1")
#criar wavelengths
wavelengths1 = []
for i in range(100):
    wavelengths1.append(i)

for w in wavelengths1:
    fronthaul1.create_wavelength(w,0)
#criar ONUs
ONUs1 = {}
for i in range(N_RRHS):
    ONUs1[i]=ONU(i,env,monitoring,wavelengths1,20,fronthaul1)

#criar PacketGenerator
pkt_gen1 = []

for i in range(N_RRHS):
    #pkt_gen1.append(PacketGenerator(env,i,ONUs1[i],bbu_store1,random.randint(1,N_RRHS)))

    cpri1=1
    pkt_gen1.append(PacketGenerator(env,i,ONUs1[i],bbu_store1,cell1,cpri1))
#criar link entre a OLT e o BBU POOL
link_dc_local1 = ODN(env,monitoring,"link_dc_local1")
link_dc_local1.create_wavelength(150,1)#wavelength = 150
link_dc_local1.activate_wavelength(150,1)#wavelength e bbupoll_id
link_dc_local1.set_Bside_nodes({1:dc_local1})

#criar OLT
#dba = {'name':"Nakayama_DWBA"}
dba1 = {'name':"PM_DWBA"}
olt1 = OLT(env,monitoring,0,fronthaul1,ONUs1,wavelengths1,dba1,link_dc_local1,150)
fronthaul1.set_Aside_nodes(ONUs1)
fronthaul1.set_Bside_nodes({0:olt1})

link_dc_local1.set_Aside_nodes({0:olt1})

bbu1 = env.process(bbu_sched(olt1,bbu_store1))

# init split algorithm
#splitter1= Splitter(env)
#splitter1.init_bbu_dict(cell1, edge_BBUs_obj_list , dc_BBUs_obj_list, split)


# 'TIDAL' EFFECT
#tc(env,pkt_gen1,0.5)
#tc(env,pkt_gen2,0.5)

#start simulation
env.run(until=0.5)

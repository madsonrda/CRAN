import logging as log
from arguments import *
import os
import time

print "TOPOLOGY == %s" % TOPOLOGY

time_sim = {'time': 0}
FORMAT = "%(levelname)s: %(asctime)s at SIMTIME:%(time)f = %(message)s"

log.basicConfig(format=FORMAT,filename='example.log',level=log.DEBUG) # filemode='w'

log.debug("STARTING LOG", extra=time_sim)

#logging.basicConfig(filename='func-sim.log',level=logging.DEBUG,format='%(asctime)s %(message)s')

#dir_path = os.path.dirname(os.path.realpath(__file__))
timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
os.makedirs("csv/"+timestamp)
# os.makedirs("csv/"+timestamp+"/pkt")
# os.makedirs("csv/"+timestamp+"/proc")
# os.makedirs("csv/"+timestamp+"/bw")
# os.makedirs("csv/"+timestamp+"/energy")
pkts_file = open("csv/{}/{}-{}-{}-{}-{}-{}-{}-{}-pkts.csv".format(timestamp,N_CELLS,N_RRHS,ADIST,SEED,DURATION,LTHOLD,HTHOLD,BWMID),"w")
proc_pkt_file = open("csv/{}/{}-{}-{}-{}-{}-{}-{}-{}-proc-pkt.csv".format(timestamp,N_CELLS,N_RRHS,ADIST,SEED,DURATION,LTHOLD,HTHOLD,BWMID),"w")
bw_usage_file = open("csv/{}/{}-{}-{}-{}-{}-{}-{}-{}-bw-usage.csv".format(timestamp,N_CELLS,N_RRHS,ADIST,SEED,DURATION,LTHOLD,HTHOLD,BWMID),"w")
base_energy_file = open("csv/{}/{}-{}-{}-{}-{}-{}-{}-{}-base-energy.csv".format(timestamp,N_CELLS,N_RRHS,ADIST,SEED,DURATION,LTHOLD,HTHOLD,BWMID),"w")
proc_usage_file = open("csv/{}/{}-{}-{}-{}-{}-{}-{}-{}-proc-usage.csv".format(timestamp,N_CELLS,N_RRHS,ADIST,SEED,DURATION,LTHOLD,HTHOLD,BWMID),"w")

pkts_file.write("timestamp,pkt_id,cell_id,prb,cpri_option,coding\n") #DONE
proc_pkt_file.write("cell_id,vbbu_id,cloud,pkt_id,split,gops_vbbu,gops_pkt,energy,time_start,time_end,proc_delay\n") #DONE
bw_usage_file.write("cell_id,vbbu_id,haul,pkt_id,bw,plane,type\n") #DONE
base_energy_file.write("entity,id,energy,timestamp\n") # DONE
proc_usage_file.write("cell_id,vbbu_id,cloud,gops,pcnt,timestamp\n") #DONE
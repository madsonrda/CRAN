import argparse as arg

#TODO:
# - Put these arguments to the use
# - Make a better help text
# - Option for ETH MTU
######

parser = arg.ArgumentParser(description="Function Splitting - RAN Simulator")
#parser.add_argument("-T", type=str, default='Hybrid',choices=["CRAN","DRAN","Hybrid"], help="Topology")
parser.add_argument("-T", "--type", type=str, default='Hybrid', help="Choose simulation type, between CRAN,DRAN and Hybrid (default).")
parser.add_argument("-D", "--duration", type=int, default=2, help="Duration of simulation, in miliseconds.")
parser.add_argument("-S", "--seed", type=int, default=50, help="Random number generator seed number.")
parser.add_argument("-C", "--cells", type=int, default=2, help="Cell clusters number.")
parser.add_argument("-R", "--rrhs", type=int, default=3, help="Remote radio heads number per cell cluster.")
parser.add_argument("-A", "--adist", type=int, default=4, help="Interval between CPRI packets arrival in ms.")
parser.add_argument("-L", "--lthold", type=int, default=60, help="Lower orchestrator's threshold in %, to trigger splitting.")
parser.add_argument("-H", "--hthold", type=int, default=90, help="Higher orchestrator's threshold in %, to trigger splitting.")
parser.add_argument("-B", "--bwmid", type=int, default=10, help="Maximum Midhaul bandwidth in Gbits.")
parser.add_argument("-I", "--interval", type=int, default=2.001, help="Interval in secs between orchestrator consulting the MID.")
parser.add_argument("-G", "--geninterval", type=float, default=0.0005, help="Interval in seconds between pkts generated at RRH.")
#parser.add_argument("-Q", "--qlimit", type=int, default=None, help="The size of the FH and MID port queue in bytes.")

args = parser.parse_args()

#Arguments
TOPOLOGY = args.type
DURATION = args.duration
SEED = args.seed
N_CELLS = args.cells
N_RRHS = args.rrhs
ADIST = args.adist
LTHOLD = args.lthold
HTHOLD = args.hthold
BWMID = args.bwmid
INTERVAL = args.interval
GEN_INTERVAL = args.geninterval

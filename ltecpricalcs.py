from collections import defaultdict
import math
import pandas as pd
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

"""
UPLINK LTE and CPRI calculations
The Multidimensional table called splits_info contains the bandwidth and 
virtual function processing cost (in flops) for every possible scenario: 
- for every coding scheme (ex. 64QAM) and
- every possible CPRI option
- every splitting option

how to use it:
splits_info[coding][cpri_option][split_option]['bw']
or
splits_info[coding][cpri_option][split_option]['gops']
"""

# _ means 'per'
# DOWNLINK is NOT simulated yet

#### PHY layer parameters assumptions
CPRI_data=8.0
CPRI_total=10.0
CPRI_coding=CPRI_total/CPRI_data

n_RB= 100.0
n_SUB_SYM= 14.0
n_RB_SC= 12.0
n_Data_Sym=12.0

nAnt=2.0 		# number of antennas (2x2MIMO=4 antenna, 2 TX(DL) and 2 RX(UL))
n_Sector= 4		# 2x2MIMO = 4 setor
A = nAnt * n_Sector

QmPUSCH=4.0 	# 16QAM
LayersUL=1.0	# Could also be 2 (2x2 mimo). But, BW calc of splits 4 and 5 would return the same bandwidth..
RefSym_RES=6.0	# Number of REs for reference signals per RB per sub-frame (for 1 or 2 antennas) 
nIQ=32.0 		#16I + 16Q bits
PUCCH_RBs=4.0 #RBs allocated for PUCCH
nLLR=8.0
nSIC=1.0		# No SIC

#### L2/L3 layers parameters assumptions
HdrPDCP=2.0
HdrRLC=5.0
HdrMAC=2.0
IPpkt=1500.0
nTBS_UL_TTI= 2.0	# 1 Layer
Sched=0.5 		# Scheduler overhead per UE
FAPI_UL=1.0		# Uplink FAPI overhead per UE in Mbps
MCS_UL=28		# Dynamic tho. Attribute of each 'packet generated'

# Tables
mcs_2_tbs=[0,1,2,3,4,5,6,7,8,9,9,10,11,12,13,14,15,15,16,17,18,19,20,21,22,23,24,25,26]
# TBS_TABLE USAGE: tbs_table[resourceblocks][TBS_Index] -> Where TBS_Index == mcs_2_tbs[MCS]
tbs_table= pd.read_excel(dir_path + "/tabelas/TBS-table.xlsx")


# -->> FOR DOWNLINK ONLY <<--
# #### PHY layer parameters assumptions
# LayersDL=2
# CFI=1.0		# CFI symbols
# QmPDSCH=6.0 	# 64QAM
# QmPCFICH=2.0 	# QPSK
# QmPDCCH=2.0  	# QPSK
# PDSCH_REs= n_RB *(n_RB_SC *(n_SUB_SYM-CFI)-(RefSym_RES*nAnt)) # =150
# Regardless of System Bandwidth, PCFICH is always carried by 4 REGs (16 REs) at the first symbol of each subframe
# PCFICH_REs=16.0 
# PHICH_REs=12.0 	#one PHICH group
# PDCCH_REs=144.0 	#aggregation lvl 4
# nUE=1 	# number of users per TTI
# MCS_DL=28
#
# #### L2/L3 layers parameters assumptions
# TBS_DL=75376 	# Transport block size (in bits) 
# IP_TTI_DL= (TBS_DL)/((IPpkt + HdrPDCP + HdrRLC + HdrMAC) *8) 
# nTBS_DL_TTI= 2 	# 2 Layers
# FAPI_DL=1.5
# ---------------------------

## PACKET INCOMING
# For each CPRI type we have different set of variables for calcs.
# CPRI options 4 and 6 do not fit 2x2MIMO LTE traffic perfectly, its necessary\
# to set custom Fs (Mhz) for each antenna in order achieve a better LTE<->CPRI fit 
used_CPRIs=[1,2,3,5,7]
# Table below used for calcs
CPRI={\
1:{'Mhz':1.25,'Fs':1.92,'PRB':6},\
2:{'Mhz':2.5,'Fs':3.84,'PRB':12},\
3:{'Mhz':5.0,'Fs':7.68,'PRB':25},\
4:5,\
5:{'Mhz':10.0,'Fs':15.36,'PRB':50},\
6:10,\
7:{'Mhz':5,'Fs':30.72,'PRB':100}}

splits_info = defaultdict( lambda: defaultdict( lambda: defaultdict( lambda: defaultdict(float))))

for coding in range(0,29):
	for cpri_option in used_CPRIs:

		#----------- Changing CPRI option, we change:
		# 	PRB 
		#	sampling frequency MHz
		#	TBS
		# 	IP pkt TTI

		#print "Coding: %d 	CPRI OPTION: %d" % (coding,cpri_option)
		TBS_UL = tbs_table[CPRI[cpri_option]['PRB'] - PUCCH_RBs][mcs_2_tbs[MCS_UL]]
		#print "TBS: %.3f" % TBS_UL
		
		IP_TTI_UL= (TBS_UL)/((IPpkt + HdrPDCP + HdrRLC + HdrMAC) *8)
		#print "IP_TTI_UL: %.3f" % IP_TTI_UL
		#--------------------------------------------


		#--------------BW & GOPS CALCS---------------
		# SPLIT 1 -> PHY SPLIT IV - SCF
		a1_UL = nIQ * CPRI_coding
		r1_UL= CPRI[cpri_option]['Fs'] * nAnt * n_Sector * a1_UL
		# nIQ= (2*(15+1))= 32 -> facilita aproximacao nas contas
		splits_info[coding][cpri_option][1]['bw'] = r1_UL
		
		gops_1 = int((cpri_option*nAnt*n_Sector*a1_UL)/10)
		splits_info[coding][cpri_option][1]['gops'] = gops_1
		#print "Split1 : %.3f Mbps	GOPS:%d |" % (r1_UL, gops_1),

		# SPLIT 2 -> PHY SPLIT IIIb - SCF
		a2_UL= nIQ
		r2_UL= CPRI[cpri_option]['Fs'] * nAnt * n_Sector * a2_UL
		splits_info[coding][cpri_option][2]['bw'] = r2_UL
		
		gops_2 = int((cpri_option*nAnt*n_Sector*a2_UL*nIQ)/100)
		splits_info[coding][cpri_option][2]['gops'] = gops_2
		#print "Split2 : %.3f Mbps  GOPS:%d |" % (r2_UL,gops_2)
				
		# SPLIT 3 -> PHY SPLIT III - SCF
		a3_UL = n_RB_SC * n_Data_Sym * nIQ # <- *1000 / 1000000
		r3_UL = (a3_UL * nAnt * n_Sector * CPRI[cpri_option]['PRB'])/1000
		gops_3 = int(r3_UL/10)
		splits_info[coding][cpri_option][3]['bw'] = r3_UL
		splits_info[coding][cpri_option][3]['gops'] = gops_3
		#print "Split3 : %.3f Mbps	GOPS:%d |" % (r3_UL,gops_3),

		#SPLIT 4 -> PHY SPLIT II - SCF
		r4_UL = (n_Data_Sym * n_RB_SC * (CPRI[cpri_option]['PRB'] - PUCCH_RBs) * nAnt * nIQ)/1000
		splits_info[coding][cpri_option][4]['bw'] = r4_UL

		# Can be better represented.. -> insert every variable of r4_UL in the calculation (insert PUCCH_RBs)
		gops_4= int(2*gops_2) 
		
		splits_info[coding][cpri_option][4]['gops'] = gops_4
		#print "Split4 : %.3f Mbps   GOPS:%d |" % (r4_UL, gops_4)

		# SPLIT 5 -> PHY SPLIT I - SCF
		r5_UL = (n_Data_Sym * n_RB_SC * (CPRI[cpri_option]['PRB'] - PUCCH_RBs) * QmPUSCH * LayersUL * nSIC * nLLR) / 1000
		if coding > 3: 
			gops_5= int((gops_4) * (coding**2/(1+coding+(coding*math.sqrt(coding)))))
		else: #  In coding <= 3, split 5 has lower gops than split 4 
			gops_5= int(gops_4) #lower limit is equal to split 4
		splits_info[coding][cpri_option][5]['gops'] = gops_5
		splits_info[coding][cpri_option][5]['bw'] = r5_UL
		#print "Split5 : %.3f Mbps 	GOPS:%d | " % (r5_UL, gops_5),

		# SPLIT 6 -> SPLIT MAC-PHY - SCF
		a6_UP = (IP_TTI_UL* (IPpkt + HdrPDCP + HdrRLC + HdrMAC) * nTBS_UL_TTI)/ 125
		r6_UL = a6_UP * LayersUL + FAPI_UL
		gops_6 = int(a6_UP*LayersUL)
		splits_info[coding][cpri_option][6]['bw'] = r6_UL
		splits_info[coding][cpri_option][6]['gops'] = gops_6
		#print "Split6 : %.3f Mbps	GOPS:%d |" % (r6_UL,gops_6)

		# SPLIT 7 -> SPLIT RRC-PDCP - SCF
		a7_UP = (IP_TTI_UL * IPpkt * nTBS_UL_TTI) / 125
		r7_UL = a7_UP * LayersUL
		# GOPS calculates the processing cost of a function, but function 7 doesn't exist for us
		# gops_7 = int(a7_UP * LayersUL) # legacy calcs for gops_7
		gops_7 = 0
		# BW in split 7 can also be approximated by TBS/1000.0
		splits_info[coding][cpri_option][7]['bw'] = r7_UL 
		splits_info[coding][cpri_option][7]['gops'] = gops_7
		#########

		# Total GOPS of coding and CPRI_option 
		GOPS_total= gops_1+gops_2+gops_3+gops_4+gops_5+gops_6+gops_7
		splits_info[coding][cpri_option]['gops_total']= GOPS_total
		#print "Split7 : %.3f Mbps	GOPS:%d 	GOPS TOTAL Split1:%d|\n" % (r7_UL,gops_7,GOPS_total)

		# measuring edge and metro gops for each split in each coding and cpri option
		for split in range(1,8):
			edge_gops=0
			if split > 1:
				for ec_split in range(1,split):
					edge_gops+= splits_info[coding][cpri_option][ec_split]['gops']
			splits_info[coding][cpri_option][split]['edge_gops']= edge_gops

			metro_gops=0
			if split < 7:
				for metro_split in range(split,7):
					metro_gops+= splits_info[coding][cpri_option][metro_split]['gops']
			splits_info[coding][cpri_option][split]['metro_gops']= metro_gops
		#-----------------END OF BW AND GOPS CALCS ----------------------- 

#print dict(splits_info)

# BETTER PRINT OF DEFAULT DICT \/
#import json
#data_as_dict = json.loads(json.dumps(splits_info, indent=4))
#print(data_as_dict)
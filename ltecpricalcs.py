from collections import defaultdict
import math
import pandas as pd
import os
#import logging as log
from logcontrol import *

dir_path = os.path.dirname(os.path.realpath(__file__))

#time_sim = {0: 0}
time_sim = {'time': 0}
FORMAT = "%(levelname)s: %(asctime)s at SIMTIME:%(time)f = %(message)s"

log.basicConfig(format=FORMAT,filename='example.log',level=log.DEBUG) # filemode='w'
#FORMAT = "%(levelname)s: %(asctime)s at SIMTIME:%(time)f = %(message)s"

#log.basicConfig(format=FORMAT,filename='example.log',level=log.DEBUG) # filemode='w'
log.debug("STARTING LTE & CPRI CALCULATIONS", extra=time_sim)

"""
UPLINK LTE and CPRI calculations
The Multidimensional table called UL_splits contains the bandwidth and 
virtual function processing cost (in flops) for every possible scenario: 
- for every coding scheme (ex. 64QAM) and
- every possible CPRI option
- every splitting option

how to use it:
UL_splits[coding][cpri_option][split_option]['bw']
or
UL_splits[coding][cpri_option][split_option]['gops']

OBS: '_' means 'per' in variables description
OBS: DOWNLINK is NOT simulated yet
"""



#### PHY layer parameters assumptions
# DEPENDE CPRI_data=8.0
# DEPENDE CPRI_total=10.0
# SOME CPRI_coding=CPRI_total/CPRI_data

#DEPENDE n_RB= 100.0
n_SUB_SYM= 14.0
n_RB_SC= 12.0
n_Data_Sym=12.0

nAnt=2.0 		# number of antennas (2x2MIMO=4 antenna, 2 TX(DL) and 2 RX(UL))
n_Sector=1		# 2x2MIMO = 4 setor
A = nAnt * n_Sector

QmPUSCH=4.0 	# 16QAM
LayersUL=1.0	# Could also be 2 (2x2 mimo). But, BW calc of splits 4 and 5 would return the same bandwidth..
RefSym_RES=6.0	# Number of REs for reference signals per RB per sub-frame (for 1 or 2 antennas) 
nIQ=32.0 		# 16I + 16Q bits
PUCCH_RBs=4.0 	#RBs allocated for PUCCH
nLLR=8.0
nSIC=1.0		# No SIC


#### L2/L3 layers parameters assumptions
HdrPDCP=2.0
HdrRLC=5.0
HdrMAC=2.0
IPpkt=1500.0
nTBS_UL_TTI= 1.0	# 1 Layer
Sched=0.5 		# Scheduler overhead per UE
FAPI_UL=1.0		# Uplink FAPI overhead per UE in Mbps
MCS_UL=23		# Dynamic tho. Attribute of each 'packet generated'

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
#used_CPRIs=[1,2,3,5,7]
# Table below used for calcs
# CPRI={\
# 1:{'Mhz':1.25,'Fs':1.92,'PRB':6},\
# 2:{'Mhz':2.5,'Fs':3.84,'PRB':12},\
# 3:{'Mhz':5.0,'Fs':7.68,'PRB':25},\
# 4:5,\
# 5:{'Mhz':10.0,'Fs':15.36,'PRB':50},\
# 6:10,\
# 7:{'Mhz':20.0,'Fs':30.72,'PRB':100}}

##################
## NOVAS TABELAS CPRI E AxC
# SUBSTITUIRAO A TABELA CPRI ACIMA

CPRI={\
'1':{'BitPerWord':8 , 'PRBs':50,'BW':614.4},\
'2':{'BitPerWord':16, 'PRBs':100,'BW':1228.8},\
'3':{'BitPerWord':32, 'PRBs':200,'BW':2457.6},\
'4':{'BitPerWord':40, 'PRBs':250,'BW':3072},\
'5':{'BitPerWord':64, 'PRBs':400,'BW':4915.21},\
'6':{'BitPerWord':80, 'PRBs':500,'BW':6144.01},\
'7':{'BitPerWord':128, 'PRBs':800,'BW':9830.41},\
'7A':{'BitPerWord':128, 'PRBs':800,'BW':8110.09},\
'8' :{'BitPerWord':160,'PRBs':1000, 'BW':10137.7},\
'9' :{'BitPerWord':192,'PRBs':1200, 'BW':12165.13},\
'10':{'BitPerWord':384, 'PRBs':2400,'BW':24330.25}}

# NO DIRECT USAGE... BUT WORKED AS REFERENCE FOR AxC TABLE (TOWARDS END OF CODE)
AxC={\
1.25:{'8B/10B':76.8, '64B/66B':63.36, 'Fs':1.92, 'PRB':6},\
2.5:{'8B/10B':153.6, '64B/66B':126.72, 'Fs':3.84, 'PRB':12},\
5.0:{'8B/10B':307.2, '64B/66B':254.44, 'Fs':7.68, 'PRB':25},\
10.0:{'8B/10B':614.4, '64B/66B':506.88, 'Fs':15.36, 'PRB':50},\
15.0:{'8B/10B':921.6, '64B/66B':760.32, 'Fs':23.04, 'PRB':75},\
20.0:{'8B/10B':1228.8, '64B/66B':1013.76, 'Fs':30.72, 'PRB':100}}


#RESULTADOS PRBS PARCIAIS
# 1 - 50
# 2 - 100
# 3 - 200
# 4 - 250
# 5 - 400
# 6 - 500
# 7 - 800
# 7A - 800
# 8 - 1000
# 9 - 1200
# 10 = 2400

#TABLE AxCs per CPRI - 20Mhz - 1 reception antenna
# Mhz	CPRIs: 1	2	3	4	5	6	7	7A	8	9	10
# 1.25											
# 2.5											
# 5											
# 10			1			1							
# 15											
# 20				1	2	2	4	5	8	8	10	12	24

#TABLE AxCs per CPRI - 10Mhz - 1 reception antenna
# Mhz	CPRIs: 1	2	3	4	5	6	7	7A	8	9	10
# 1.25											
# 2.5											
# 5											
# 10			1	2	4	5	8	10	16	16	20	24	48
# 15											
# 20

#TABLE AxCs per CPRI - 5Mhz - 1 reception antenna
# Mhz	CPRIs: 1	2	3	4	5	6	7	7A	8	9	10
# 1.25											
# 2.5											
# 5											
# 10			1	2	4	5	8	10	16	16	20	24	48
# 15											
# 20				

###### TO CALCULATE HOW MANY PRBS AT MOST MAY FIT AT EACH CPRI OPTION

# print "\n\n\n START\n"
# for option in CPRI2:
# 	print "\n\nentrou1 - OPTION %s" % option
# 	prbs=0
# 	prbs_bw=0
# 	total_bw=CPRI2[option]['BW']
# 	aux1=total_bw
# 	counter=0
# 	atrib_loop_anterior=0
# 	for cada in [20.0, 15.0, 10.0, 5.0, 2.5, 1.25]:
# 		print "NEXT AxC - entrou 2 - start check loop AxC %d for CPRI %s with bucket=%d and counter=%d" % (cada, option, aux1, counter)
# 		if counter ==0:
# 			print "entrou 10 - Loop AxC anterior nao atribuiu, setando atrib_loop==0 "
# 			atrib_loop_anterior=0
		
# 		if math.floor(aux1) == 0 or math.ceil(aux1) == 0:
# 			print "entrou 9 - DONE - CPRI%s - PRBs %d" % (option,prbs)
# 			break
# 		else:
# 			aux1=total_bw - prbs_bw
# 			print "entrou 12 - reduzindo bucket para %d " % aux1
# 		#if atrib_loop_anterior == 0:
# 		#	aux1=total_bw
# 		counter=0

# 		if option in ['7A','8','9','10']:
# 			bw_AxC=AxC[cada]['64B/66B']
# 		else:
# 			bw_AxC=AxC[cada]['8B/10B']
# 		print "entrou 3 - Banda escolhida bw_AxC=%d" % bw_AxC
# 		while True:
# 			print "entrou 4 - entrou while true"
# 			aux1=aux1 - bw_AxC
# 			print "entrou 5 - apos reduzir bucket para %d, pela bw_AxC=%d" % (aux1, bw_AxC)
# 			if aux1 >= 0:
# 				counter+=1
# 				print "entrou 6, bucket ainda nao negativo, counter=%d" %counter
# 				if math.floor(aux1) == 0 or math.ceil(aux1) == 0:
# 					print "entrou 11 - floor deu == 0"
# 					prbs=prbs + (AxC[cada]['PRB'] * counter)
# 					prbs_bw=prbs_bw + bw_AxC*counter
# 					#aux1=aux1 - prbs
# 					CPRI2[option]['PRBs']=prbs
# 					atrib_loop_anterior=1
# 					break
# 			else:
# 				print "entrou 7, bucket negativo=%d e counter=%d" % (aux1,counter)
# 				prbs=prbs + (AxC[cada]['PRB'] * counter)
# 				prbs_bw=prbs_bw + bw_AxC*counter
# 				aux1=aux1 - prbs
# 				CPRI2[option]['PRBs']=prbs
# 				atrib_loop_anterior=1
# 				print "entrou 8, somando %d prbs ao total de PRBs do CPRI %s" % (prbs,option)
# 				break

# for cada in CPRI2:
# 	print "!!!!!!!!! Total PRBs in CPRI %s: %d" % (cada,CPRI2[cada]['PRBs'])

####################

UL_splits = defaultdict( lambda: defaultdict ( lambda: defaultdict(float)))
#UL_splits[coding][cpri_option][split]
MHz_splits = defaultdict( lambda: defaultdict( lambda: defaultdict(float)))
#MHz_splits[Mhz][split]
#mhz > split > bw

#UPLINK CALCULATION
#for coding in range(23,24):
coding=23
MHZs={5:5,10:10,20:20}
for mhz in MHZs:
	if mhz == 20:
		CPRI_coding=10/8.0
		PRB=100
		Fs=30.72
		cpri_option='3'
		int_cpri_option=3
	if mhz == 10:
		CPRI_coding=10/8.0
		PRB=50
		Fs=15.36
		cpri_option='2'
		int_cpri_option=2
	if mhz == 5:
		CPRI_coding=10/8.0
		PRB=25
		Fs=7.68
		cpri_option='1'
		int_cpri_option=1

	print "\n\n-------MHZ %d ------\n" % mhz
	
	#----------- Changing CPRI option, we change:
	# 	PRB 
	#	sampling frequency MHz
	#	TBS
	# 	IP pkt TTI
	#CPRI[cpri_option]['PRBs']

	#print "Coding: %d 	CPRI OPTION: %d" % (coding,cpri_option)
	TBS_UL = tbs_table[PRB - PUCCH_RBs][mcs_2_tbs[MCS_UL]]
	#print "TBS: %.3f" % TBS_UL
	
	IP_TTI_UL= (TBS_UL)/((IPpkt + HdrPDCP + HdrRLC + HdrMAC) *8)
	#print "IP_TTI_UL: %.3f" % IP_TTI_UL
	#--------------------------------------------


	#--------------BW & GOPS CALCS---------------
	# SPLIT 1 -> PHY SPLIT IV - SCF
	a1_UL = nIQ * CPRI_coding
	r1_UL= Fs * nAnt * n_Sector * a1_UL
	# nIQ= (2*(15+1))= 32 -> facilita aproximacao nas contas
	MHz_splits[mhz][1]['bw'] = r1_UL

	
	gops_1 = int((int_cpri_option*nAnt*n_Sector*a1_UL)/10)
	MHz_splits[mhz][1]['gops'] = gops_1
	print "Split1 : %.3f Mbps	GOPS:%d |" % (r1_UL, gops_1),

	# SPLIT 2 -> PHY SPLIT IIIb - SCF
	a2_UL= nIQ
	r2_UL= Fs * nAnt * n_Sector * a2_UL
	MHz_splits[mhz][2]['bw'] = r2_UL
	
	gops_2 = int((int_cpri_option*nAnt*n_Sector*a2_UL*nIQ)/100)
	MHz_splits[mhz][2]['gops'] = gops_2
	print "Split2 : %.3f Mbps  GOPS:%d |" % (r2_UL,gops_2)
			
	# SPLIT 3 -> PHY SPLIT III - SCF
	a3_UL = n_RB_SC * n_Data_Sym * nIQ # <- *1000 / 1000000
	r3_UL = (a3_UL * nAnt * n_Sector * PRB)/1000
	gops_3 = int(r3_UL/10)
	MHz_splits[mhz][3]['bw'] = r3_UL
	MHz_splits[mhz][3]['gops'] = gops_3
	print "Split3 : %.3f Mbps	GOPS:%d |" % (r3_UL,gops_3),

	#SPLIT 4 -> PHY SPLIT II - SCF
	r4_UL = (n_Data_Sym * n_RB_SC * (PRB - PUCCH_RBs) * nAnt * nIQ)/1000
	MHz_splits[mhz][4]['bw'] = r4_UL

	# Can be better represented.. -> insert every variable of r4_UL in the calculation (insert PUCCH_RBs)
	gops_4= int(2*gops_2) 
	
	MHz_splits[mhz][4]['gops'] = gops_4
	print "Split4 : %.3f Mbps   GOPS:%d |" % (r4_UL, gops_4)

	# SPLIT 5 -> PHY SPLIT I - SCF
	r5_UL = (n_Data_Sym * n_RB_SC * (PRB - PUCCH_RBs) * QmPUSCH * LayersUL * nSIC * nLLR) / 1000
	if coding > 3: 
		gops_5= int((gops_4) * (coding**2/(1+coding+(coding*math.sqrt(coding)))))
	else: #  In coding <= 3, split 5 has lower gops than split 4 
		gops_5= int(gops_4) #lower limit is equal to split 4
	MHz_splits[mhz][5]['gops'] = gops_5
	MHz_splits[mhz][5]['bw'] = r5_UL
	print "Split5 : %.3f Mbps 	GOPS:%d | " % (r5_UL, gops_5),

	# SPLIT 6 -> SPLIT MAC-PHY - SCF
	a6_UP = (IP_TTI_UL* (IPpkt + HdrPDCP + HdrRLC + HdrMAC) * nTBS_UL_TTI)/ 125
	r6_UL = a6_UP * LayersUL + FAPI_UL
	gops_6 = int(a6_UP*LayersUL)
	MHz_splits[mhz][6]['bw'] = r6_UL
	MHz_splits[mhz][6]['gops'] = gops_6
	print "Split6 : %.3f Mbps	GOPS:%d |" % (r6_UL,gops_6)

	# SPLIT 7 -> SPLIT RRC-PDCP - SCF
	a7_UP = (IP_TTI_UL * IPpkt * nTBS_UL_TTI) / 125
	r7_UL = a7_UP * LayersUL
	# GOPS calculates the processing cost of a function, but function 7 doesn't exist for us
	# gops_7 = int(a7_UP * LayersUL) # legacy calcs for gops_7
	gops_7 = 0
	# BW in split 7 can also be approximated by TBS/1000.0
	MHz_splits[mhz][7]['bw'] = r7_UL 
	MHz_splits[mhz][7]['gops'] = gops_7
	#########

	# Total GOPS of coding and CPRI_option 
	GOPS_total= gops_1+gops_2+gops_3+gops_4+gops_5+gops_6+gops_7
	MHz_splits[mhz]['gops_total']= GOPS_total
	print "Split7 : %.3f Mbps	GOPS:%d 	GOPS TOTAL Split1:%d|\n" % (r7_UL,gops_7,GOPS_total)

	#bottom_up_ratio=0
	#up_bottom_ratio=0
	# measuring edge and metro gops for each split in each coding and cpri option
	for split in range(1,8):
		edge_gops=0
		actual_bw=MHz_splits[mhz][split]['bw']

		if split > 1:
			for ec_split in range(1,split):
				edge_gops+= MHz_splits[mhz][ec_split]['gops']
		MHz_splits[mhz][split]['edge_gops']= edge_gops

		metro_gops=0
		if split < 7:
			for metro_split in range(split,7):
				metro_gops+= MHz_splits[mhz][metro_split]['gops']
		MHz_splits[mhz][split]['metro_gops']= metro_gops

		# ######### STARTING RATIO CALCULATIONS #########
		# if split < 7:
		# 	# calculation - BW ratio to move to upper split 
		# 	ratio=0
		# 	ratio= UL_splits[coding][cpri_option][split+1]['bw'] / UL_splits[coding][cpri_option][split]['bw']
		# 	UL_splits[coding][cpri_option][split]['ratio_up'] = ratio
		# 	print "CODING: %d ; CPRI_OPTION: %d ; SPLIT: %d ; SPLIT_BW: %f RATIO_UP: %f" % (coding,cpri_option,split,actual_bw,ratio)
		# 	if bottom_up_ratio==0:
		# 		bottom_up_ratio = ratio
		# 	else:
		# 		bottom_up_ratio= bottom_up_ratio*ratio

		# 	if ratio >= 1:
		# 		#print "WTF ratio up bigger than 1"
		# 		log.warning('WTF ratio BOTTOM->UP higher than 1! CODING: %d ; CPRI_OPTION: %d ; SPLIT: %d ; RATIO_DOWN: %f', coding,cpri_option,split,ratio, extra=time_sim)

		# if split > 1:
		# 	# calculation - BW ratio to move to lower split
		# 	ratio=0
		# 	ratio= UL_splits[coding][cpri_option][split-1]['bw'] / UL_splits[coding][cpri_option][split]['bw']
		# 	UL_splits[coding][cpri_option][split]['ratio_down'] = ratio
		# 	print "CODING: %d ; CPRI_OPTION: %d ; SPLIT: %d ; SPLIT_BW: %f RATIO_DOWN: %f" % (coding,cpri_option,split,actual_bw,ratio)

		# 	if up_bottom_ratio==0:
		# 		up_bottom_ratio = ratio
		# 	else:
		# 	 	up_bottom_ratio= up_bottom_ratio*ratio
		# 	if ratio < 1:
		# 		#print "WTF ratio up lower than 1"
		# 		log.warning('WTF ratio UP->BOTTOM is lower than 1! CODING: %d ; CPRI_OPTION: %d ; SPLIT: %d ; RATIO_DOWN: %f', coding,cpri_option,split,ratio, extra=time_sim)

		# ######### ENDING RATIO CALCULATIONS #########

#-----------------END OF BW AND GOPS CALCS ----------------------- 

#TABLE AxCs per CPRI - 20Mhz
# Mhz	CPRIs: 1	2	3	4	5	6	7	7A	8	9	10
# 1.25											
# 2.5											
# 5											
# 10			1			1							
# 15											
# 20				1	2	2	4	5	8	8	10	12	24

#TABLE AxCs per CPRI - 20Mhz - with 2 antennas in 1x2 SIMO <<<<<<<<<<<<<<< THIS IS THE CORRECT TABLE FOR OUR SIMULATION WITH 1x2 SIMO IN UPLINK
# Mhz	CPRIs: 1	2	3	4	5	6	7	7A	8	9	10
# 1.25											
# 2.5											
# 5				1			1				
# 10				1				1					
# 15											
# 20					1	1	2	2	4	5	5	6	12

########## TEST ZONE ##############

# multiply_8b[CPRIoption][MHZ] retorna multiplicador de qts AxC na respectiva MHz
multiply_8b={'1':{5:1},'2':{10:1},'3':{20:1},'4':{5:1,20:1},'5':{20:2},'6':{10:1,20:2},'7':{20:4}}
ordered=multiply_8b.keys()
ordered.sort()

#completar com multiply_64b={'7A':16,'8':20,'9':24,'10':48}

#from MHz_splits generate UL_splits
#UL_splits[mhz][split]['bw']

# Based on how many AxCs of different MHz fits in each CPRI option,
# below we define the bandwidth of each CPRI_option for every split.
# That is because, by summing the bandwidth of 5,10 or 20Mhz AxCs, we get exact CPRI's and splits' bandwidth
coding=23
for cpri_option in ordered:
	print ""
	for split in range(1,8):
		bw_total =0
		for mhz in multiply_8b[cpri_option]:
			mhz_bw = MHz_splits[mhz][split]['bw']
			multiplier=multiply_8b[cpri_option][mhz]
			
			bw_axc= mhz_bw * multiplier
			bw_total=bw_total + bw_axc

		UL_splits[cpri_option][split]['bw'] = bw_total
		#print "CPRI_option: %s ; Split%d BW: %.3f Mbps ; DICT: %f" % (cpri_option,split,bw_total, UL_splits[cpri_option][split]['bw'])
		#print UL_splits[coding][cpri_option][split]['bw']
		

splits_info=UL_splits

log.debug("FINISHING LTE and CPRI CALCULATIONS - RIGHT BEFORE SIMULATION BEGIN", extra=time_sim)


for cpri in UL_splits:
	for split in UL_splits[cpri]:
		print "CPRI %s Split %d BW: %f" % (cpri,split,UL_splits[cpri][split]['bw'])

####################################

#print dict(UL_splits)

# BETTER PRINT OF DEFAULT DICT \/
#import json
#data_as_dict = json.loads(json.dumps(UL_splits, indent=5))
#print(data_as_dict)


####### FUNCTION TO CALCULATE UP/DOWN RATIO OF SPLIT JUMPS #########
# def splits_bw(cpri_option,init_split,final_split,coding=28):
# 	bw = UL_splits[coding][cpri_option][init_split]['bw']

# 	if init_split > final_split: #split going DOWN -> rising bandwidth
# 		for cada in range(init_split,final_split -1, -1):
# 			bw= bw * UL_splits[coding][cpri_option][init_split]['ratio_down']

# 	elif init_split < final_split: #split going UP -> decaying bandwidth
# 		for cada in range(init_split,final_split +1):
# 			bw= bw * UL_splits[coding][cpri_option][init_split]['ratio_up']

# 	return bw
####################################################################

def get_bits_cpri_split(cpri_op,split_op,interval=1):
	#coding=23
	bw=UL_splits[str(cpri_op)][split_op]['bw'] * interval
	return bw
	#size_bits(bw)

def get_bytes_cpri_split(cpri_op,split_op,interval=1):
	#coding=23
	bw=((UL_splits[str(cpri_op)][split_op]['bw'] * 1000 * 1000 ) * interval) / 8
	return bw
	#size_byte(bw)

#def bits_cpri_split_interval

def size_bits(pkt_size):
	final_size = (pkt_size * 1000 * 1000)
	return final_size

def size_byte(pkt_size,interval):
	"""
	1. Change Mbits to MBytes (divide by 8)
	2. From Mbytes to bytes (multiply by 1million)
	3. Multiply by interval of pkt generation in seconds (ex. 4ms == 0.004)
	"""
	final_size = ((pkt_size / 8) * 1000 * 1000) * interval
	return final_size
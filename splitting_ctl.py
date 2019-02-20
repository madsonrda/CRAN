import simpy
import logging
import ltecpricalcs as calc
from collections import defaultdict
from operator import itemgetter

from pprint import pprint


class Orchestrator(object):
	""" Heuristic now: put everything in dc, limited by FRONTHAUL BW and proactivelly before losses appear (60%<x<90%)
	TODOs: 
	1. Consider energy in calcs
	2. Consider justice in calcs
	3. Consider maximum chain delay in calcs (QOS)
		3.1 Measure chain latency
			3.1.1 (all of them desired) Measure transmission + queing + processing delays

	"""
	def __init__ (self,env,high_thold=0.9,low_thold=0.6,interval=0.008,topology='Hybrid',coding=23,gen_interval=0.004):
		self.env=env
		self.interval = interval
		self.gen_interval = gen_interval
		self.coding = coding

		# multi layer default dict \/
		nested_dict = lambda: defaultdict(nested_dict)
		self.BBUs_dict = nested_dict()
		
		self.high_thold = high_thold
		self.low_thold = low_thold

		#DBA related variables
		self.dba = None
		self.cycle_tables = None
		self.cycle = 0
		self.last_cycle=0
		self.diff=0

		self.actual_slotn = 0
		self.actual_slote = 0
		self.actual_slotg = 0
		self.actual_n_slots = 0
		self.actual_e_slots = 0
		self.actual_g_slots = 0

		self.average_slotn = 0
		self.average_slote = 0
		self.average_slotg = 0
		self.average_n_slots = 0
		self.average_e_slots = 0
		self.average_g_slots = 0

		if topology == 'Hybrid':
			pass
			#self.read_metrics = self.env.process(self.read_metrics())

		# same function (num_pkts_burst), but with 2 names to it
		self.num_pkts_burst = self.sim_slot_usage
	
	def init_bbu_dict(self, cell_id, cell_id_edge_BBUs, cell_id_dc_BBUs, split=1, fronthaul_obj=None):
		# [cell_id][BBU_id]['split']=split
		# [cell_id][BBU_id]['dc_BBU']=class_obj
		# [cell_id][BBU_id]['edge_BBU']=class_obj
		# [cell_id]['fronthaul_obj']= class_obj

		# the algorithm has to know what fronthaul and bbu objects are assigned to which cell

		num_BBUs = len(cell_id_edge_BBUs)
		num_dc_BBUs = len(cell_id_dc_BBUs)
		if num_BBUs == len(cell_id_dc_BBUs): # considering 1 to 1 edge and dc BBUs
			self.BBUs_dict[cell_id]['fronthaul_obj']= fronthaul_obj
			#fronthaul_obj.add_UL_entry('orchestrator',self)

			for BBU in range(num_BBUs):
				edge_BBU = cell_id_edge_BBUs[BBU]
				self.BBUs_dict[cell_id][BBU]['edge_bbu'] = edge_BBU

				dc_BBU = cell_id_dc_BBUs[BBU]
				self.BBUs_dict[cell_id][BBU]['dc_bbu'] = dc_BBU

				self.BBUs_dict[cell_id][BBU]['split'] = split
				self.BBUs_dict[cell_id][BBU]['pred_enabled'] = 0
		else:
			print "Error adding cell in Orchestrator. Not 1 to 1 edges and dc BBUs."
			print "NUM_EDGE_BBUs = %d ; NUM_DC_BBUs = %d" % (num_BBUs,num_dc_BBUs)
			logging.debug("Error adding cell in Orchestrator. Not 1 to 1 edges and dc BBUs.")
		#print ">>" * 30
		#print self.BBUs_dict

	def high_splitting_updt(self,cell_id,phi_metrics,BBU_metrics):
		# total phi drops
		bytes_usage = phi_metrics['UL_bytes_rx_diff']
		reduced_bw = 0
		MID_max_bw = phi_metrics['max_bw']
		print "----- HIGH ORCHESTRATOR - CELL %d ------" % (cell_id)
		#print "Total byte usage MID: %f " % bytes_usage
		
		changed_BBU_splits = {} # dict of changed BBU splits key: BBU_id and value: split 
		
		# ordered list of most bw on a BBU
		usage_list = []
		#print "BBU_metrics"
		#print BBU_metrics
		for cada in BBU_metrics:
			list_pos = (cada,BBU_metrics[cada]['UL_bytes_rx_diff'])
			usage_list.append(list_pos)

		# ordered list
		usage_list.sort(key=itemgetter(1),reverse=True)
		#print "usage list:"
		#print usage_list
		#print ""
		
		cpri_option = 3
		
		diff_bw = 0
		split = 0
		# get most usages and change their split until around 10% under maximum bw of MID
		for BBU_tuple in usage_list:
			try :
				int(BBU_tuple[0])
			except:
				continue

			#print "\nStart test BBU: %s" % BBU_tuple[0]
			if (bytes_usage) > (self.high_thold * MID_max_bw):
				last_bw_diff = 0
				#print "ENTER IF 1: Bytes usage %f > h_thold %f" % (bytes_usage,(self.high_thold * MID_max_bw))
				#print "Reduced bw: %f" % reduced_bw
				#BBU_split = self.BBU_splits[BBU_tuple[0]]

				BBU_split = self.BBUs_dict[cell_id][BBU_tuple[0]]['split']

				#print "BLA %s" % self.BBUs_dict[(cell_id)][BBU_tuple[0]]
				#print BBU_tuple
				#print cell_id
				#print BBU_split
				#print "BBU_split: %d" % BBU_split

				bw_BBU_split = self.splitting_table[self.coding][cpri_option][BBU_split]['bw']
				last_bw_BBU_split=bw_BBU_split
				#print "Actual: BBU split= %d | BBU bw= %.3f | BW last split: %.3f" % \
				#(BBU_split, bw_BBU_split, last_bw_BBU_split)

				for split in range(BBU_split+1,7+1):
					#print "Test split %d" % split,
					bw_split = self.splitting_table[self.coding][cpri_option][split]['bw']
					# difference between splits
					diff_bw = bw_BBU_split - bw_split
					#print "Diff bw= %.3f" % diff_bw
					changed_BBU_splits[BBU_tuple[0]] = split
					
						#bytes_usage -= diff_bw
					# if what was reduced is lower than our threshold
					if (bytes_usage-diff_bw) <= (self.high_thold * MID_max_bw) or split==7:
						#print "ENTER IF 2: diff %f <= h_thold or split 7s" % (bytes_usage-diff_bw)
						if (bytes_usage-diff_bw) <= (self.low_thold * MID_max_bw):
							#print "Entrou low_thold"
							# test if last split bw is > h_thold
							diff_bw2 = last_bw_diff
							#print diff_bw2
							if (bytes_usage-diff_bw2) > (self.high_thold * MID_max_bw):
								#if one split > h_thold and the other < l_thold...
								# let the higher split and choose split of the next BBU
								#print "Last split is higher than h_thold. %f" % (bytes_usage-diff_bw2)
								#print "Changing BBU%d to split %d" % (BBU_tuple[0],split)
								changed_BBU_splits[BBU_tuple[0]] = split
							else:
								#print "Changing BBU%d to split %d" % (BBU_tuple[0],split-1)
								changed_BBU_splits[BBU_tuple[0]] = split-1
							break
						bytes_usage -= diff_bw
						#print "Next BBU. Bytes usage now: %f " % bytes_usage
						#set split
						break
					last_bw_diff=diff_bw
		self.submit_changes(cell_id,changed_BBU_splits)		

	def low_splitting_updt(self,cell_id,phi_metrics,BBU_metrics):
		# total phi drops
		bytes_usage = phi_metrics['UL_bytes_rx_diff']
		reduced_bw = 0
		MID_max_bw = phi_metrics['max_bw']
		print "----- LOW ORCHESTRATOR - CELL %d ------" % (cell_id)
		#print "Total byte usage MID: %f " % bytes_usage
		
		changed_BBU_splits = {} # key: BBU_id ; value: split 
		
		# ordered list of lowest bw on a BBU
		usage_list = []
		#print "BBU_metrics"
		#print BBU_metrics
		for cada in BBU_metrics:
			list_pos = (cada,BBU_metrics[cada]['UL_bytes_rx_diff'])
			usage_list.append(list_pos)

		# ordered list
		usage_list.sort(key=itemgetter(1))
		#print "usage list"
		#print usage_list
		#TODO: Consider that CPRI_option changes. Now CPRI is fixed = 3
		cpri_option = 3
		#TODO: Consider energy in calcs
		diff_bw = 0
		split = 0
		# get most usages and change their split until around 10% under maximum bw of MID
		for BBU_tuple in usage_list:
			try :
				int(BBU_tuple[0])
			except:
				continue

			#print "\nStart test BBU: %s" % BBU_tuple[0]
			if (bytes_usage) <= (self.low_thold * MID_max_bw):
				#print "ENTER IF 1: Bytes usage %f <= l_thold %f" % (bytes_usage,(self.low_thold * MID_max_bw))
				#print self.BBU_splits
				#print "Reduced bw: %f" % reduced_bw
				#BBU_split = self.BBU_splits[BBU_tuple[0]]
				BBU_split = self.BBUs_dict[cell_id][BBU_tuple[0]]['split']
				#print "BBU_split: %d" % BBU_split
				bw_BBU_split = self.splitting_table[self.coding][cpri_option][BBU_split]['bw']
				last_bw_BBU_split = bw_BBU_split
				#print "Actual: BBU split= %d | BBU bw= %.3f | BW last split: %.3f" %\
				# (BBU_split, bw_BBU_split, last_bw_BBU_split)

				#print range(1,BBU_split)[::-1]
				for split in range(1,BBU_split)[::-1]:
					#print "Test split %d" % split,
					bw_split = self.splitting_table[self.coding][cpri_option][split]['bw']
					# difference between splits
					diff_bw = bw_split - bw_BBU_split

					# initializing last_bw_diff at first bbbu
					# if split == BBU_split-1:
					# 	last_bw_diff = diff_bw

					#print "DIFF BW: %.3f " % diff_bw
					changed_BBU_splits[BBU_tuple[0]] = split
					
					# if (bytes_usage+diff_bw) > (self.high_thold * self.MID_max_bw):
					# 	changed_BBU_splits[BBU_tuple[0]] = split+1
					# 	diff_bw = last_bw_diff
					# 	#print "MAIOR. Volta p/ split %d c/ diff %f" % (split+1, diff_bw)
					# 	break
					# if what was reduced is lower than our threshold
					if (bytes_usage+diff_bw) > (self.low_thold * MID_max_bw) or split == 1:
						#print "ENTER IF 2: diff %f > l_thold or split==1" % (bytes_usage+diff_bw)
						if (bytes_usage+diff_bw) > (self.high_thold * MID_max_bw):
							#print "Entrou low_thold"
							# test if last split bw is > h_thold
							diff_bw2 = last_bw_diff
							if (bytes_usage+diff_bw2) <= (self.low_thold * MID_max_bw):
								#if one split > h_thold and the other < l_thold...
								# let the lower split and choose split of the next BBU
								print "Changing BBU%d to split %d" % (BBU_tuple[0],split+1)
								changed_BBU_splits[BBU_tuple[0]] = split+1
							else:
								print "Changing BBU%d to split %d" % (BBU_tuple[0],split)
								break
							
						#print "Entrou 4"
						
						bytes_usage += diff_bw
						#print bytes_usage
						#set split
						break
					last_bw_diff=diff_bw
		self.submit_changes(cell_id,changed_BBU_splits)

	def low_splitting_dba(self,cell_id):
		"""
		project how many slots the lowest consuming & higher priority in 'e' would occupy in 'n' with a lower split
		if it fits in 'n'
			send onu back to 'n'
		otherwise 
			try to reduce 'n' and place it in 'e' 
			if still not fitting:
				reduce another ONU already in 'e' and try projecting again until it fits
		"""
		pass

	def high_splitting_dba(self,cell_id):
		"""
		project how many slots it would occupy in 'e'
		if there is space in 'e'
			send onu to 'e'
		otherwise 
			try to reduce 'e' and place it in 'e' 
			if still not fitting:
				reduce another ONU already in 'e' and try projecting again until it fits
		"""		

	def get_sim_slot_usage(self, cpri_option,pkt_size,split=1):
		""" 
			Returns the number of packets (same as slots) that a ONU in would generate based on the ONU's: 
			Gen Interval; CPRI option and Split option.
		"""
        # ETH PKTs CALCULATION
        # BW= ((BW_bits * interval_pkt_sec) / 8) / eth_pktsize_byte
        
		# MTU_size = pkt_size
		# bw_bytes = calc.get_bytes_cpri_split(cpri_option,split,self.gen_interval)
		
		# num_eth_pkts,last_pkt_size = calc.num_eth_pkts(cpri_option,split,self.gen_interval,MTU_size)
		
		# return num_eth_pkts

		# NEW slot table \/
		return calc.get_slot_usage(cpri_option,split,pkt_size)

	# def check_splitting_ok(self,cell_id,dict_bbu_splits):
	# 	"""
	# 		use sim_slot_usage() for each ONU

	# 		sum their slots
	# 			if split <= 5, put in slots n or g (if available)
	# 			if split >= 6, put in slots e

	# 		check if bigger than

	# 	"""
	# 	sum_n = sum_e = sum_g = 0

	# 	for cada in dict_bbu_splits:
	# 		self.BBUs_dict[cell_id]['']



	def check_pred_enabled(self,bbu_ID):
		"""
		Check if the prediction is enabled for the ONU of a specific BBU
			Thus, validate if we could use the grant timeslots for their data transmission
		
		PS 1: Remember we are currently using 1:1 ONU<->BBU (just like a centralized BBU hotel.. for a simplification purpose)
		PS 2: BBU and ONU share the same OID number
		"""

		# self.dba.predictions_list lists ONUs, but they share the same ID with their BBU (which is what we know)

		num_predictions = len(self.dba.predictions_list[bbu_ID])

		if num_predictions > 0:
			return True
		else:
			return False


	def read_metrics(self):
		# wait interval to gather metrics
		while True:
			yield self.env.timeout(self.interval)

			# update metrics from our single DBA's cycle table
			self.updt_metrics()

			if self.env.now() > 0.15:

				for cell_id in self.BBUs_dict.keys():

					slot_usage_n = (self.actual_slotn / self.actual_n_slots)
					print "Slot usage (n): %f" % slot_usage_n

					if (slot_usage_n >= self.high_thold):
						self.high_splitting_dba(cell_id)

					elif (slot_usage_n <= self.low_thold):
						self.low_splitting_dba(cell_id)

				#print "---> Time now: %d <--- " % self.env.now
				#print self.BBUs_dict.keys()
				for cell_id in self.BBUs_dict.keys():
				# read amount of bytes dropped in midhaul

					#phi_metrics,BBU_metrics = self.MID_port.get_metrics()
					#print cell_id
					MID_port = self.BBUs_dict[cell_id]['fronthaul_obj'] # get MID port
					phi_metrics,BBU_metrics = MID_port.get_metrics() # get metrics of MID port
					MID_max_bw = phi_metrics['max_bw'] # get max BW of MID
					#print MID_max_bw
					#print self.high_thold
					bytes_usage = phi_metrics['UL_bytes_rx_diff'] # get last bytes usage of MID
					#print "bytes_usage %.3f of MIDport from cell %d" % (bytes_usage,cell_id)
					print "%.3f" % (bytes_usage/1000.0)
					#print "HIGH: %.3f" % (self.high_thold * MID_max_bw)
					#print "LOW: %.3f" % (self.low_thold * MID_max_bw)
					# default high_thold is a max of 90% in order to trigger splitting updt
					if (bytes_usage > (self.high_thold * MID_max_bw)):
						#print "HIGH: %.3f" % (float(self.high_thold * MID_max_bw))
						self.high_splitting_updt(cell_id, phi_metrics, BBU_metrics)
					elif (bytes_usage <= (self.low_thold * MID_max_bw)):
					 	self.low_splitting_updt(cell_id, phi_metrics, BBU_metrics)
					#print "\n\n"

	#UPDT needed \/
	def submit_changes(self, cell_id, changed_BBU_splits):
		# write changes to the EDGE BBU POOL
		print "SPLITS CHANGED"
		print changed_BBU_splits
		if len(changed_BBU_splits) > 0:
			for cada in changed_BBU_splits:
				#print "CADA %d" % cada
				#create pkt
				str_BBU = str(cada)
				split_updt = {'plane':'ctrl','src':'orchestrator', 'dst':'edge_pool_'+str(cell_id), \
							  'BBU_id':cada, 'split':changed_BBU_splits[cada]}
				#print split_updt
				#send to MID_port
				
				# updt splits table of edge BBUs 
				#self.BBU_splits[cell_id][cada]= changed_BBU_splits[cada]
				self.BBUs_dict[int(cell_id)][cada]['split'] = changed_BBU_splits[cada]

				MID_port=self.BBUs_dict[int(cell_id)]['fronthaul_obj']
				MID_port.downstream.put(split_updt)
		else:
			logging.debug("WARNING: No better splitting possible at cell%d. Actual MID BW: %.3f" %(cell_id,MID_max_bw))

	# def set_split_all(self):
	# 	pass

	def set_dba(self,dba):
		self.dba= dba
		#pprint(vars(dba))
		self.cycle_table = dba.cycle_tables

	def get_actual_cycle(self):
		return self.dba.cycle

	def enable_pred(self,cell_ID,bbu_ID):
		self.BBUs_dict[cell_ID][bbu_ID]['pred_enabled'] = 1

	def disable_pred(self,cell_ID,bbu_ID):
		self.BBUs_dict[cell_ID][bbu_ID]['pred_enabled'] = 0

	# OK \/
	def updt_metrics(self):
		#1. get actual dba cycle
		#2. diff between actual cycle and cycle of last orch interval 
		#3. iterate through the diff
		#4. calc differences in slot usage
		#5. return values
		#->> if they exceed read_metric() thresholds they trigger splitting 
		
		#1. get actual dba cycle
		actual_cycle = self.get_actual_cycle()

		#2. diff
		diff = actual_cycle - last_cycle

		average_slotn = 0
		average_slote = 0
		average_slotg = 0
		average_n_slots = 0
		average_e_slots = 0
		average_g_slots = 0

		#3.
		for i in range(last_cycle,actual_cycle+1):

			average_slotn += self.cycle_tables[i].slotn # em uso slot N
	        average_slote += self.cycle_tables[i].slote # em uso slot E
	        average_slotg += self.cycle_tables[i].slotg # em uso slot G
	        average_n_slots += self.cycle_tables[i].n_slots # total slot N
	        average_e_slots += self.cycle_tables[i].e_slots # total slot E
	        average_g_slots += self.cycle_tables[i].g_slots # total slot G

	    #4. calc average diffs
		# no need for this average thing when the changes occurs so sporadically in real life
		# but in our simulation everything happens under a second for speedy purposes...	
		# so our orch interval must be shorter than the cpri changes in our load variation algorithm (LVA)
		# my vote: 
			#.1 keep both, instant and average (its done above anyways) metrics
			#.2 and lower orch interval to below LVA's
		self.diff = diff
		self.average_slotn =  average_slotn / diff
		self.average_slote =  average_slote / diff
		self.average_slotg =  average_slotg / diff
		self.average_n_slots = average_n_slots / diff
		self.average_e_slots =  average_e_slots / diff
		self.average_g_slots = average_g_slots / diff

		self.actual_slotn = self.cycle_tables[actual_cycle].slotn
		self.actual_slote = self.cycle_tables[actual_cycle].slote
		self.actual_slotg = self.cycle_tables[actual_cycle].slotg
		self.actual_n_slots = self.cycle_tables[actual_cycle].n_slots
		self.actual_e_slots = self.cycle_tables[actual_cycle].e_slots
		self.actual_g_slots = self.cycle_tables[actual_cycle].g_slots

		
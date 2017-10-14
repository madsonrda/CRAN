import simpy
import argparse
import logging
import pandas as pd
from collections import defaultdict
import os
import math
from operator import itemgetter
import time
from scipy.stats import truncnorm
import numpy as np


class Packet_CPRI(object):
	""" This class represents a network packet """
	def __init__(self, time, cell_id, rrh_id, CPRI_option, coding, id, src="a", dst="z"):
		self.time = time# creation time
		self.cell_id= cell_id
		self.rrh_id= rrh_id
		self.plane='data'
		self.coding = coding #same as MCS

		self.CPRI_option = CPRI_option

		self.size = (splits_info[coding][self.CPRI_option][1]['bw'])/100
		self.prb = CPRI[self.CPRI_option]['PRB']
		#print self.size
		self.id = id # packet id
		self.src = str(src) #packet source address
		self.dst = str(dst) #packet destination address
		pkts_file.write("{},{},{},{},{},{}\n".format(time,id,cell_id,self.prb,CPRI_option,coding))

	def __repr__(self):
		return "id: {}, src: {}, time: {}, CPRI_option: {}, coding: {}".\
			format(self.id, self.src, self.time, self.CPRI_option, self.coding)

class Packet_Generator(object):
	"""This class represents the packet generation process """
	def __init__(self, env, cell_id, rrh_id, adist, finish=float("inf"), interval=100):
		self.cell_id = cell_id
		self.rrh_id = rrh_id # packet id
		self.env = env # Simpy Environment
		self.adist = adist #packet arrivals distribution

		self.coding = 28 #coding fixed for now

		self.finish = finish # packet end time
		self.interval = interval

		self.out = None # packet generator output
		self.packets_sent = 0 # packet counter
		self.action = env.process(self.run())  # starts the run() method as a SimPy process
		self.change_cpri = env.process(self.change_cpri())

# In 'Analytical and Experimental Evaluation of CPRI over Ethernet Dynamic Rate Reconfiguration',
# its possible to change CPRI option in slightly under 1ms

	def change_cpri(self):
		# variables for cpri calcs (truncaded integer normal distribution)
		mean=3.3
		sd=1
		low=1
		upp=5
		# initial random timeout between RRHs
		#self.env.timeout(random.random())

		while True:
			# workaround to generate a normal distribution in a range of 1 to 5
			X = truncnorm((low - mean) / sd, (upp - mean) / sd, mean, sd).rvs().round().astype(int)
			if X == 4:
				self.CPRI_option = 5
			elif X == 5:
				self.CPRI_option = 7
			else:
				self.CPRI_option = X
			yield self.env.timeout(self.interval)

	def run(self):
		"""The generator function used in simulations. """
		while self.env.now < self.finish:
			# wait for next transmission
			yield self.env.timeout(self.adist)
			self.packets_sent += 1
			#print "New packet generated at %f" % self.env.now

			p = Packet_CPRI(self.env.now, self.cell_id, self.rrh_id, self.CPRI_option, self.coding,\
							self.packets_sent, src=self.rrh_id, dst=self.rrh_id)
			#time,rrh_id, coding, CPRI_option, id, src="a"
			#print p
			#Logging
			#pkt_file.write("{}\n".format(self.fix_pkt_size))
			self.out.put(p)
	# call the function put() of RRHPort, inserting the generated packet into RRHPort' buffer

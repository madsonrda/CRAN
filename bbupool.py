import simpy
from bbu import BBU
import logging as log
import simtime as l


class BBUPool(object):
	def __init__(self,env,bbupoll_id,wavelength,split=7,odn=None,distance=0):
	#def __init__(self,env,DC_type,bbupoll_id,OLT,odn=None):
 		self.env = env
 		self.d = {'bla': self.env.now}
 		#self.DC_type = DC_type # 1 = Fog node; 2 = DC local; 3 = DC central
		self.wavelength = wavelength
 		self.bbupoll_id = bbupoll_id
 		self.ULInput = simpy.Store(self.env)
		self.odn = odn
		self.pre_proc_buffer = simpy.Store(self.env)
		self.post_proc_buffer = simpy.Store(self.env)
		self.split = split
		self.distance = distance

		self.pre_proc = self.env.process(self.Pre_Proc()) #
		self.post_proc = self.env.process(self.Post_Proc())

		self.BBU_DICT = {}

	def add_bbu(self,bbu_id):
		self.BBU_DICT[bbu_id] = BBU(self.env,bbu_id,self.bbupoll_id,self.post_proc_buffer,split=self.split)

	def Pre_Proc(self):
		while True:
			pkt = yield self.ULInput.get()

			BBU_id = pkt.src # src id is the same for all DC BBUs of a cell
			self.BBU_DICT[BBU_id].proc_buffer.put(pkt) #write to BBU proc buffer

	def Post_Proc(self):
		while True:
			pkt = yield self.post_proc_buffer.get()
			if self.odn != None:
				#print "BBUPOOL %d: Send to ODN" % self.bbupoll_id
				#log.debug("now: %f", self.env.now)
				#log.debug("D: %f", self.d['time'])
				#log.debug("BBUPOOL %d: Send to ODN", self.bbupoll_id, extra=l.stime(self.env))

				msg = (self.bbupoll_id,pkt,self.wavelength)
				self.odn.wavelengths[self.wavelength]['upstream'].put(msg)

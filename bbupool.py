import simpy

class BBUPool(object):
	def __init__(self,env,oid,odn=None):
	#def __init__(self,env,DC_type,oid,OLT,odn=None):
 		self.env = env
 		#self.DC_type = DC_type # 1 = Fog node; 2 = DC local; 3 = DC central
 		self.oid = oid
 		self.odn = odn
		self.pre_proc_buffer = simpy.Store(self.env)
		self.post_proc_buffer = simpy.Store(self.env)

		self.pre_proc = self.env.process(self.Pre_Proc()) #
		self.post_proc = self.env.process(self.Post_Proc())

		self.BBU_list = []

	def Pre_Proc(self):
		while True:
			pkt = yield self.pre_proc_buffer.get()
			print "CHEGOU PKT NO BBU BUFFER"
			print pkt

			BBU_id = pkt.src # src id is the same for all DC BBUs of a cell
			
			self.BBU_list[BBU_id].proc_buffer.put(pkt) #write to BBU proc buffer

	def Post_Proc(self):
		while True:
			pkt = yield self.post_proc_buffer.get()
			#if odn != none:
			print "BBUPOOL: Send to ODN"



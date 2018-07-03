import simpy
import ltecpricalcs as calc

interval = 0.004

class BBU(object):
	def __init__(self,env,bbu_id,bbupoll_id,post_proc_buffer=None,split=7):
		self.bbu_id = bbu_id
		self.bbupoll_id = bbupoll_id
		self.env = env
		self.split = split
		self.proc_timeout = 1/1000.0 # 1ms
		self.proc_buffer = simpy.Store(self.env)
		self.check_procbuffer = self.env.process(self.Check_ProcBuffer())

		self.postProc_buffer = post_proc_buffer # post proc buffer da BBU POOL

	def set_split(self,split):
		self.split = split

	def Check_ProcBuffer(self):
		while True:
			pkt = yield self.proc_buffer.get()
			yield self.env.process(self.Proc(pkt))

	def Proc(self,pkt):
		#print "PKT sendo processado"
		if self.bbupoll_id == 0:
			print "Pacote chegou no DC CENTRAL!!"
		if pkt.split != self.split:
			pkt.split = self.split
			
			table_size = calc.splits_info[pkt.coding][pkt.cpri_option][pkt.split]['bw']
			pkt.size = calc.size_byte(table_size,pkt.interval)

			# later add energy cost
			# later add processed pkt to log file

			# fix proc timeout
			self.env.timeout(self.proc_timeout)
		else:
			#print "SPLITS iguais, segue o jogo"
			yield self.env.timeout(0)
		self.postProc_buffer.put(pkt)

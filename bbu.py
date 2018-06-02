import simpy
import ltecpricalcs as calc

class BBU(object):
	def __init__(self,env,bbu_id,post_proc_buffer=None,split=1):
		self.bbu_id = bbu_id
		self.env = env
		self.split = split
		self.proc_timeout = 1/1000 # 1ms

		self.proc_buffer = simpy.Store(self.env)
		self.check_procbuffer = self.env.process(self.Check_ProcBuffer())

		self.postProc_buffer = post_proc_buffer # post proc buffer da BBU POOL


	# todo: function to change self.split

	def Check_ProcBuffer(self):
		while True:
			pkt = yield self.proc_buffer.get()
			yield self.env.process(self.Proc(pkt))

	def Proc(self,pkt):
		print "PKT sendo processado"
		if pkt.split != self.split:
			pkt.split = self.split
			bw_split = (calc.splits_info[pkt.coding][pkt.cpri_option][pkt.split]['bw'])/100
			pkt.size = bw_split

			# later add energy cost
			# later add processed pkt to log file

			# fix proc timeout
			self.env.timeout(self.proc_timeout)
		else:
			print "SPLITS iguais, segue o jogo"
		self.postProc_buffer.put(pkt)

import simpy
import ltecpricalcs as calc
import logging as log
import simtime as l

interval = 0.004

class BBU(object):
	def __init__(self,env,bbu_id,bbupoll_id,post_proc_buffer=None,split=7):
		self.bbu_id = bbu_id
		self.bbupoll_id = bbupoll_id
		self.env = env
		self.split = split
		self.proc_timeout = 1/1000.0 # 1ms of processing timeout
		self.proc_buffer = simpy.Store(self.env)

		# ETH PKT BUFFER
		self.pkt=None
		self.buffer_bits=0
		self.expected_bw=0
		#########

		self.check_procbuffer = self.env.process(self.Check_ProcBuffer())

		self.postProc_buffer = post_proc_buffer # post proc buffer da BBU POOL

	def set_split(self,split):
		self.split = split

	def Check_ProcBuffer(self):
		while True:
			pkt = yield self.proc_buffer.get()
			if self.pkt == None:
				#print "STARTING BUFFER OF BBU %d" % self.bbu_id
				self.pkt = pkt
				self.buffer_bits+= pkt.mtu
				self.expected_bw = calc.get_bytes_cpri_split(pkt.cpri_option,pkt.split,pkt.interval)
				#print "CPRI %d SPLIT %d INTERVAL %f EXPECTED BW == %f" % (pkt.cpri_option,pkt.split,pkt.interval,self.expected_bw)
				##print "PKT SIZE %d incremented to "
				self.env.process(self.Proc(pkt))
				yield self.env.timeout(0)
			else:
				self.buffer_bits+=pkt.mtu
				#print "BBU %d ; CELL %d ; BUFFER BITS %f ; CPRI %d ; EXPECTED BW %f ; TIME: %f" % \
				(self.bbu_id,pkt.cell,self.buffer_bits,pkt.cpri_option,self.expected_bw, self.env.now)

				if self.buffer_bits == self.expected_bw:
					#print "BUFFER BITS == EXPECTED BW AT BBU %d ! YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS" % self.bbu_id

					self.buffer_bits = 0
					self.pkt=None
					yield self.env.process(self.Proc(pkt))

				elif self.buffer_bits > self.expected_bw:
					#print "WTF BUFFER NA BBU DEU MAIOR DO QUE O SPLIT TEM ALGO ERRADO!"
					#print "BUFFER_bits: %f ; BW CPRI %d SPLIT %d: %f" \
					% (self.buffer_bits,pkt.cpri_option,pkt.split, self.expected_bw)
					#print "Seguindo adiante ainda sim... PKT SIZE == EXPECTED BW OF CPRI OPTION "

					self.buffer_bits = 0
					self.pkt=None
					yield self.env.process(self.Proc(pkt))

	def Proc(self,pkt):
		##print "PKT sendo processado"
		if self.bbupoll_id == 0:
			#print "Pacote %d chegou no DC CENTRAL! SRC-ID:%d ;CPRI-option:%d ;Size:%d ;Split:%d " % (pkt.id,pkt.src,pkt.cpri_option,pkt.size,pkt.split)
		if pkt.split != self.split:
			#print "SPLITOU DE %d para %d - Pacote %d de SRC-ID:%d na BBU-ID: %d" % (pkt.split,self.split,pkt.id,pkt.src,self.bbu_id)
			pkt.split = self.split

			table_size = calc.splits_info[str(pkt.cpri_option)][pkt.split]['bw']
			pkt.cpri_size = calc.size_byte(table_size,pkt.interval)

			# later add energy cost
			# later add processed pkt to log file

			# fix proc timeout
			self.env.timeout(self.proc_timeout)
		else:
			#print "SPLITS iguais, segue o jogo"
			yield self.env.timeout(0)
		self.postProc_buffer.put(pkt)

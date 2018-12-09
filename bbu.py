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
		
		######### ETH PKT BUFFER
		self.pkt=None
		self.buffer_pkts=0
		self.expected_pkts=0

		### debug only
		self.buffer_bytes=0
		self.expected_bw=0
		###
		
		#########

		self.check_procbuffer = self.env.process(self.Check_ProcBuffer())

		self.postProc_buffer = post_proc_buffer # post proc buffer da BBU POOL

	def set_split(self,split):
		self.split = split

	def Check_ProcBuffer(self):
		while True:
			pkt = yield self.proc_buffer.get()
			if self.pkt == None:
				print "STARTING BUFFER OF BBU %d" % self.bbu_id
				self.pkt = pkt
				self.buffer_pkts+=1
				
				### debug only
				self.buffer_bytes+=pkt.size
				self.expected_bw = calc.get_bytes_cpri_split(pkt.cpri_option,pkt.split,pkt.interval)
				###
				
				self.expected_pkts = calc.num_eth_pkts(pkt.cpri_option,pkt.split,pkt.interval,pkt.size)

				print "CPRI %d SPLIT %d INTERVAL %f EXPECTED PKTs == %d" % (pkt.cpri_option,pkt.split,pkt.interval,self.expected_pkts)
				
				yield self.env.timeout(0)
			else:
				self.buffer_pkts+=1
				self.buffer_bytes+=pkt.size
				print "BBU %d ; CELL %d ; BUFFER BITS %f ; CPRI %d ; EXPECTED PKTs %d ; TIME: %f" % \
				(self.bbu_id,pkt.cell,self.buffer_pkts,pkt.cpri_option,self.expected_pkts, self.env.now)

				if self.buffer_pkts == self.expected_pkts:
					print "BUFFER PKTs == EXPECTED PKTs AT BBU %d ! YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS" % self.bbu_id
					print "BUFFER_pkts: %d BUFFER_size: %f EXPECTED_bytes: %f ; BW CPRI %d SPLIT %d: %d" \
					% (self.buffer_pkts,self.buffer_bytes,self.expected_bw,pkt.cpri_option,pkt.split, self.expected_pkts)
					
					self.buffer_pkts = 0
					yield self.env.process(self.Proc(pkt))
					self.buffer_bytes=0
					self.pkt=None
				
				elif self.buffer_pkts > self.expected_pkts:
					print "WTF BUFFER NA BBU DEU MAIOR DO QUE O SPLIT TEM ALGO ERRADO!"
					print "BUFFER_pkts: %d ; BW CPRI %d SPLIT %d: %f" \
					% (self.buffer_pkts,pkt.cpri_option,pkt.split, self.expected_pkts)
					#print "Seguindo adiante ainda sim... PKT SIZE == EXPECTED BW OF CPRI OPTION "

					self.buffer_pkts = 0
					yield self.env.process(self.Proc(self.pkt))
					self.buffer_bytes=0
					self.pkt=None

				yield self.env.timeout(0)
					
	def Proc(self,pkt):
		#print "PKT sendo processado"
		if self.bbupoll_id == 0:
			print "Pacote %d chegou no DC CENTRAL! SRC-ID:%d ;CPRI-option:%d ;Size:%d ;Split:%d " % (pkt.id,pkt.src,pkt.cpri_option,pkt.size,pkt.split)
		if pkt.split != self.split:
			print "SPLITOU DE %d para %d - Pacote %d de SRC-ID:%d na BBU-ID: %d" % (pkt.split,self.split,pkt.id,pkt.src,self.bbu_id)
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

		if self.postProc_buffer != None:
			#if there is no central DC 
			self.postProc_buffer.put(pkt)

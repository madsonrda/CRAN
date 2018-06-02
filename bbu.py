import time
import simpy
import random

import ltecpricalcs as calc

# BBU - Bruno

#primeiro vc implementa la o BBU pool e BBU
"""
podemos ter uma classe chamada BBU pool ou DC e 
fog, local e central eh uma instacia dessa classe
dai essa classe tem um attr store do simpy
que recebe pacotes destinados a uma BBU
a classe BBU armazena uma lista de BBUs
e havera um processo que retira o pacote da store verifica para qual eh BBU
e faz o put desse pacote no store da BBU
basicamente isso seria a BBU pool

bbu tem o processo que faz get do store e pega o pacote

cada split vai receber um delay fixo de processamento

entao o pacote eh colocado em store de pos processamento da BBU pool
esse store de pos processamento eh passado por parametro para classe BBU

a classe bbu pool tera um processo que retira o pacote do store de pos processamento
e com base na configuracao ira fazer o put desse pacote num store de saida
que pode ser do midhaul, backhaul, etc
"""


#print dict(calc.splits_info) #teste importacao dos calculos

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

class BBU(object):
	def __init__(self,env,oid,post_proc_buffer=None,split=1):
		self.oid = oid
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

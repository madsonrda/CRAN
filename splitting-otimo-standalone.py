#import time
import simpy
#import random
#import math
#import sys
#import logging as log
#import simtime as l
#import pandas as pd
#import numpy as np
#import copy
import ltecpricalcs_quiet as calc
import itertools

####
# Consultando tabela de banda CPRI por splits:
# calc.UL_splits[cpri_option][split_option]['bw']
# ou tabela_BW[cpri_option][split_option]['bw']
####

tabela_BW=calc.UL_splits
uso_banda_RRHs = 0

def print_uso_banda():
	print "USO DE BANDA DAS RRHs: %f Mbps" % uso_banda_RRHs

def set_uso_banda(splits_atuais):
	uso=0
	for cada in splits_atuais:
		uso+= tabela_BW[str(cada[1])][cada[2]]['bw']
	
	global uso_banda_RRHs
	uso_banda_RRHs= uso

def splitting_alto_naive(max_banda, splits_atuais, tabela_BW, high_thold=90, low_thold=50):
	#splits_atuais=[(2,3),(2,4,6),(3,2,1),(4,5,2),(5,7,3)]
	# RRH_ID pos1
	# CPRI_OPTION pos2
	# SPLIT OPTION pos3
	validos = []
	combinatoria=0
	n_validos=0
	print "uso banda RRHs %f" % uso_banda_RRHs
	if (float(uso_banda_RRHs)/max_banda)*100 > high_thold:
		
		splits_possiveis = [1,2,3,4,5,6,7]
		qtd_RRHs = len(splits_atuais)
		args = [splits_possiveis]*qtd_RRHs
		for combination in itertools.product(*args):
			combinatoria+=1
			# aqui sera uma combinacao de split, ex: (1,2,3,4,4)
			soma_banda=0
   			for pos,cada in enumerate(combination):
				soma_banda+=tabela_BW[str(splits_atuais[pos][1])][cada]['bw']
			
			if (float(soma_banda)/max_banda)*100 < high_thold and (float(soma_banda)/max_banda)*100 > low_thold:
				validos.append((combination, soma_banda))
				n_validos+=1
				#print "Combination %s: %f Mbps - OK" % (str(combination),soma_banda)
			#else:
				#print "Combination %s: %f Mbps - ERRO" % (str(combination),soma_banda)
				
		print "\nTotal de %d combinacoes de split possiveis testadas" % combinatoria
		print "Total de %d combinacoes validas" % n_validos
			#print "Combination %s" % str(combination)

		#return validos
	else:
		print "Uso atual nao eh maior do que o limiar superior. Saindo de splitting_alto"

def splitting_alto_bbound(max_banda, splits_atuais, tabela_BW, high_thold=90, low_thold=50):
	#splits_atuais=[(2,3),(2,4,6),(3,2,1),(4,5,2),(5,7,3)]
	# RRH_ID pos1
	# CPRI_OPTION pos2
	# SPLIT OPTION pos3
	"""	1. ACHAR QUAIS BRANCHS NAO PRECISAM SER TESTADOS
			1.1 testar 11111
		2.
	"""
	validos = []
	combinatoria=0
	n_validos=0
	print "uso banda RRHs %f" % uso_banda_RRHs
	if (float(uso_banda_RRHs)/max_banda)*100 > high_thold:
		avoid=None
		qtd_RRHs = len(splits_atuais)
		combinatoria=(1,)*qtd_RRHs




		#for cada in 
		#splits_possiveis = [1,2,3,4,5,6,7]
		
		#args = [splits_possiveis]*qtd_RRHs

		# for combination in itertools.product(*args):
		# 	combinatoria+=1
		# 	# aqui sera uma combinacao de split, ex: (1,2,3,4,4)
		# 	soma_banda=0
		# 	for pos,cada in enumerate(combination):
		# 		soma_banda+=tabela_BW[str(splits_atuais[pos][1])][cada]['bw']
			
		# 	if (float(soma_banda)/max_banda)*100 < high_thold and (float(soma_banda)/max_banda)*100 > low_thold:
		# 		validos.append((combination, soma_banda))
		# 		n_validos+=1
		# 		print "Combination %s: %f Mbps - OK" % (str(combination),soma_banda)
		# 	else:
		# 		print "Combination %s: %f Mbps - ERRO" % (str(combination),soma_banda)
		# print "\nTotal de %d combinacoes de split possiveis testadas" % combinatoria
		# print "Total de %d combinacoes validas" % n_validos
		# return validos
	else:
		print "Uso atual nao eh maior do que o limiar superior. Saindo de splitting_alto"

def splitting_baixo(max_banda, splits_atuais, tabela_BW, high_thold=90, low_thold=50):
	if (uso_banda_RRHs/max_banda) < low_thold:
		pass
	print "Uso atual nao eh menos do que o limiar inferior. Saindo de splitting_baixo"


max_banda=10000
# 5 RRHs ; 1 wavelength 10Gbps
splits_atuais=[(1,2,3),(2,4,6),(3,2,1),(4,5,2),(5,7,3),(5,7,3),(5,7,3),(5,7,3)]
# RRH_ID pos1
# CPRI_OPTION pos2
# SPLIT OPTION pos3

set_uso_banda(splits_atuais)
print_uso_banda()

validos = splitting_alto_naive(max_banda, splits_atuais, tabela_BW)

#### TEMPO DE EXECUCAO ###
# PC do PoP - 1 core AMD A10 PRO-7800B R7
# ALGORITMO NAIVE
# 5 RRHs = ~0.4s
# 6 RRHs = ~1.2s
# 7 RRHs = ~9s
# 8 RRHs = ~67s  #firefox aberto + prints + calculos
# 8 RRHs = ~62s  #+ sem firefox aberto + prints + calculos
# 8 RRHs = ~21s  #+ sem firefox aberto + sem calculos(somente print)
# 8 RRHs = ~26s  #+ sem firefox aberto + com calculos(sem print) <--
# 8 RRHs = ~0.3s #+ sem firefox aberto + sem calculos(sem print)
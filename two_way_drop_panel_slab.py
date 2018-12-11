from numpy import sqrt
from numpy import pi
from numpy import roots
from numpy import zeros
from numpy import interp
from numpy import tanh
from numpy import cosh

class TwoWayDropPanel(TwoWayFlatPlateSlab):
	'''
	# methods to override - usage of self.h
		# calculate_f_i - h should be equivalent h (h_equiv)
		# mass - h should be h_equiv
		# bending moment - h should be h_equiv
		# calculate M_n - h should be h_equiv
		# calculate_strip_I_e - h should be drop panel or mid span
		# calculate_rho_from_As - h should be drop panel or mid span
		# calculate_As_from_rho - h should be drop panel or mid span
		# estimate_As - h should be drop panel or midspan
	# Approach should refactor two way slab so that h is parameter passed for above methods
	# super method needed for
		calculate_avg_strip_I_e
		self.h 
	'''




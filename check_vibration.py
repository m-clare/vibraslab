from numpy import pi, sin, exp, interp, sqrt

__author__     = ['Maryanne Wachter']
__version__    = '0.1'
__status__     = 'Development'
__date__       = 'Dec 5, 2018'

vibration_crit_limits = {'Ordinary workshops': 32000, 'Offices': 16000, 'Computer systems': 8000, 'Residences': 8000,
						 'Operating rooms': 4000, 'Surgery facilities': 4000, 'Bench microscopes 100x': 4000, 'Lab robots': 4000,
						 'Bench microscopes 400x': 2000}

def calculate_f_i(k_1, c_1, l_1, l_2, w_c, f_c, h, nu):
	if col_size > 24:
		k_2 = 2.1
	else:
		k_2 = 1.9
	if w_c >= 90 and w_c <= 160:
		E_c = w_c ** 1.5 * 33 * sqrt(f_c)
	else:
		raise ValueError
	lambda_i_sq = interp(l_1 / l_2, [1.0, 1.5, 2.0], [7.12, 8.92, 9.29])
	mass  = h / 12. * w_c * l_1 * l_2 / 32.2 # lb sec2/ft
	gamma = mass / (l_1 * l_2) # slug / ft2
	f_i = k_2 * lambda_i_sq / (2 * pi * l_1 ** 2.0) * sqrt((k_1 * E_c * h ** 3.0) / (12. * gamma * (1 - nu ** 2.)))
	return f_i

def calculate_mode_scaling(x, y, Lb, Lg, fb, fg):
	if fb <= fg:
		phi = sin(pi * x / Lb) * sin(pi * (y + Lg) / (3 * Lg))
	else:
		phi = sin(pi * (x + Lb) / (3 * Lb)) * sin(pi * y / Lg)
	return phi

def check_sensitive_equip_steel(floor_fn, eff_weight, damping, manufacturer_limit=None, limit_type=None, limit_app=None):
	# steel
	walking_parameters = {'very_slow': {'f_step': 1.25}, 
					  	  'slow': {'f_step': 1.6, 'f_4max': 6.8, 'f_L': 6., 'f_U': 8, 'gamma': 0.10},
					  	  'moderate': {'f_step': 1.85, 'f_4max': 8.0, 'f_L': 7., 'f_U': 9, 'gamma': 0.09},
					  	  'fast': {'f_step': 2.1, 'f_4max': 8.8, 'f_L': 8., 'f_U': 10, 'gamma': 0.08}}

	limit_types = ['generic velocity', 'one-third octave acceleration', 'peak velocity', 'peak acceleration', 
				   'narrowband spectral velocity', 'narrowband spectral acceleration']

	def eqn_6_3a(f_step, f_n, beta, W):
		V_13 = 250e6 / (beta * W * 1000) * f_step ** 2.43 / f_n ** 1.8 * (1 - exp(-2 * pi * beta * f_n / f_step))
		return round(V_13, 0)

	def eqn_6_3b(f_n, beta, gamma, W):
		V_13 = 175e6 / (beta * W * 1000 * sqrt(f_n)) * exp(-gamma * f_n) # Eqn 6-3b
		return round(V_13, 0)

	if not limit_type in limit_types:
		raise NameError
	if manufacturer_limit:
		limit = manufacturer_limit
	else:
		limit = vibration_crit_limits[limit_app]
	if limit_type == 'generic velocity':
		V_13_out = {'beta': damping}
		for speed in walking_parameters:
			# Check if low or high frequency floor
			f_step = walking_parameters[speed]['f_step']
			if 'f_4max' in walking_parameters[speed]:
				f_4max = walking_parameters[speed]['f_4max']
				# slow/moderate/fast
				f_L = walking_parameters[speed]['f_L']
				f_U = walking_parameters[speed]['f_U']
				gamma = walking_parameters[speed]['gamma']
				V_13_f_L = eqn_6_3b(f_L, damping, gamma, eff_weight)
				V_13_f_U = eqn_6_3a(f_step, f_U, damping, eff_weight)
				if floor_fn <= f_L:
					V_13 = eqn_6_3b(floor_fn, damping, gamma, eff_weight)
				elif floor_fn >= f_U:
					V_13 = eqn_6_3a(f_step, floor_fn, damping, eff_weight)
				else: # linear interpolate between equations
					V_13  = round(interp(floor_fn, [f_L, f_U], [V_13_f_L, V_13_f_U]), 0)
			else:
				# very slow
				V_13 = eqn_6_3a(f_step, floor_fn, damping, eff_weight)
			V_13_out[speed] = {}
			V_13_out[speed]['V_13'] = V_13
			if V_13 > limit:
				V_13_out[speed]['crit'] = 'fail'
			else:
				V_13_out[speed]['crit'] = 'pass'
		return V_13_out
	elif limit_type == 'peak acceleration':
		pass
	elif limit_type == 'narrowband spectral velocity':
		pass
	elif limit_type == 'narrowband spectral acceleration':
		pass
	else: 
		raise NameError

def check_sensitive_equip_concrete(floor_fn, delta_p, manufacturer_limit=None, limit_type=None, limit_app=None):
	# concrete
	footfall_impulse_parameters = {'fast': {'F_m': 315., 'f_0': 5.0, 'U_v': 25000, 'steps/min': 100.},
							  	   'moderate': {'F_m': 280., 'f_0': 2.5, 'U_v': 5500, 'steps/min': 75.},
							 	   'slow': {'F_m': 240., 'f_0': 1.4, 'U_v': 1500, 'steps/min': 50.}}

	if manufacturer_limit:
		limit = manufacturer_limit
	else:
		limit = vibration_crit_limits[limit_app]
	if limit_type == 'maximum velocity':
		V_out = {}
		for pace in footfall_impulse_parameters:
			parameters = footfall_impulse_parameters[pace]
			f_0 = parameters['f_0']
			if floor_fn / f_0 > 0.5: # should be >> 0.5
				U_v = parameters['U_v']
				V = delta_p * U_v / floor_fn
			else:
				raise ValueError
			V_out[pace] = {}
			V_out[pace]['V'] = round(V * 1e6, 0) # provide in micro-in/sec (mips)
			if V > limit:
				V_out[pace]['crit'] = 'fail'
			else:
				V_out[pace]['crit'] = 'pass'
		return V_out

if __name__ == "__main__":
	# fn = [4.34,4.45,4.55, 4.64, 4.74, 4.83, 4.93, 5.02, 5.1, 5.19, 5.28, 5.36, 5.45, 5.53, 5.61, 5.69, 5.77, 5.84, 5.92, 6.0]
	fn = [3.66,3.75,3.83,3.92,4.0,4.08,4.15,4.23,4.31,4.38,4.45,4.52, 4.59, 4.66, 4.73,4.8,4.86,4.93,4.99,5.06, 5.12, 5.18, 5.24, 5.3, 5.36, 5.42, 5.48, 5.54, 5.60, 5.65, 5.71, 5.76, 5.82, 5.87]
	W = 186.0
	beta = 0.04
	for freq in fn:
		out = (check_sensitive_equip_steel(freq, W, beta, manufacturer_limit=6000, limit_type='generic velocity'))
		print(out['very_slow']['V_13'])
	pass

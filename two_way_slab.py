from numpy import sqrt
from numpy import pi
from numpy import roots
from numpy import zeros
from numpy import interp
from numpy import tanh
from numpy import cosh

def check_R(f_c, R):
	table_A5a = {5000: {30: 0.0005, 60: 0.0010, 89: 0.0015, 118: 0.0020, 147: 0.0025, 
						176: 0.003, 205: 0.0035, 233: 0.004, 261: 0.0045, 289: 0.0050, 
						317: 0.0055, 345: 0.0060, 372: 0.0065, 399: 0.0070, 426: 0.0075}}
	# interpolate between values
	rho = interp(R, [30, 60, 89, 118, 147, 176, 205, 233, 261, 289, 317, 345, 372, 399, 426],
					[0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.0045, 0.005,
					 0.0055, 0.0060, 0.0065, 0.0070, 0.0075])
	return rho

class TwoWayFlatPlateSlab(object):
	'''
	Calculate the vibration characteristics (fundamental frequency) of a 2 way flat slab for interior/exterior bays only without beams
	between interior supports (no edge beam)
	Note: This assumes that the Direct Design Criteria by ACI have been fulfilled
	'''

	def __init__(self, l_1, l_2, h, f_c, f_y, w_c, nu, col_size, bay, loading=None, reinforcement=None, floor_type='rc'):
		self.l_1 = l_1
		self.l_2 = l_2
		self.h = h
		self.f_c = f_c
		self.c_1 = col_size['c1']
		self.c_2 = col_size['c2']
		self.bay = bay or {}
		self.l_ratio = self.l_1 / self.l_2
		self.f_y = f_y
		self.w_c = w_c
		self.nu  = nu # Poisson's ratio
		self.loading = loading or {}
		self.reinforcement = reinforcement or {}
		self.phi = 0.9 # want tension controlled section

		# set reinforcement ratios (if they exist)
		self.rho = {}
		try:
			if self.reinforcement['type'] == 'rho':
				self.rho['l_1'] = self.reinforcement['l_1']
				self.rho['l_2'] = self.reinforcement['l_2']
		except KeyError:
			pass

		# set modulus of elasticity
		if w_c >= 90 and w_c <= 160:
			self.E_c = w_c ** 1.5 * 33 * sqrt(f_c)
		else:
			raise ValueError

		if floor_type == 'rc':
			self.E_c *= 1.2

		if w_c == 150.0:
			self.lambda_cw = 1.0
		elif w_c < 150.0:
			self.lambda_cw = 0.75
		else:
			raise NotImplementedError

		self.n = 29000000 / self.E_c
		self.f_r = 4.5 * self.lambda_cw * sqrt(f_c)

		# set strip widths
		# WHAT DOES THIS MEAN FOR EXTERIOR STRIPS?
		self.strips = {'l_1': {}, 'l_2': {}}
		col_width   = min(0.25 * self.l_1, 0.25 * self.l_2) * 2.
		for bay, value in self.bay.items():
			self.strips[bay]['column'] = col_width 
		self.strips['l_1']['middle'] = self.l_2 - col_width 
		self.strips['l_2']['middle'] = self.l_1 - col_width 

		# set mass / weight
		sdl = self.loading['sdl'] or 0.0
		ll  = self.loading['ll_vib'] or 0.0
		self.mass = ((self.h / 12. * self.w_c + sdl + ll) * self.l_1 * self.l_2) / 32.2 # lb sec2/ft
		self.weight = self.mass * 32.2 / 1000. # kips

		# Calculate maximum reinforcement ratio
		# Find beta_1
		if self.f_c <= 4000:
			beta_1 = 0.85
		elif self.f_c == 5000:
			beta_1 = 0.8
		elif self.f_c == 6000:
			beta_1 = 0.75
		elif self.f_c == 7000:
			beta_1 = 0.7
		elif self.f_c >= 8000:
			beta_1 = 0.65
		epsilon_u = 0.003
		self.rho_max = 0.85 * beta_1 * f_c / f_y * epsilon_u / (epsilon_u + 0.005)

		# Set bending moments
		self.bending_moments = {'l_1': {}, 'l_2': {}}
		for span in self.bending_moments:
			self.bending_moments[span] = self.calculate_bending_moments(span)

	def calculate_Mn(self, strip_type, location, bay, M_0):
		'''
		Calculates design moment based on continuous interior span
		Needs to be generalized for all span conditions..., find a more efficient way of representing this?
		'''
		if bay == 'interior':
			if strip_type == 'middle' and location == 'p':
				p_moment    = 0.35
				dist_factor = 0.4
			elif strip_type == 'middle' and location == 'n1':
				p_moment    = 0.65
				dist_factor = 0.25
			elif strip_type == 'middle' and location == 'n2':
				p_moment    = 0.65
				dist_factor = 0.25
			elif strip_type == 'column' and location == 'p':
				p_moment    = 0.35
				dist_factor = 0.6
			elif strip_type == 'column' and location == 'n1':
				p_moment    = 0.65
				dist_factor = 0.75
			elif strip_type == 'column' and location == 'n2':
				p_moment    = 0.65
				dist_factor = 0.75
			else:
				raise NameError
		elif bay == 'exterior':
			if strip_type == 'middle' and location == 'p':
				p_moment    = 0.52
				dist_factor = 0.4
			elif strip_type == 'middle' and location == 'n1': # n1 is exterior Neg Mu
				p_moment    = 0.26
				dist_factor = 0.0
			elif strip_type == 'middle' and location == 'n2': # n2 is interior Neg Mu
				p_moment    = 0.7
				dist_factor = 0.25
			elif strip_type == 'column' and location == 'p':
				p_moment    = 0.52
				dist_factor = 0.6
			elif strip_type == 'column' and location == 'n1':
				p_moment    = 0.26
				dist_factor = 1.0
			elif strip_type == 'column' and location == 'n2':
				p_moment    = 0.7
				dist_factor = 0.75
			else:
				raise NameError
		else:
			raise NameError
		return round(p_moment * dist_factor * M_0 * 0.001, 1)

	def calculate_bending_moments(self, span):

		def factor_moment(dead, live):
			return round(1.2 * dead + 1.6 * live, 1)

		span_types = ['l_1', 'l_2']
		if span not in span_types:
			raise ValueError("Invalid span type. Expected one of: %s" % span_types)
		if span == 'l_1':
			col_dim = self.c_1
		if span == 'l_2':
			col_dim = self.c_2
		w_sdl = self.loading['sdl']
		w_ll_design  = self.loading['ll_design']
		w_dl = self.w_c * self.h / 12. + w_sdl
		w_ll = w_ll_design
		if span == 'l_1':
			l_trans = self.l_2
			l_span = self.l_1
		if span == 'l_2':
			l_trans = self.l_1
			l_span = self.l_2
		M_0_dl = w_dl * l_trans * (l_span - col_dim / 12.) ** 2.0 / 8.
		M_0_ll = w_ll * l_trans * (l_span- col_dim / 12.) ** 2.0 / 8.
		load_out = {'service': {'column': {'n1': {}, 'n2': {}, 'p': {}}, 
								'middle': {'n1': {}, 'n2': {}, 'p': {}}},
					'factored': {'column': {'n1': 0.0, 'n2': 0.0, 'p': 0.0}, 
								'middle':  {'n1': 0.0, 'n2': 0.0, 'p': 0.0}}}
		service = load_out['service']
		strip_types = ['column', 'middle']
		moments = ['p', 'n1', 'n2']
		load_type = ['dl', 'll']
		for strip in strip_types:
			for moment in moments:
				for load in load_type:
					if load == 'dl':
						service[strip][moment][load] = self.calculate_Mn(strip, moment, self.bay[span], M_0_dl)
					if load == 'll':
						service[strip][moment][load] = self.calculate_Mn(strip, moment, self.bay[span], M_0_ll)
		# Factored moments
		factored = load_out['factored']
		for strip in strip_types:
			for moment in moments:
				factored[strip][moment] = factor_moment(service[strip][moment]['dl'], service[strip][moment]['ll'])
		return load_out

	def calculate_flexural_reinforcement(self, bending_moment, cover=0.75, bar_guess=0.75):
		raise NotImplementedError("Not implemented (yet)! Use another program to design slab for flexure for a tension controlled section")

	def calculate_strip_I_g(self, strip_width):
		'''
		Calculates gross moment of inertia neglecting rebar
		'''
		return 1 / 12. * strip_width * 12 * self.h ** 3.0

	def calculate_strip_I_e(self, strip_width, M_a, As, d=None):
		# calculate I_g 
		I_g = self.calculate_strip_I_g(strip_width)
		y_t = self.h / 2.0
		a_j = strip_width * 12 / (self.n * As)
		# estimate d if not provided
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = self.h - cover - 0.5 * bar_guess
		p    = zeros(3)
		p[0] = strip_width * 12 * 0.5
		p[1] = self.n * As
		p[2] = -self.n * As * d
		kd   = max(roots(p))
		if kd < 0.0:
			raise ValueError
		I_cr = strip_width * 12 * kd ** 3.0 / 3 + self.n * As * (d - kd) ** 2.0
		I_cr = min(I_cr, I_g)
		M_cr = self.f_r * I_g / y_t * 1 / 12000. # ft-kips
		if M_a == 0.0 or M_cr / M_a > 1.0:
			I_e = I_g
		else: 		
			M_ratio = M_cr / M_a
			I_e = I_cr / (1 - (M_ratio ** 2.0 * (1 - I_cr / I_g)))
		return round(I_e, 0)

	def calculate_rho_from_As(self, strip_width, As, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = self.h - cover - 0.5 * bar_guess
		return As / (strip_width * 12 * d)

	def calculate_As_from_rho(self, strip_width, rho, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = self.h - cover - 0.5 * bar_guess
		return rho * strip_width * 12 * d

	def estimate_As(self, strip_width, M_u, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = self.h - cover - 0.5 * bar_guess
		As = max(M_u * 12000 / d * 0.85 / 54000., 0.0025 * strip_width * 12. * d ) # still need check?
		Mu_ft = M_u / strip_width
		R  = Mu_ft * 12000 / (self.phi * 12 * d ** 2.0)
		rho_R = check_R(self.f_c, R)
		# check As against min and max
		if self.f_y < 60000:
			As_min = 0.002 * strip_width * 12 * self.h
		else: # THIS NEEDS TO BE CHECKED...
			As_min = max(0.0018 * 60000 / self.f_y * strip_width * 12 * self.h, 0.0014 * strip_width * 12 * self.h)
		if As < As_min:
			As = As_min
			print('As is from As_min')
		As_max = self.calculate_As_from_rho(strip_width, self.rho_max, d=None)
		if As > As_max:
			print('As > As_max')
			As = As_max
		rho = self.calculate_rho_from_As(strip_width, As)
		print('rho_max:', self.rho_max, 'rho_R:', rho_R, 'rho_est:', rho)
		return round(As, 2) 

	def calculate_avg_strip_I_e(self, span, strip_type):
		strip_options = ['column', 'middle']
		locations = ['p', 'n1', 'n2']
		I_e_map = {'p': 'I_m', 'n1': 'I_e1', 'n2': 'I_e2'}
		if strip_type not in strip_options:
			raise NameError
		I_eff = {}
		for location in locations:
			bm = sum(self.bending_moments[span]['service'][strip_type][location].values())
			if 'type' not in self.reinforcement or self.reinforcement['type'] == 'estimated':
				M_u   = self.bending_moments[span]['factored'][strip_type][location]
				reinf = self.estimate_As(self.strips[span][strip_type], M_u)
				self.reinforcement['type'] = 'estimated' 
			elif self.reinforcement['type'] == 'As':
				reinf = self.reinforcement[span][strip_type][location]
			elif self.reinforcement['type'] == 'rho':
				strip_width = self.strips[span][strip_type]
				reinf = self.calculate_As_from_rho(strip_width, self.reinforcement[span][strip_type][location])
			I_e = self.calculate_strip_I_e(self.strips[span][strip_type], bm, reinf)
			I_eff[I_e_map[location]] = I_e
		I_e  = 0.7 * I_eff['I_m'] + 0.15 * (I_eff['I_e1'] + I_eff['I_e2']) # Eqn 4.19
		return I_e

	def calculate_panel_I_e(self):
		I_e_csx = self.calculate_avg_strip_I_e('l_1', 'column')
		I_e_csy = self.calculate_avg_strip_I_e('l_2', 'column')
		I_e_msx = self.calculate_avg_strip_I_e('l_1', 'middle')
		I_e_msy = self.calculate_avg_strip_I_e('l_2', 'middle')
		if self.l_ratio == 1.0: # square
			self.I_e = I_e_csx + I_e_msy
		else: # rectangular
			self.I_e = ((I_e_csx + I_e_msy) + (I_e_csy + I_e_msx)) / 2.0
		return self.I_e

	def calculate_panel_I_g(self):
		I_g_csx = self.calculate_strip_I_g(self.strips['l_1']['column'])
		I_g_csy = self.calculate_strip_I_g(self.strips['l_2']['column'])
		I_g_msx = self.calculate_strip_I_g(self.strips['l_1']['middle'])
		I_g_msy = self.calculate_strip_I_g(self.strips['l_2']['middle'])
		self.I_g = ((I_g_csx + I_g_msy) + (I_g_csy + I_g_msx)) / 2.0
		return self.I_g

	def calculate_k_1(self):
		# accounts for level of cracking
		# if self.rho <= 0.01:
		#  low reinforcement ratio (should include temp/shrink reinforcement)
		I_e = self.calculate_panel_I_e()
		I_g = self.calculate_panel_I_g()
		self.k_1 = I_e / I_g
		return self.k_1

	def calculate_f_i(self):
		# calculate k_1 - accounts for level of cracking
		k_1 = self.calculate_k_1()
		# calculate k_2
		col_size = max(self.c_1, self.c_2)
		if col_size > 24:
			k_2 = 2.1
		else:
			k_2 = 1.9
		# calculate lambda_i_sq - allow linear interpolation
		lambda_i_sq = interp(self.l_ratio, [1.0, 1.5, 2.0], [7.12, 8.92, 9.29])
		gamma = self.mass / (self.l_1 * self.l_2) # slug / ft2
		self.f_i = k_2 * lambda_i_sq / (2 * pi * self.l_1 ** 2.0) * \
				   (k_1 * self.E_c * 144 * (self.h / 12.) ** 3.0 / (12 * gamma * (1 - self.nu ** 2.0))) ** 0.5
		return round(self.f_i, 2)

	def calculate_delta_p(self):
		# Timoshenko plate theory, maximum deflection of floor system subjected to concentrated unit load
		# assumes simply supported edges
		k_1 = self.calculate_k_1()
		const_p = 6 * (self.l_2 * 12.) ** 2. * (1 - self.nu ** 2.) / (k_1 * self.E_c * self.h ** 3. * pi ** 3.)
		tol = 1.0
		i = 1
		sum_p = 0.
		m = 1
		while tol > 0.001:
			old_sum = sum_p
			alpha_m = m * pi / 2 * self.l_ratio
			sum_p += 1 / m ** 3. * (tanh(alpha_m) - alpha_m / (cosh(alpha_m)) ** 2.)
			tol = abs(sum_p - old_sum)
			m += 2
		self.delta_p = const_p * sum_p
		return self.delta_p

	def to_json(self, name='two_way_slab'):
		with open(name + '.json', 'w') as fh:
			json.dump(self.__dict__, fh)

	def from_json(self, fp):
		raise NotImplementedError

if __name__ == "__main__":
	import json
	# l_1 must be longer span, l_2 must be shorter span
	# Example 5.3 CRSI Design Guide
	# d5_3 = {'loading': {'sdl': 20., 'll_design': 65., 'll_vib': 11.},
	# 		'reinf': {'l_1': {'column': {'n': 5.39, 'p': 2.31}, 'middle': {'n': 2.05, 'p': 2.05}},
	# 		      	  'l_2': {'column': {'n': 4.15, 'p': 2.05}, 'middle': {'n': 3.08, 'p': 3.08}},
	# 		      	  'type': 'As'},
	# 		 'l_1': 25., 'l_2': 20., 'h': 9.5, 'f_c': 4000, 'f_y': 60000, 'w_c': 150, 'nu': 0.2, 
	# 		 'col_size': {'c1': 22., 'c2': 22.}, 'bay': {'l_1': 'interior', 'l_2': 'interior'}}
	# ex5_3 = TwoWayFlatPlateSlab(l_1=d5_3['l_1'], l_2=d5_3['l_2'], h=d5_3['h'], 
	# 							f_c=d5_3['f_c'], f_y=d5_3['f_y'], w_c=d5_3['w_c'], nu=d5_3['nu'], col_size=d5_3['col_size'], 
	# 	 				        bay=d5_3['bay'], loading=d5_3['loading'], reinforcement=d5_3['reinf'])
	# print(d5_3['l_1'], ex5_3.calculate_bending_moments('l_1')['factored'])
	# print(d5_3['l_2'], ex5_3.calculate_bending_moments('l_2')['factored'])
	# print(ex5_3.calculate_f_i())
	ssm_d = {'loading': {'sdl': 21., 'll_design': 125., 'll_vib': 11.},
			'reinf': {},
			 'l_1': 35., 'l_2': 22., 'h': 11, 'f_c': 5000, 'f_y': 60000, 'w_c': 145, 'nu': 0.2, 
			 'col_size': {'c1': 21., 'c2': 21.}, 'bay': {'l_1': 'exterior', 'l_2': 'interior'}}
	ssm_ex = TwoWayFlatPlateSlab(l_1=ssm_d['l_1'], l_2=ssm_d['l_2'], h=ssm_d['h'], 
								f_c=ssm_d['f_c'], f_y=ssm_d['f_y'], w_c=ssm_d['w_c'], nu=ssm_d['nu'], col_size=ssm_d['col_size'], 
		 				        bay=ssm_d['bay'], loading=ssm_d['loading'], reinforcement=ssm_d['reinf'])
	print(ssm_ex.calculate_f_i())
	print(ssm_ex.k_1)
	print(ssm_ex.weight)
	print(ssm_ex.I_e)
	# s = json.dumps(ex5_3.__dict__)
	# ex5_3.to_json()

	# with open('test.json', 'w') as fh:
	# 	json.dump(ex5_3.__dict__, fh)
	# print(ex5_3.calculate_bending_moments('l_1'))
	# print(ex5_3.calculate_bending_moments('l_2'))
	# print(ex5_3.mass)
	# print(ex5_3.I_e)
	# Parameters to experiment with:
	# Slab reinforcment (implement as reinforcement ratio rather than As)
	# Column size
	# Stiffness variation between column and middle strip (i.e. reinforcement)
	# Creep/Post Tensioning considerations
	# Drop panel estimation of equivalent slab based on voids?
	# LL should be 80
	# Check LL against AISC comparison




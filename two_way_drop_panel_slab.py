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
	# interpolate between values # Table A5a
	rho = interp(R, [30, 60, 89, 118, 147, 176, 205, 233, 261, 289, 317, 345, 372, 399, 426, 453, 
					 479, 506, 532, 558, 583, 609, 634, 659, 684, 708, 733, 757, 781, 805, 828, 852, 875, 898, 920],
					[0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.0045, 0.005,
					 0.0055, 0.0060, 0.0065, 0.0070, 0.0075, 0.0080, 0.0085, 0.0090, 0.0095, 0.010, 
					 0.0105, 0.0110, 0.0115, 0.0120, 0.0125, 0.0130, 0.0135, 0.0140, 0.0145, 0.0150, 
					 0.0155, 0.016, 0.0165, 0.017, 0.0175])
	return rho

class TwoWayDropPanel(object):

	def __init__(self, l_1, l_2, h, f_c, f_y, w_c, nu, col_size, bay, loading=None, reinforcement=None, floor_type='rc'):
		
		self.l_1 = l_1
		self.l_2 = l_2
		self.h = h or {}
		self.h_equiv = self.h['h_equiv']
		self.f_c = f_c
		self.c1 = col_size['c1']
		self.c2 = col_size['c2']
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

		if not self.rho:
			self.rho = {'l_1': {'column': {}, 'middle': {}},
						'l_2': {'column': {}, 'middle': {}}}

		# set modulus of elasticity
		if w_c >= 90 and w_c <= 160:
			self.E_c = w_c ** 1.5 * 33 * sqrt(f_c)
		else:
			print(w_c)
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
		self.f_r = 4.5 * self.lambda_cw * sqrt(f_c) # CRSI p.4-6

		# set strip widths
		self.strips = {'l_1': {}, 'l_2': {}}
		col_width   = min(0.25 * self.l_1, 0.25 * self.l_2) * 2.
		for bay, value in self.bay.items():
			self.strips[bay]['column'] = col_width 
		self.strips['l_1']['middle'] = self.l_2 - col_width 
		self.strips['l_2']['middle'] = self.l_1 - col_width 

		# set mass / weight
		sdl = self.loading['sdl'] or 0.0
		ll  = self.loading['ll_vib'] or 0.0
		self.mass = ((self.h_equiv / 12. * self.w_c + sdl + ll) * self.l_1 * self.l_2) / 32.2 # lb sec2/ft
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
			self.bending_moments[span] = self.calculate_bending_moments(span, self.h_equiv)

	def calculate_strip_moment(self, strip_type, location, bay, M_0):
		'''
		Calculates design moment based on continuous interior span
		Needs to be generalized for all span conditions where Direct Design Method is applicable....
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

	def calculate_bending_moments(self, span, h):

		def factor_moment(dead, live):
			return round(1.2 * dead + 1.6 * live, 1)

		span_types = ['l_1', 'l_2']
		if span not in span_types:
			raise ValueError("Invalid span type. Expected one of: %s" % span_types)
		if span == 'l_1':
			col_dim = self.c1
		if span == 'l_2':
			col_dim = self.c2
		w_sdl = self.loading['sdl']
		w_ll_design  = self.loading['ll_design']
		w_dl = self.w_c * h / 12. + w_sdl
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
						service[strip][moment][load] = self.calculate_strip_moment(strip, moment, self.bay[span], M_0_dl)
					if load == 'll':
						service[strip][moment][load] = self.calculate_strip_moment(strip, moment, self.bay[span], M_0_ll)
		# Factored moments
		factored = load_out['factored']
		for strip in strip_types:
			for moment in moments:
				factored[strip][moment] = factor_moment(service[strip][moment]['dl'], service[strip][moment]['ll'])
		return load_out

	def calculate_flexural_reinforcement(self, bending_moment, cover=0.75, bar_guess=0.75):
		raise NotImplementedError("Not implemented (yet)! Use another program to design slab for flexure for a tension controlled section")

	def calculate_Mn(self, strip_width, As, h, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
		a = As * self.f_y / (0.85 * self.f_c * strip_width * 12)
		Mn = As * self.f_y * (d - a / 2.)
		Mn = Mn / 12000.
		return Mn

	def calculate_strip_I_g(self, strip_width, h):
		'''
		Calculates gross moment of inertia neglecting rebar
		'''
		return 1 / 12. * strip_width * 12 * h ** 3.0

	def calculate_strip_I_e(self, strip_width, M_a, As, h, d=None):
		# calculate I_g 
		I_g = self.calculate_strip_I_g(strip_width, h)
		y_t = h / 2.0
		a_j = strip_width * 12 / (self.n * As)
		# estimate d if not provided
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
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
			M_ratio = 1.0
		else: 		
			M_ratio = M_cr / M_a
			I_e = I_cr / (1 - (M_ratio ** 2.0 * (1 - I_cr / I_g)))
		print('fr: ', self.f_r, 'yt: ', y_t, "Mcr: ", M_cr, 'M_cr/M_a: ', M_ratio)
		print("I_g: ", I_g, "I_cr: ", I_cr, "I_e: ", I_e)
		return round(I_e, 0)

	def calculate_rho_from_As(self, strip_width, As, h, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
		return As / (strip_width * 12 * d)

	def calculate_As_from_rho(self, strip_width, rho, h, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
		return rho * strip_width * 12 * d

	def estimate_As(self, strip_width, M_u, h, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
		Mu_ft = M_u / strip_width
		R  = Mu_ft * 12000 / (self.phi * 12 * d ** 2.0)
		rho_R = check_R(self.f_c, R)
		As = rho_R * strip_width * d * 12
		# check As against min and max
		if self.f_y < 60000:
			As_min = 0.002 * strip_width * 12 * h
		else:
			As_min = max(0.0018 * 60000 / self.f_y * strip_width * 12 * h, 0.0014 * strip_width * 12 * h)
		if As < As_min:
			As = As_min
			#print('As is from As_min')
		As_max = self.calculate_As_from_rho(strip_width, self.rho_max, h, d=None)
		if As > As_max:
			raise ValueError('As > As_max')
		rho = self.calculate_rho_from_As(strip_width, As, h)
		M_n  = self.calculate_Mn(strip_width, As, h)
		return round(As, 2) 


	def calculate_panel_I_e(self):
		I_e_csx = self.calculate_avg_strip_I_e('l_1', 'column')
		I_e_csy = self.calculate_avg_strip_I_e('l_2', 'column')
		I_e_msx = self.calculate_avg_strip_I_e('l_1', 'middle')
		I_e_msy = self.calculate_avg_strip_I_e('l_2', 'middle')
		self.I_e = ((I_e_csx + I_e_msy) + (I_e_csy + I_e_msx)) / 2.0
		return self.I_e

	def calculate_panel_I_g(self):
		# I_g_csx = self.calculate_strip_I_g(self.strips['l_1']['column'], self.h_equiv)
		# I_g_csy = self.calculate_strip_I_g(self.strips['l_2']['column'], self.h_equiv)
		# I_g_msx = self.calculate_strip_I_g(self.strips['l_1']['middle'], self.h_equiv)
		# I_g_msy = self.calculate_strip_I_g(self.strips['l_2']['middle'], self.h_equiv)
		# test = ((I_g_csx + I_g_msy) + (I_g_csy + I_g_msx)) / 2.0
		I_g_csx = self.calculate_avg_strip_I_g('l_1', 'column')
		I_g_csy = self.calculate_avg_strip_I_g('l_2', 'column')
		I_g_msx = self.calculate_avg_strip_I_g('l_1', 'middle')
		I_g_msy = self.calculate_avg_strip_I_g('l_2', 'middle')
		self.I_g = ((I_g_csx + I_g_msy) + (I_g_csy + I_g_msx)) / 2.0
		# print("Ig: ", self.I_g, test)
		return self.I_g

	def calculate_avg_strip_I_e(self, span, strip_type):
		strip_options = ['column', 'middle']
		locations = ['p', 'n1', 'n2']
		I_e_map = {'p': 'I_m', 'n1': 'I_e1', 'n2': 'I_e2'}
		h_map = {'p': self.h[span][strip_type]['p'], 'n1': self.h[span][strip_type]['n1'], 'n2': self.h[span][strip_type]['n2']}
		if strip_type not in strip_options:
			raise NameError
		I_eff = {}
		for location in locations:
			h_eff = h_map[location]
			strip_width = self.strips[span][strip_type]
			bm = sum(self.bending_moments[span]['service'][strip_type][location].values())
			if 'type' not in self.reinforcement or self.reinforcement['type'] == 'estimated':
				M_u   = self.bending_moments[span]['factored'][strip_type][location]
				As = self.estimate_As(self.strips[span][strip_type], M_u, h_eff)
				self.reinforcement['type'] = 'estimated' 
			elif self.reinforcement['type'] == 'As':
				As = self.reinforcement[span][strip_type][location]
			elif self.reinforcement['type'] == 'rho':	
				As = self.calculate_As_from_rho(strip_width, self.reinforcement[span][strip_type][location], h_eff)
			self.rho[span][strip_type][location] = round(self.calculate_rho_from_As(strip_width, As, h_eff), 5)
			print(span, strip_type, location)
			I_e = self.calculate_strip_I_e(strip_width, bm, As, h_eff)
			# print(I_e)
			print()
			I_eff[I_e_map[location]] = I_e

		I_e  = 0.7 * I_eff['I_m'] + 0.15 * (I_eff['I_e1'] + I_eff['I_e2']) # Eqn 4.19
		return I_e

	def calculate_avg_strip_I_g(self, span, strip_type):
		I_m = self.calculate_strip_I_g(self.strips[span][strip_type], self.h[span][strip_type]['p'])
		I_e1 = self.calculate_strip_I_g(self.strips[span][strip_type], self.h[span][strip_type]['n1'])
		I_e2 = self.calculate_strip_I_g(self.strips[span][strip_type], self.h[span][strip_type]['n2'])
		I_g = 0.7 * I_m + 0.15 * (I_e1 + I_e2)
		return I_g

	def calculate_k_1(self):
		# accounts for level of cracking
		#  low reinforcement ratio (should include temp/shrink reinforcement)
		I_e = self.calculate_panel_I_e()
		I_g = self.calculate_panel_I_g()
		self.k_1 = I_e / I_g
		return self.k_1

	def calculate_f_i(self):
		k_1 = self.calculate_k_1()
		# calculate k_2
		col_size = max(self.c1, self.c2)
		if col_size > 24:
			k_2 = 2.1
		else:
			k_2 = 1.9
		# calculate lambda_i_sq - allow linear interpolation
		lambda_i_sq = interp(self.l_ratio, [1.0, 1.5, 2.0], [7.12, 8.92, 9.29])
		print(lambda_i_sq)
		gamma = self.mass / (self.l_1 * self.l_2) # slug / ft2
		self.f_i = k_2 * lambda_i_sq / (2 * pi * self.l_1 ** 2.0) * \
				   (k_1 * self.E_c * 144 * (self.h_equiv / 12.) ** 3.0 / (12 * gamma * (1 - self.nu ** 2.0))) ** 0.5
		return round(self.f_i, 2)

	def to_json(self, name='two_way_slab'):
		with open(name + '.json', 'w') as fh:
			json.dump(self.__dict__, fh)

	def from_json(self, fp):
		raise NotImplementedError


	# overwrite calculate_avg_strip_I_e method
	# since it requires multiple mapping (both location)
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
		calculate_f_i
		FIX THIS WHEN YOU HAVE TIME... should not replicate so much code :(
	'''

if __name__ == "__main__":
	import json

	# h = {'l_1': {'column': {'p': 12., 'n1': 12., 'n2': 12.}, 'middle': {'p': 12., 'n1': 12., 'n2': 12.}},
		 # 'l_2': {'column': {'p': 12., 'n1': 12., 'n2': 12.}, 'middle': {'p': 12., 'n1': 12., 'n2': 12.}}, 'h_equiv': 12}
	h = {'l_1': {'column': {'p': 14., 'n1': 17.5, 'n2': 17.5}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}},
		 'l_2': {'column': {'p': 14., 'n1': 17.5, 'n2': 17.5}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}}, 'h_equiv': 15.167}
	# h = {'l_1': {'column': {'p': 14., 'n1': 17., 'n2': 17.}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}},
		 # 'l_2': {'column': {'p': 14., 'n1': 17., 'n2': 17.}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}}, 'h_equiv': 15.}
	# h = {'l_1': {'p': 14.5, 'n1': 14.5, 'n2': 14.5},
	# 	 'l_2': {'p': 14.5, 'n1': 14.5, 'n2': 14.5}, 'h_equiv': 14.5}
	d5_3 = {'loading': {'sdl': 0., 'll_design': 80., 'll_vib': 11.},
				 'l_1': 34., 'l_2': 34., 'f_c': 5000, 'f_y': 60000, 'w_c': 150, 'nu': 0.2, 
			 	 'col_size': {'c1': 28., 'c2': 28.}, 'bay': {'l_1': 'exterior', 'l_2': 'interior'}}
	slab_test = TwoWayDropPanel(l_1=d5_3['l_1'], l_2=d5_3['l_2'], h=h, 
								f_c=d5_3['f_c'], f_y=d5_3['f_y'], w_c=d5_3['w_c'], nu=d5_3['nu'], col_size=d5_3['col_size'], 
		 				        bay=d5_3['bay'], loading=d5_3['loading'])
	# print(slab_test.l_1, slab_test.calculate_bending_moments('l_2', slab_test.h_equiv))
	print(slab_test.calculate_f_i())
	print(slab_test.k_1)
	print(slab_test.f_r)
	print(slab_test.I_g)
	print(slab_test.rho)
	# d5_3 = {'loading': {'sdl': 20., 'll_design': 65., 'll_vib': 11.},
	# 		'reinf': {'l_1': {'column': {'n1': 5.39, 'n2': 5.39, 'p': 2.31}, 'middle': {'n1': 2.05, 'n2': 2.05, 'p': 2.05}},
	# 		      	  'l_2': {'column': {'n1': 4.15, 'n2': 4.15, 'p': 2.05}, 'middle': {'n1': 3.08, 'n2': 3.08, 'p': 3.08}},
	# 		      	  'type': 'As'},
	# 		 'l_1': 25., 'l_2': 20., 'h': 9.5, 'f_c': 4000, 'f_y': 60000, 'w_c': 150, 'nu': 0.2, 
	# 		 'col_size': {'c1': 22., 'c2': 22.}, 'bay': {'l_1': 'interior', 'l_2': 'interior'}}
	# ex5_3 = TwoWayDropPanel(l_1=d5_3['l_1'], l_2=d5_3['l_2'], h=h, 
	# 							f_c=d5_3['f_c'], f_y=d5_3['f_y'], w_c=d5_3['w_c'], nu=d5_3['nu'], col_size=d5_3['col_size'], 
	# 	 				        bay=d5_3['bay'], loading=d5_3['loading'], reinforcement=d5_3['reinf'])
	# print(d5_3['l_1'], ex5_3.calculate_bending_moments('l_1', d5_3['h'])['factored'])
	# print(d5_3['l_2'], ex5_3.calculate_bending_moments('l_2', d5_3['h'])['factored'])
	# print(ex5_3.calculate_f_i())
	# print(ex5_3.rho)

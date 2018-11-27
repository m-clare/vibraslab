from numpy import sqrt, pi, roots, array, shape, zeros, interp, tanh, cosh

class TwoWayFlatPlateSlab(object):
	'''
	NOTE THIS IS ONLY FOR INTERIOR BAY CURRENTLY WITH CONTINUOUS SPANS
	'''

	def __init__(self, l_1, l_2, h, f_c, f_y, w_c, nu, col_size, loading=None, reinforcement=None, floor_type='rc'):
		self.l_1 = l_1
		self.l_2 = l_2
		self.h = h
		self.f_c = f_c
		self.c_1 = col_size['c1']
		self.c_2 = col_size['c2']
		self.l_ratio = self.l_1 / self.l_2
		self.f_y = f_y
		self.w_c = w_c
		self.nu  = nu # Poisson's ratio
		self.loading = loading or {}
		self.reinforcement = reinforcement or {}

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
		self.strips = {'l_1': {}, 'l_2': {}}
		col_width   = min(0.25 * self.l_1, 0.25 * self.l_2) * 2.
		self.strips['l_1']['column'] = col_width 
		self.strips['l_2']['column'] = col_width 
		self.strips['l_1']['middle'] = self.l_2 - col_width 
		self.strips['l_2']['middle'] = self.l_1 - col_width 

		# set mass / weight
		sdl = self.loading['sdl'] or 0.0
		ll  = self.loading['ll_vib'] or 0.0
		self.mass = ((self.h / 12. * self.w_c + sdl + ll) * self.l_1 * self.l_2) / 32.2 # lb sec2/ft
		self.weight = self.mass * 32.2 # lb

	def calculate_Mn(self, strip_type, location, M_0):
		'''
		Calculates design moment based on continuous interior span
		'''
		if strip_type == 'middle' and location == 'p':
			p_moment    = 0.35
			dist_factor = 0.4
		elif strip_type == 'middle' and location == 'n':
			p_moment    = 0.65
			dist_factor = 0.25
		elif strip_type == 'column' and location == 'p':
			p_moment    = 0.35
			dist_factor = 0.6
		elif strip_type == 'column' and location == 'n':
			p_moment    = 0.65
			dist_factor = 0.75
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
		load_out = {'service': {'column': {'n': {}, 'p': {}}, 
								'middle': {'n': {}, 'p': {}}},
					'factored': {'column': {'n': 0.0, 'p': 0.0}, 
								'middle':  {'n': 0.0, 'p': 0.0}}}
		service = load_out['service']
		strip_types = ['column', 'middle']
		moments = ['p', 'n']
		load_type = ['dl', 'll']
		for strip in strip_types:
			for moment in moments:
				for load in load_type:
					if load == 'dl':
						service[strip][moment][load] = self.calculate_Mn(strip, moment, M_0_dl)
					if load == 'll':
						service[strip][moment][load] = self.calculate_Mn(strip, moment, M_0_ll)
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

	def calculate_strip_I_e(self, strip_width, M_n, As, d=None):
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
		kd   = max(roots(p)) # error handling??
		I_cr = strip_width * 12 * kd ** 3.0 / 3 + self.n * As * (d - kd) ** 2.0
		I_cr = min(I_cr, I_g)
		M_cr = self.f_r * I_g / y_t * 1 / 12000. # ft-kips
		M_ratio = M_cr / M_n
		if M_ratio > 1.0:
			I_e = I_g # uncracked section
		else:
			I_e = I_cr / (1 - (M_ratio ** 2.0 * (1 - I_cr / I_g)))
		return round(I_e, 0)

	def calculate_rho(self, strip_width, As, d=None):
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = self.h - cover - 0.5 * bar_guess
		return As / (strip_width * d)

	def calculate_avg_strip_I_e(self, span, strip_type):
		strip_options = ['column', 'middle']
		if strip_type not in strip_options:
			raise ValueError
		bending_moment = self.calculate_bending_moments(span)
		bm_p = sum(bending_moment['service'][strip_type]['p'].values())
		bm_n = sum(bending_moment['service'][strip_type]['n'].values())
		reinf_p = self.reinforcement[span][strip_type]['p']
		reinf_n = self.reinforcement[span][strip_type]['n']
		I_m  = self.calculate_strip_I_e(self.strips[span][strip_type], bm_p, reinf_p)
		I_e1 = self.calculate_strip_I_e(self.strips[span][strip_type], bm_n, reinf_n)
		I_e2 = I_e1 # when would this differ?
		I_e  = 0.7 * I_m + 0.15 * (I_e1 + I_e2) # Eqn 4.19
		return I_e

	def calculate_panel_I_e(self):
		if self.l_ratio == 1.0: # square
			I_e_cs = self.calculate_avg_strip_I_e('l_1', 'column')
			I_e_ms = self.calculate_avg_strip_I_e('l_2', 'middle') # orthogonal to column strip
			self.I_e = I_e_cs + I_e_ms
		else: # rectangular
			I_e_csx = self.calculate_avg_strip_I_e('l_1', 'column')
			I_e_csy = self.calculate_avg_strip_I_e('l_2', 'column')
			I_e_msx = self.calculate_avg_strip_I_e('l_1', 'middle')
			I_e_msy = self.calculate_avg_strip_I_e('l_2', 'middle')
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
		print(self.mass)
		gamma = self.mass / (self.l_1 * self.l_2) # slug / ft2
		self.f_i = k_2 * lambda_i_sq / (2 * pi * self.l_1 ** 2.0) * \
				   (k_1 * self.E_c * 144 * (self.h / 12.) ** 3.0 / (12 * gamma * (1 - self.nu ** 2.0))) ** 0.5
		print(lambda_i_sq, k_2, gamma)
		return round(self.f_i, 1)

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


if __name__ == "__main__":
	# l_1 must be longer span, l_2 must be shorter span
	loading = {'sdl': 20., 'll_design': 65., 'll_vib': 11.}
	reinf   = {'l_1': {'column': {'n': 5.39, 'p': 2.31}, 'middle': {'n': 2.05, 'p': 2.05}},
			   'l_2': {'column': {'n': 4.15, 'p': 2.05}, 'middle': {'n': 3.08, 'p': 3.08}}}
	test = TwoWayFlatPlateSlab(l_1=25.0, l_2=20.0, h=9.5, f_c=4000, f_y=60000, w_c=150, nu=0.2, col_size={'c1': 22., 'c2': 22.}, 
		 				       loading=loading, reinforcement=reinf)
	print(test.calculate_f_i())



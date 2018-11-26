from numpy import sqrt, pi, roots, array, shape, zeros

class TwoWayFlatPlateSlab(object):
	'''
	NOTE THIS IS ONLY FOR INTERIOR BAY CURRENTLY WITH CONTINUOUS SPANS
	'''

	def __init__(self, l_1, l_2, h, f_c, f_y, w_c, col_size, loading=None, reinforcement=None, floor_type='rc'):
		self.l_1 = l_1
		self.l_2 = l_2
		self.h = h
		self.f_c = f_c
		self.c_b = col_size['b']
		self.c_h = col_size['h']
		self.l_ratio = l_1 / l_2
		self.f_y = f_y
		self.w_c = w_c
		self.loading = loading or {}
		self.reinforcement = reinforcement or {}

		# set modulus of elasticity
		if w_c >= 90 and w_c <= 160:
			self.E_c = w_c ** 1.5 * 33 * sqrt(f_c)
		else:
			raise ValueError

		if floor_type =='rc':
			self.E_c *= 1.2

		if w_c == 150.0:
			self.lambda_cw = 1.0
		elif w_c < 150.0:
			self.lambda_cw = 0.75
		else:
			raise NotImplementedError

		self.n = 29000000 / self.E_c
		self.f_r = 4.5 * self.lambda_cw * sqrt(f_c)

	def calculate_bending_moments(self, span, col_dim):

		def factor_moment(dead, live):
			return 1.2 * dead + 1.6 * live

		span_types = ['l_1', 'l_2']
		if span not in span_types:
			raise ValueError("Invalid span type. Expected one of: %s" % span_types)
		w_sdl = self.loading['sdl']
		w_ll_design  = self.loading['ll_design']
		w_ll_vib = self.loading['ll_vib']
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
								'middle': {'n': 0.0, 'p': 0.0}}}
		service = load_out['service']
		# Service moments
		service['column']['n']['dl'] = round(0.65 * M_0_dl * 0.75 * 0.001, 1)
		service['middle']['n']['dl'] = round(0.65 * M_0_dl * 0.25 * 0.001, 1)
		service['column']['n']['ll'] = round(0.65 * M_0_ll * 0.75 * 0.001, 1)
		service['middle']['n']['ll'] = round(0.65 * M_0_ll * 0.25 * 0.001, 1)
		service['column']['p']['dl'] = round(0.35 * M_0_dl * 0.6 * 0.001, 1)
		service['column']['p']['ll'] = round(0.35 * M_0_ll * 0.6 * 0.001, 1)
		service['middle']['p']['dl'] = round(0.35 * M_0_dl * 0.4 * 0.001, 1)
		service['middle']['p']['ll'] = round(0.35 * M_0_ll * 0.4 * 0.001, 1)
		# Factored moments
		factored = load_out['factored']
		factored['column']['n'] = round(factor_moment(service['column']['n']['dl'], service['column']['n']['ll']), 1)
		factored['column']['p'] = round(factor_moment(service['column']['p']['dl'], service['column']['p']['ll']), 1)
		factored['middle']['n'] = round(factor_moment(service['middle']['n']['dl'], service['middle']['n']['ll']), 1)
		factored['middle']['p'] = round(factor_moment(service['middle']['p']['dl'], service['middle']['p']['ll']), 1)
		return load_out

	def calculate_flexural_reinforcement(self, bending_moment, cover=0.75, bar_guess=0.75):
		raise NotImplementedError("Not implemented (yet)! Use another program to design slab for flexure for a tension controlled section")

	def get_strip_widths(self, span):
		col_width = min(0.25 * self.l_1, 0.25 * self.l_2) * 2
		if span == 'l_1':
			middle_width = self.l_2 - col_width
		if span == 'l_2':
			middle_width = self.l_1 - col_width
		return col_width, middle_width

	def calculate_strip_I_g(self, strip_width):
		return 1 / 12. * strip_width * 12 * self.h ** 3.0

	def calculate_strip_I_e(self, strip_width, M_n, As, d=None):
		n = self.n
		h = self.h
		f_r = self.f_r
		# calculate I_g 
		I_g = self.calculate_strip_I_g(strip_width) # does not account for steel reinf. (conservative)
		y_t = h / 2.0
		a_j = strip_width * 12 / (n * As)
		# estimate d if not provided
		if d == None:
			cover = 0.75
			bar_guess = 1.0
			d = h - cover - 0.5 * bar_guess
		p    = zeros(3)
		p[0] = strip_width * 12 * 0.5
		p[1] = n * As
		p[2] = -n * As * d
		kd   = max(roots(p)) # error handling??
		I_cr = strip_width * 12 * kd ** 3.0 / 3 + n * As * (d - kd) ** 2.0
		I_cr = min(I_cr, I_g)
		M_cr = f_r * I_g / y_t * 1 / 12000. # ft-kips
		M_ratio = M_cr / M_n
		if M_ratio > 1.0:
			I_e = I_g
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
		if span == 'l_1':
			col_width, middle_width = self.get_strip_widths('l_1')
			col_dim = self.c_b
		if span == 'l_2':
			col_width, middle_width = self.get_strip_widths('l_2')
			col_dim = self.c_h
		bending_moment = self.calculate_bending_moments(span, col_dim)
		bm_p = sum(bending_moment['service'][strip_type]['p'].values())
		bm_n = sum(bending_moment['service'][strip_type]['n'].values())
		#print(span, strip_type, bm_n, bm_p)
		reinf_p = self.reinforcement[span][strip_type]['p']
		reinf_n = self.reinforcement[span][strip_type]['n']
		if strip_type == 'column':
			#print(col_width, bm_p, reinf_p)
			#print(col_width, bm_n, reinf_n)
			I_m  = self.calculate_strip_I_e(col_width, bm_p, reinf_p)
			I_e1 = self.calculate_strip_I_e(col_width, bm_n, reinf_n)
		if strip_type == 'middle':
			#print(middle_width, bm_p, reinf_p)
			#print(middle_width, bm_n, reinf_n)
			I_m  = self.calculate_strip_I_e(middle_width, bm_p, reinf_p)
			I_e1 = self.calculate_strip_I_e(middle_width, bm_n, reinf_n)
		I_e2 = I_e1 # when would this differ?
		I_e  = 0.7 * I_m + 0.15 * (I_e1 + I_e2) # Eqn 4.19
		return I_e

	def calculate_panel_I_e(self):
		if self.l_ratio == 1.0:
			raise NotImplementedError
			# # middle strip span l_1
			# col_width, middle_width = self.get_strip_widths('l_1') # should be identical in both directions
			# bm_1   = self.calculate_bending_moments(span='l_1', col_dim=self.c_b)
			# bm_p   = sum(bm_1['service']['middle']['p'].values())
			# bm_n   = sum(bm_1['service']['middle']['n'].values())
			# I_m_m  = self.calculate_strip_I_e(middle_width, bm_p, l_1r['middle']['p'])
			# I_e1_m = self.calculate_strip_I_e(middle_width, bm_n, l_1r['middle']['n'])
			# I_e2_m = I_e1_m
			# I_e_m  = 0.7 * I_m_m + 0.15 * (I_e1_m + I_e2_m)
			# # column strip span l_2
			# bm_2   = self.calculate_bending_moments(span='l_2', col_dim=self.c_h)
			# bm_p   = sum(bm_1['service']['column']['p'].values())
			# bm_n   = sum(bm_1['service']['column']['n'].values())
			# I_m_m  = self.calculate_strip_I_e(col_width, bm_p, l_1r['column']['p'])
			# I_e1_c = self.calculate_strip_I_e(col_width, bm_n, l_1r['column']['n'])
			# I_e2_c = self.calculate_strip_I_e(col_width, bm_n, l_1r['column']['n']) # what differentiates e1 and e2?
			# I_e_c  = 0.7 * I_m_m + 0.15 * (I_e1_m + I_e2_m)
			# self.I_e = I_e_m + I_e_c
		else:
			I_e_csx = self.calculate_avg_strip_I_e('l_1', 'column')
			I_e_csy = self.calculate_avg_strip_I_e('l_2', 'column')
			I_e_msx = self.calculate_avg_strip_I_e('l_1', 'middle')
			I_e_msy = self.calculate_avg_strip_I_e('l_2', 'middle')
			self.I_e = ((I_e_csx + I_e_msy) + (I_e_csy + I_e_msx)) / 2.0
		return self.I_e

	def calculate_k_1(self):
		# accounts for level of cracking
		if self.rho <= 0.01:
			#  low reinforcement ratio (should include temp/shrink reinforcement)
			I_e = min(I_cr / (1 - (M_cr / M_a) ** 2.0 * (1 - I_cr / I_g)), I_g)
		elif l_ratio == 1.0:
			# square panel
			I_e = 0.7 * I_m + 0.15 * (I_e1 + I_e2)
		else: 
			# rectangular panel
			I_e = ((I_e_csx + I_e_msy) + (I_e_csy + I_e_msx)) / 2.0

		self.k_1 = I_e / I_g
		return self.k_1

	def calculate_f_i(self):
		# calculate k_1 - accounts for level of cracking
		k_1 = self.calculate_k_1
		# calculate k_2
		if self.col_size > 24:
			k_2 = 2.1
		else:
			k_2 = 1.9
		# calculate lambda_i_sq
		if l_ratio == 1.0:
			lambda_i_sq = 7.12
		elif l_ratio == 1.5:
			lambda_i_sq = 8.92
		elif l_ratio == 2.0:
			lambda_i_sq = 9.29
		else: 
			raise NotImplementedError
		self.f_i = k_2 * lambda_i_sq/ 2 * pi * l_1 ** 2.0 * \
				   sqrt((k_1 * E_c, h ** 3.0) / (12 * gamma * (1 - nu ** 2.0))) 
		return self.f_i

if __name__ == "__main__":
	loading = {'sdl': 20., 'll_design': 65., 'll_vib': 11.}
	reinf   = {'l_1': {'column': {'n': 5.39, 'p': 2.31}, 'middle': {'n': 2.05, 'p': 2.05}},
			   'l_2': {'column': {'n': 4.15, 'p': 2.05}, 'middle': {'n': 3.08, 'p': 3.08}}}
	test = TwoWayFlatPlateSlab(l_1=25.0, l_2=20.0, h=9.5, f_c=4000, f_y=60000, w_c=150, col_size={'b': 22., 'h': 22.}, loading=loading, reinforcement=reinf)
	bm_1 = test.calculate_bending_moments(span='l_1', col_dim=22.0)
	M_1n = sum(bm_1['service']['column']['n'].values())
	M_1p = sum(bm_1['service']['column']['p'].values())
	bm_2 = test.calculate_bending_moments(span='l_2', col_dim=22.0)
	M_2n = sum(bm_2['service']['column']['n'].values())
	M_2p = sum(bm_2['service']['column']['p'].values())
	print(test.calculate_panel_I_e())



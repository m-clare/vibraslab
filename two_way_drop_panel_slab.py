from numpy import sqrt
from numpy import pi
from numpy import roots
from numpy import zeros
from numpy import interp
from numpy import tanh
from numpy import cosh
from two_way_slab import TwoWayFlatPlateSlab
from two_way_slab import check_R

class TwoWayDropPanel(TwoWayFlatPlateSlab):
	'''
	Calculate the vibration characteristics (fundamental frequency) of a 2 way flat slab with drop panels 
	for interior/exterior bays only without beams between interior supports (no edge beam)
	Note: This assumes that the Direct Design Criteria by ACI have been fulfilled
	'''
	def __init__(self, h_dict, *args, **kwargs):
		super(TwoWayDropPanel, self).__init__(*args, **kwargs)

		self.h_dict = h_dict
		self.h_equiv = self.h_dict['h_equiv']
		self.h_slab = self.h_dict['l_1']['middle']['p'] # need to generalize
		self.h_drop = self.h_dict['l_1']['column']['n1'] # need to generalize

		# set self weight based on additional weight from drop panel
		self.self_weight = (self.l_1 * self.l_2 * self.h_slab / 12. + \
				 	       (0.33 * self.l_1) ** 2.0 * (self.h_drop - self.h_slab) / 12.) * 150. / (self.l_1 * self.l_2) 
		self.mass = ((self.self_weight + self.loading['sdl'] + self.loading['ll_vib']) * self.l_1 * self.l_2) / 32.2 # lb sec2/ft

	def calculate_avg_strip_I_g(self, span, strip_type):
		I_m = self.calculate_strip_I_g(self.strips[span][strip_type], self.h_dict[span][strip_type]['p'])
		I_e1 = self.calculate_strip_I_g(self.strips[span][strip_type], self.h_dict[span][strip_type]['n1'])
		I_e2 = self.calculate_strip_I_g(self.strips[span][strip_type], self.h_dict[span][strip_type]['n2'])
		I_g = 0.7 * I_m + 0.15 * (I_e1 + I_e2)
		return I_g

	def calculate_panel_I_g(self):
		I_g_csx = self.calculate_avg_strip_I_g('l_1', 'column')
		I_g_csy = self.calculate_avg_strip_I_g('l_2', 'column')
		I_g_msx = self.calculate_avg_strip_I_g('l_1', 'middle')
		I_g_msy = self.calculate_avg_strip_I_g('l_2', 'middle')
		self.I_g = ((I_g_csx + I_g_msy) + (I_g_csy + I_g_msx)) / 2.0
		return self.I_g

	def calculate_avg_strip_I_e(self, span, strip_type):
		strip_options = ['column', 'middle']
		locations = ['p', 'n1', 'n2']
		I_e_map = {'p': 'I_m', 'n1': 'I_e1', 'n2': 'I_e2'}
		h_map = {'p': self.h_dict[span][strip_type]['p'], 
				 'n1': self.h_dict[span][strip_type]['n1'], 
				 'n2': self.h_dict[span][strip_type]['n2']}
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
			I_e = self.calculate_strip_I_e(strip_width, bm, As, h_eff)
			I_eff[I_e_map[location]] = I_e

		I_e  = 0.7 * I_eff['I_m'] + 0.15 * (I_eff['I_e1'] + I_eff['I_e2']) # Eqn 4.19
		return I_e

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
		gamma = self.mass / (self.l_1 * self.l_2) # slug / ft2
		self.f_i = k_2 * lambda_i_sq / (2 * pi * self.l_1 ** 2.0) * \
				   (k_1 * self.E_c * 144 * (self.h_equiv / 12.) ** 3.0 / (12 * gamma * (1 - self.nu ** 2.0))) ** 0.5
		return round(self.f_i, 2)

if __name__ == "__main__":
	import json

	h = {'l_1': {'column': {'p': 14., 'n1': 17.5, 'n2': 17.5}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}},
		 'l_2': {'column': {'p': 14., 'n1': 17.5, 'n2': 17.5}, 'middle': {'p': 14., 'n1': 14., 'n2': 14.}}, 'h_equiv': 15.1}
	d5_3 = {'loading': {'sdl': 0., 'll_design': 80., 'll_vib': 11.},
				 'l_1': 34., 'l_2': 34., 'f_c': 5000, 'f_y': 60000, 'w_c': 150, 'nu': 0.2, 
			 	 'col_size': {'c1': 28., 'c2': 28.}, 'bay': {'l_1': 'exterior', 'l_2': 'interior'}}
	slab_test = TwoWayDropPanel(l_1=d5_3['l_1'], l_2=d5_3['l_2'], h=14, h_dict=h, 
								f_c=d5_3['f_c'], f_y=d5_3['f_y'], w_c=d5_3['w_c'], nu=d5_3['nu'], col_size=d5_3['col_size'], 
		 				        bay=d5_3['bay'], loading=d5_3['loading'])

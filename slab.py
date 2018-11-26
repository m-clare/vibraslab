class Slab(object):
	def __init__(self, mat_type, damping_ratio, loading, deck, girder,
		         beam, floor_width, floor_length, mode_scaling):
		self.mat_type = mat_type
		self.damping_ratio = damping_ratio
		self.loading = loading or {}
		self.deck = deck or {}
		self.girder = girder or {}
		self.beam = beam or {}
		self.floor_width = floor_width
		self.floor_length = floor_length
		self.mode_scaling = mode_scaling or {}

		def calculate_girder_loads(self, side=None):
			if side='left':
				pass
			if side='right':
				pass
			else: 
				raise NameError
			return

		def calculate_beam_loads(self):

			return

		def get_girder_properties(self, side=None):
			# will be different for diff material types
			if side:
				load = self.calculate_girder_loads(side)
			else:
				raise NameError
			return

		def get_beam_properties(self):
			# will be different for diff material types
			return

		def calculate_mode_scaling(self):
			return

		def calculate_beam_frequency(self, beam_type='beam'):
			if beam_type='beam':
				pass
			if beam_type='left_girder':
				pass
			if beam_type='right_girder':
				pass
			else: 
				raise NameError
			return

		def calculate_system_frequency(self):
			f_gl = calculate_beam_frequency(self, beam_type='left_girder')
			f_gr = calculate_beam_frequency(self, beam_type='right_girder')
			f_b = calculate_beam_frequency(self, beam_type='beam')
			f_s = min(f_gl, f_gr, f_b)
			self.f_s = f_s
			return f_s

test = Slab('steel', 0.05, {'dead': 4.0, 'live': 11.0, 'collateral': 0.0}, 
			{'total_depth': 5.25, 'f_c': 3, 'weight': 115.0}, 
			{'left_member': 'W24x55', 'right_member':'W24x55', 'span': 24.0},
			{'left_span': 0.0, 'center_span': 30.0, 'right_span': 30.0, 'spacing': 84.0, 'member': 'W16x26'}, 
			140.0, 60.0, {'xe': 15.0, 'ye': 14.0, 'xw': 8, 'yw': 14.0})
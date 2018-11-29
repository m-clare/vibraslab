from check_vib import check_sensitive_equip_steel, check_sensitive_equip_concrete
from two_way_slab import TwoWayFlatPlateSlab

# Input data
loading = {'sdl': 15., 'll_design': 60., 'll_vib': 11.}
slab_depths = [12, 14, 16, 18, 20, 24]
slabs = [{'l_1': 30., 'l_2': 30., 
		 'reinf': {'l_1': {'column': {'n': 10.1, 'p': 4.2}, 'middle': {'n': 3.9, 'p': 3.9}},
		      	   'l_2': {'column': {'n': 10.1, 'p': 4.2}, 'middle': {'n': 3.9, 'p': 3.9}}}}, 
		 {'l_1': 32., 'l_2': 32., 
		 'reinf': {'l_1': {'column': {'n': 12.5, 'p': 5.2}, 'middle': {'n': 4.2, 'p': 4.2}},
		      	   'l_2': {'column': {'n': 12.5, 'p': 5.2}, 'middle': {'n': 4.2, 'p': 4.2}}}}, 
		 {'l_1': 32., 'l_2': 16.,
		 'reinf': {'l_1': {'column': {'n': 6.22, 'p': 2.6}, 'middle': {'n': 2.07, 'p': 2.07}},
		      	   'l_2': {'column': {'n': 2.62, 'p': 2.07}, 'middle': {'n': 6.22, 'p': 6.22}}}}, 
		 {'l_1': 36., 'l_2': 16.,
		 'reinf': {'l_1': {'column': {'n': 8.11, 'p': 3.36}, 'middle': {'n': 2.6, 'p': 2.21}},
		      	   'l_2': {'column': {'n': 3.0, 'p': 2.07}, 'middle': {'n': 7.3, 'p': 7.3}}}},
		 {'l_1': 38., 'l_2': 32,
		 'reinf': {'l_1': {'column': {'n': 16.5, 'p': 6.9}, 'middle': {'n': 5.3, 'p': 4.5}},
		      	   'l_2': {'column': {'n': 13.5, 'p': 5.6}, 'middle': {'n': 5.7, 'p': 5.7}}}},
		 {'l_1': 36., 'l_2': 32,
		 'reinf': {'l_1': {'column': {'n': 14.7, 'p': 6.1}, 'middle': {'n': 4.7, 'p': 4.2}},
		      	   'l_2': {'column': {'n': 12.7, 'p': 5.3}, 'middle': {'n': 5.2, 'p': 5.2}}}}]
bay = {'l_1': 'interior', 'l_2': 'interior'}
col_size = {'c1': 32., 'c2': 32.}

for slab in slabs:
	for depth in slab_depths:

		twslab = TwoWayFlatPlateSlab(l_1=slab['l_1'], l_2=slab['l_2'], h=depth, f_c=4000, f_y=60000, w_c=150, nu=0.2, 
									 col_size=col_size, bay=bay, loading=loading, reinforcement=slab['reinf'])
		fn = twslab.calculate_f_i()
		delta_p = twslab.calculate_delta_p()
		fw = twslab.weight
		print('h: ', depth, 'l_1', slab['l_1'], 'l_2', slab['l_2'])
		print(twslab.strips, fn, delta_p, fw, twslab.k_1)
		test_c = check_sensitive_equip_concrete(fn, delta_p, manufacturer_limit=6000, limit_type='maximum velocity')
		test_s = check_sensitive_equip_steel(fn, fw, 0.03, manufacturer_limit=6000, limit_type='one-third octave velocity')
		print(test_c)
		print(test_s)
		print()

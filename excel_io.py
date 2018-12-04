from openpyxl import Workbook
from openpyxl import load_workbook
# columns - model, limit, bay size (x, x), slab thickness, column dimensions

# recursion doesn't work yet...
def iterdict_out(idict, ws):

	def iterdict(idict):
		for key, address in idict.items():
			print(address)
			if isinstance(address, dict):
				iterdict(address)
			else:
				address = ws[address].value
	return idict

def json_to_excel(ws, data, row_index=0, col_index=0, existing_ws=None):
	raise NotImplementedError
	# headers = ['l_1', 'l_2', 'bay_1', 'bay_2', 'c_1', 'c_2',  'nu', 'f_c', 'f_y', 'h', 'w_c', 'SDL', 'LL', 'LLvib', 'f_n', 'W', 'beta',
	# 		   'very_slow_v', 'slow_v', 'moderate_v', 'fast_v']
	# for i in range(len(headers)):
	# 	ws.write(1, i, headers[i])

def slab_excel_to_json(wb_name='Flat_Plate_Vibration_Template.xlsx', ws_name='Slab_Properties'):
	wb = load_workbook(filename=wb_name)
	ws = wb[ws_name]
	excel_address = {'l_1': 'B3', 'l_2': 'B4', 'nu': 'B8',
					   'f_c': 'B9', 'f_y': 'B10', 'h': 'B12', 'w_c': 'B14'}
	col_address = {'c1': 'B6', 'c2': 'B7'}
	loading_address = {'sdl': 'B26', 'll_design': 'B27', 'll_vib': 'B28'}
	bay_address = {'l_1': 'D3', 'l_2': 'D4'}
	all_addresses = {'l_1': 'B3', 'l_2': 'B4', 'nu': 'B8',
					   'f_c': 'B9', 'f_y': 'B10', 'h': 'B12', 'w_c': 'B14',
					 'col_size': {'c1': 'B6', 'c2': 'B7'}, 'loading': {'sdl': 'B26', 'll_design': 'B27', 'll_vib': 'B28'}}
	slab_dict = {}
	for key, address in excel_address.items():
		slab_dict[key] = ws[address].value
	slab_dict['col_size'] = {}
	for key, address in col_address.items():
		slab_dict['col_size'][key] = ws[address].value
	slab_dict['loading'] = {}
	for key, address in loading_address.items():
		slab_dict['loading'][key] = ws[address].value
	slab_dict['bay'] = {}
	for key, address in bay_address.items():
		slab_dict['bay'][key] = ws[address].value
	return slab_dict

def batch_slab_excel_to_input(start_row, end_row=None, wb_name='Flat_Plate_Vibration_Template.xlsx', ws_name='Sample_Slabs'):
	wb = load_workbook(filename=wb_name)
	ws = wb[ws_name]
	if end_row == None:
		end_row = ws.max_row
	excel_ind = {'l_1': 'B', 'l_2': 'C', 'nu': 'H', 'f_c': 'I', 'f_y': 'J', 'h': 'K', 'w_c': 'L'}
	col_ind = {'c1': 'F', 'c2': 'G'}
	loading_ind = {'sdl': 'M', 'll_design': 'N', 'll_vib': 'O'}
	bay_ind = {'l_1': 'D', 'l_2': 'E'}
	slabs = []
	for i in range(start_row, end_row + 1):
		slab_dict = {}
		for key, address in excel_ind.items():
			slab_dict[key] = ws[address + str(i)].value
		slab_dict['col_size'] = {}
		for key, address in col_ind.items():
			slab_dict['col_size'][key] = ws[address + str(i)].value
		slab_dict['loading'] = {}
		for key, address in loading_ind.items():
			slab_dict['loading'][key] = ws[address + str(i)].value
		slab_dict['bay'] = {}
		for key, address in bay_ind.items():
			slab_dict['bay'][key] = ws[address + str(i)].value
		slabs.append(slab_dict)
	return slabs

def batch_slab_output_to_excel(start_row, end_row, odata, wb_name='Flat_Plate_Vibration_Template', ws_name='Sample_Slabs'):
	wb= load_workbook(filename=wb_name + '.xlsx')
	ws = wb[ws_name]
	if end_row == None:
		end_row = start_row + len(odata)
	rho_ind  = {'l_1': {'column': {'p': 'P', 'n1': 'Q', 'n2': 'R'}, 'middle': {'p': 'S', 'n1': 'T', 'n2': 'U'}},
			    'l_2': {'column': {'p': 'V', 'n1': 'W', 'n2': 'X'}, 'middle': {'p': 'Y', 'n1': 'Z', 'n2': 'AA'}}}
	excel_ind = {'k_1': 'AB', 'f_n': 'AC', 'W': 'AD', 'beta': 'AE', 'very_slow': 'AF', 'slow': 'AG', 'moderate': 'AH', 'fast': 'AI'}
	counter = 0
	for i in range(start_row, end_row):
		# should use recursion for nested dictionaries....
		slab_data = odata[counter]
		for key, address in excel_ind.items():
			ws[address + str(i)] = slab_data[key]
		# Reinforcement Info
		spans = ['l_1', 'l_2']
		strip_types = ['column', 'middle']
		locations = ['p', 'n1', 'n2']
		for span in spans:
			for strip_type in strip_types:
				for location in locations:
					address = rho_ind[span][strip_type][location]
					try:
						ws[address + str(i)] = slab_data['rho'][span][strip_type][location]
					except:
						pass
		counter += 1

	wb.save(filename=wb_name + '_out_04.xlsx')





if __name__ == '__main__':
	#excel_to_json()
	import json
	with open('two_way_study.json') as data:
		odata = json.load(data)
	batch_slab_output_to_excel(3, None, odata)


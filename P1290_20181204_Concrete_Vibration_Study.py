from check_vib import check_sensitive_equip_steel
from two_way_slab import TwoWayFlatPlateSlab
from excel_io import batch_slab_excel_to_input
from excel_io import batch_slab_output_to_excel
import json

# Excel input
workbook  = 'Flat_Plate_Vibration_Template.xlsx'
worksheet = 'Sample_Slabs'
start_row = 3

# Excel output
workbook  = 'Flat_Plate_Vibration_Template.xlsx'
worksheet = 'Sample_Slabs'
start_row = 3

floors = batch_slab_excel_to_input(start_row=start_row, end_row=None, wb_name=workbook, ws_name=worksheet)
odata = []
for floor in floors:
	twfloor = TwoWayFlatPlateSlab(l_1=floor['l_1'], l_2=floor['l_2'], h=floor['h'], f_c=floor['f_c'], 
								  f_y=floor['f_y'], w_c=floor['w_c'], nu=floor['nu'], 
								  col_size=floor['col_size'], bay=floor['bay'], 
								  loading=floor['loading'])
	fn = round(twfloor.calculate_f_i(), 2)
	W  = round(twfloor.weight, 1)
	twfloor.vib = check_sensitive_equip_steel(fn, W, 0.04, manufacturer_limit=6000, limit_type='generic velocity')
	odata.append({'f_n': fn, 'W': twfloor.weight, 'beta': 0.04, 'rho': twfloor.rho, 'k_1': twfloor.k_1,
			     'very_slow': twfloor.vib['very_slow']['V_13'], 'slow': twfloor.vib['slow']['V_13'], 
			     'moderate': twfloor.vib['moderate']['V_13'], 'fast': twfloor.vib['fast']['V_13']})
batch_slab_output_to_excel(start_row=start_row, end_row=None, odata=odata)
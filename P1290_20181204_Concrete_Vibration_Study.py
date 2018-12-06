from check_vibration import check_sensitive_equip_steel
from two_way_slab import TwoWayFlatPlateSlab
from excel_io import batch_slab_excel_to_input
from excel_io import batch_slab_output_to_excel
import json

# Excel input
workbook  = './slab_36x32/Flat_Plate_Vibration_36x32'
worksheet = 'Rho_default'
start_row = 3

floors = batch_slab_excel_to_input(start_row=start_row, end_row=None, rho=True, wb_name=workbook, ws_name=worksheet)
odata = []
ostudy = []
for floor in floors:
	twfloor = TwoWayFlatPlateSlab(l_1=floor['l_1'], l_2=floor['l_2'], h=floor['h'], f_c=floor['f_c'], 
								  f_y=floor['f_y'], w_c=floor['w_c'], nu=floor['nu'], 
								  col_size=floor['col_size'], bay={'l_1': 'interior', 'l_2': 'interior'}, 
								  loading=floor['loading'], reinforcement=floor['reinforcement'])

	fn = round(twfloor.calculate_f_i(), 2)
	W  = round(twfloor.weight, 1)
	damping = [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
	for dr in damping:
		twfloor.vib = check_sensitive_equip_steel(fn, W, dr, manufacturer_limit=6000, limit_type='generic velocity')
		test = twfloor.__dict__.copy()
		ostudy.append(test)
with open('./slab_36x32/two_way_slab_interior_study.json', 'w') as fh:
	json.dump(ostudy, fh)
batch_slab_output_to_excel(start_row=start_row, end_row=None, odata=ostudy, rho=True, wb_name=workbook, ws_name='interior_study')
from check_vibration import check_sensitive_equip_steel
from two_way_slab import TwoWayFlatPlateSlab
from excel_io import batch_slab_excel_to_input
from excel_io import batch_slab_output_to_excel
import json

# Excel input
span = '36x16'
workbook  = './slab_' + span + '/Flat_Plate_Vibration_' + span
worksheet = 'thickness_default'
start_row = 3

floors = batch_slab_excel_to_input(start_row=start_row, end_row=None, rho=False, wb_name=workbook, ws_name=worksheet)
odata = []
ostudy = []
for floor in floors:
	twfloor = TwoWayFlatPlateSlab(l_1=floor['l_1'], l_2=floor['l_2'], h=floor['h'], f_c=floor['f_c'], 
								  f_y=floor['f_y'], w_c=floor['w_c'], nu=floor['nu'], 
								  col_size=floor['col_size'], bay=floor['bay'], 
								  loading=floor['loading'])

	fn = round(twfloor.calculate_f_i(), 2)
	W  = round(twfloor.weight, 1)
	damping = [0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07]
	for dr in damping:
		twfloor.vib = check_sensitive_equip_steel(fn, W, dr, manufacturer_limit=6000, limit_type='generic velocity')
		test = twfloor.__dict__.copy()
		ostudy.append(test)
with open('./slab_' + span + '/two_way_slab_thickness_study.json', 'w') as fh:
	json.dump(ostudy, fh)
batch_slab_output_to_excel(start_row=start_row, end_row=None, odata=ostudy, rho=True, wb_name=workbook, ws_name='thickness_study')
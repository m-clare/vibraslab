from check_vibration import check_sensitive_equip_steel
from two_way_slab import TwoWayFlatPlateSlab
from excel_io import batch_slab_excel_to_input
from excel_io import batch_slab_output_to_excel
import json

# Excel input
workbook  = 'Flat_Plate_Vibration_36x32'
worksheet = 'Rho_100%'
start_row = 3

floors = batch_slab_excel_to_input(start_row=start_row, end_row=None, rho=True, wb_name=workbook, ws_name=worksheet)
odata = []
ostudy = []
for floor in floors:
	print(floor)
	twfloor = TwoWayFlatPlateSlab(l_1=floor['l_1'], l_2=floor['l_2'], h=floor['h'], f_c=floor['f_c'], 
								  f_y=floor['f_y'], w_c=floor['w_c'], nu=floor['nu'], 
								  col_size=floor['col_size'], bay=floor['bay'], 
								  loading=floor['loading'], reinforcement=floor['reinforcement'])

	fn = round(twfloor.calculate_f_i(), 2)
	W  = round(twfloor.weight, 1)
	damping = 0.03
	twfloor.vib = check_sensitive_equip_steel(fn, W, damping, manufacturer_limit=6000, limit_type='generic velocity')
	ostudy.append(twfloor.__dict__)
with open('./slab_36x32/two_way_slab_study_100%.json', 'w') as fh:
	json.dump(ostudy, fh)
batch_slab_output_to_excel(start_row=start_row, end_row=None, odata=ostudy, rho=False, wb_name=workbook, ws_name=worksheet)
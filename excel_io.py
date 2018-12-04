from openpyxl import Workbook
# columns - model, limit, bay size (x, x), slab thickness, column dimensions
wb = Workbook

def json_to_excel(ws, data, row_index=0, col_index=0):
	headers = ['l_1', 'l_2', 'h', 'f_c', 'c_1', 'c_2', 'bay_1', 'bay_2', 'f_n', 'W', 'beta',
			   'very_slow_v', 'slow_v', 'moderate_v', 'fast_v']
	for i in range(len(headers)):
		ws.write(1, i, headers[i])

def excel_to_json():
	pass



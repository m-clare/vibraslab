import matplotlib.pyplot as plt
import numpy as np
import mpld3
from mpld3 import plugins
import json

__author__     = ['Maryanne Wachter']
__version__    = '0.1'
__status__     = 'Development'
__date__       = 'Dec 5, 2018'

def bubble_plot_floors(data, x_axis, y_axis, size, shape, color):

  # Table Attributes for Hover
  css = """
  table
  {
    border-collapse: collapse;
  }
  th
  {
    color: #ffffff;
    background-color: #000000;
  }
  td
  {
    background-color: #cccccc;
  }
  table, th, td
  {
    font-family:Arial, Helvetica, sans-serif;
    border: 1px solid white;
    text-align: center;
  }
  """

  damping_settings = {}
  color_settings = {'very_slow': 'xkcd:red', 'slow': 'xkcd:tangerine', 
                    'moderate': 'xkcd:goldenrod', 'fast': 'xkcd:grass green'}

  fig, ax = plt.subplots()
  ax.grid(True, alpha=0.3)

  x_values = []
  y_values = []
  color_values = []
  size = []
  labels = []
  scale = 2.0
  for floor in data:
    x_values.append(floor['c_1'])
    y_values.append(floor['h'])
    size.append((floor['f_i'] *scale) ** 2)
    # set marker color
    if floor['vib']['fast']['crit'] == 'pass':
      color_values.append(color_settings['fast'])
    elif floor['vib']['moderate']['crit'] == 'pass':
      color_values.append(color_settings['moderate'])
    elif floor['vib']['slow']['crit'] == 'pass':
      color_values.append(color_settings['slow'])
    elif floor['vib']['very_slow']['crit'] == 'pass':
      color_values.append(color_settings['very_slow'])
    else:
      color_values.append('xkcd:crimson')


  points = ax.scatter(x_values, y_values, s=size, c=color_values, marker='o')
  ax.set_xlabel('column size (in)')
  ax.set_ylabel('slab thickness (in)')
  ax.set_title('34 ft x 34 ft Bay 3% Damping, 50% additional flexural rebar', size=20)

  # tooltip = plugins.PointHTMLTooltip(points[0], labels, voffset=10, hoffset=10, css=css)
  # plugins.connect(fig, tooltip)
  plt.show()
  # mpld3.show()

if __name__ == "__main__":
  import json
  with open('two_way_slab_study_100%.json') as fh:
    data = json.load(fh)

    bubble_plot_floors(data, None, None, None, None, None)
    pass
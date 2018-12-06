import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
                    'moderate': 'xkcd:goldenrod', 'fast': 'xkcd:grass green', 'not_passing': 'xkcd:crimson'}

    fig, axes = plt.subplots(3, 2, sharey=True, sharex=True)

    x_values = []
    y_values = []
    color_values = []
    size = []
    labels = []
    scale = 2.0
    damping = [0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
    for dr in damping:
        x = []
        y = []
        color = []
        for floor in data:
            if floor['vib']['beta'] == dr:
                x.append(floor['c1'])
                y.append(floor['h'])
                size.append((floor['f_i'] *scale) ** 2)
                # set marker color
                if floor['vib']['fast']['crit'] == 'pass':
                  color.append(color_settings['fast'])
                elif floor['vib']['moderate']['crit'] == 'pass':
                  color.append(color_settings['moderate'])
                elif floor['vib']['slow']['crit'] == 'pass':
                  color.append(color_settings['slow'])
                elif floor['vib']['very_slow']['crit'] == 'pass':
                  color.append(color_settings['very_slow'])
                else:
                  color.append('xkcd:crimson')
        x_values.append(x)
        y_values.append(y)
        color_values.append(color)
    print(len(x_values))


    count = 0
    for i in range(3):
        for j in range(2):
            axes[i, j].grid(True, alpha=0.3)
            axes[i, j].scatter(x_values[count], y_values[count], s=size, c=color_values[count], marker='s')
            axes[i, j].set_title(str(damping[count]) + ' Damping', size=12)
            count += 1
    axes[2, 0].set_xlabel('column size (in)')
    axes[2, 1].set_xlabel('column size (in)')
    axes[2, 0].set_ylabel('slab thickness (in)')
    axes[1, 0].set_ylabel('slab thickness (in)')
    axes[0, 0].set_ylabel('slab thickness (in)')

    legend_color = ['not_passing', 'very_slow', 'slow', 'moderate', 'fast']
    patches = []
    for color in legend_color:
        patches.append(mpatches.Patch(color=color_settings[color], label=color))
    plt.legend(handles=patches, bbox_to_anchor=(1.1, 1), loc='upper center', borderaxespad=0.)

    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper center', borderaxespad=0.)
    fig.suptitle('36 ft x 32 ft Bay (Interior) - Estimated Reinforcement' , fontsize=16)
    # points = ax.scatter(x_values, y_values, s=size, c=color_values, marker='o')
    # ax.set_xlabel('column size (in)')
    # ax.set_ylabel('slab thickness (in)')
    # plt.legend()
    # ax.set_title('36 ft x 32 ft Bay 3% Damping', size=20)

    # tooltip = plugins.PointHTMLTooltip(points[0], labels, voffset=10, hoffset=10, css=css)
    # plugins.connect(fig, tooltip)
    plt.show()

    # points = points.values.tolist()
    # mpld3.show()

if __name__ == "__main__":
    import json
    with open('./slab_36x32/two_way_slab_interior_study.json') as fh:
        data = json.load(fh)

    bubble_plot_floors(data, None, None, None, None, None)
    pass
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

def line_plot_damping(data, name):
    '''
    Plots results from vibration check for different floor systems
    '''

    damping_settings = {}

    fig, axes = plt.subplots(1, 4, sharey=True)


    color_values = []
    size = []
    labels = []
    scale = 2.0
    plots = ['very_slow', 'slow', 'moderate', 'fast']
    plot = 'very_slow'
    plot_x = []
    plot_y = []
    damping = [0.025, 0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07]
    for plot in plots:
        x_values = []
        y_values = []
        for dr in damping:
            x = []
            y = []
            for floor in data:
                if floor['vib']['beta'] == dr and floor['c1'] == 28.:
                    x.append(floor['h'])
                    y.append(floor['vib'][plot]['V_13'])
            x_values.append(x)
            y_values.append(y)
        plot_x.append(x_values)
        plot_y.append(y_values)

    count = 0
    for i in range(4):
        axes[i].grid(True, alpha=0.3)
        x_val = plot_x[i]
        y_val = plot_y[i]
        for j in range(len(damping)):    
            axes[i].plot(x_val[j], y_val[j], label=damping[j])
        axes[i].plot([10.0, 18.0], [6000., 6000], linestyle='dashed', linewidth=2, color='k')
        axes[i].set_xlabel('slab depth (in)')
        axes[0].set_ylabel('Generic velocity response (mips)')
        axes[i].set_title(plots[i], size=12)
        plt.legend()

    fig.suptitle(name + ' Floor Depth Sensitivity' , fontsize=16)
    plt.show()

def bubble_plot_floors(data, name, x_axis, y_axis, size, shape, color):

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
    damping = [0.03, 0.04, 0.05, 0.06, 0.065, 0.07]
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

    fig.suptitle(name , fontsize=16)
    plt.show()

if __name__ == "__main__":
    import json

    bay = '34x34'
    param = 'exterior_study'
    # plot_type = 
    with open('../examples/slab_34x34/two_way_slab_' + param + '.json') as fh:
        data = json.load(fh)

    name = bay + ' (exterior)'
    bubble_plot_floors(data, name, None, None, None, None, None)


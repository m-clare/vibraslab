import matplotlib
import numpy as np
import matplotlib.pyplot as plt

#First create some toy data:
x = np.linspace(0, 2*np.pi, 400)
y = np.sin(x**2)

#Creates just a figure and only one subplot
# fig, ax = plt.subplots()
# ax.plot(x, y)
# ax.set_title('Simple plot')

# #Creates two subplots and unpacks the output array immediately
# f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# ax1.plot(x, y)
# ax1.set_title('Sharing Y axis')
# ax2.scatter(x, y)

# #Creates four polar axes, and accesses them through the returned array
fig, axes = plt.subplots(2, 2, subplot_kw=dict(polar=True))
axes[0, 0].plot(x, y)
axes[1, 1].scatter(x, y)

# #Share a X axis with each column of subplots
# plt.subplots(2, 2, sharex='col')

# #Share a Y axis with each row of subplots
# plt.subplots(2, 2, sharey='row')

# #Share both X and Y axes with all subplots
# plt.subplots(2, 2, sharex='all', sharey='all')

# #Note that this is the same as
# plt.subplots(2, 2, sharex=True, sharey=True)

# #Creates figure number 10 with a single subplot
# #and clears it if it already exists.
# fig, ax=plt.subplots(num=10, clear=True)

plt.show()

import matplotlib.pyplot as plt


plt.subplot(211)
plt.plot([1,2,3], label="test1")
plt.plot([3,2,1], label="test2")
# Place a legend above this subplot, expanding itself to
# fully use the given bounding box.
plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=2, mode="expand", borderaxespad=0.)

plt.subplot(223)
plt.plot([1,2,3], label="test1")
plt.plot([3,2,1], label="test2")
# Place a legend to the right of this smaller subplot.
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

plt.show()
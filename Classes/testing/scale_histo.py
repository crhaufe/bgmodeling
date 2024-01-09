import numpy as np
import matplotlib.pyplot as plt

nBinsX = 10000.0
xmin = 0.0
xmax = 10000.0

hArray = np.load('/Users/tundra/bgmodeling_inputSpectra/BuildSimSpectra_Output/DS5/cut2/l2/Enr/bulk_EnrGe_Ge68_2_DS5.npy')

#jArray = hArray / 2

xArray = np.arange(xmin + 0.5, xmax + 0.5)

plt.step(xArray, hArray, where = 'mid', color = 'tab:purple')
#plt.step(xArray, jArray, where = 'mid', color = 'tab:orange')

plt.show()

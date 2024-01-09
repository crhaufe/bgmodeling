import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

tracedir = sys.argv[1]
#tracegap = int(sys.argv[2])
trace = pd.read_pickle(tracedir + '/trace.pkl')
#color = iter(cm.rainbow(np.linspace(0, 1, 25)))
#for col in trace.columns:
#  if 'Th232' in col:
#    trace_values = trace[col].to_numpy()
#    iterations = np.arange(0,trace_values.size,tracegap)
#    c = next(color)
#    plt.scatter(iterations, trace_values[0::tracegap], c = c, label = col)
#plt.legend()
#plt.show()

df_chain = pd.DataFrame(trace,columns=['p_Th232_bulk_RadShieldCuOuter'])
df_chain['ma_theta'] = df_chain.p_Th232_bulk_RadShieldCuOuter.rolling(window=100,center=False).mean()
df_chain['iteration'] = df_chain.index.values
trace_values = df_chain['p_Th232_bulk_RadShieldCuOuter'].to_numpy()
ma_values = df_chain['ma_theta'].to_numpy()
iterations = df_chain['iteration'].to_numpy()
plt.plot(iterations,trace_values, c = 'b', label = 'RadShieldCuOuter')
plt.plot(iterations,trace_values, c = 'k', label = 'MA of RadShieldCuOuter', lw = 0.5)
#ax.lines[-1].set_linewidth(4)
#ax.lines[-1].set_color('k')
#ax.lines[0].set_label("RadShieldCuOuter")
#ax.lines[-1].set_label("Moving Average of RadShieldCuOuter")
plt.legend()
plt.show() 


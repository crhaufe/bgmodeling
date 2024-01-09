import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm

tracedir = sys.argv[1]
tracegap = int(sys.argv[2])
dC = sys.argv[3]
if 'toymcx1000' in tracedir:
  statstype = "High"
else:
  statstype = "MJD"
if 'loosepriors' in tracedir:
  unctype = "Loose"
else:
  unctype = "Original"  
trace = pd.read_pickle(tracedir + '/trace.pkl')
n = 0
for col in trace.columns:
  if dC in col: n+=1 
color = iter(cm.rainbow(np.linspace(0, 1, n)))
for col in trace.columns:
  if dC in col:
    trace_values = trace[col].to_numpy()
    iterations = np.arange(0,trace_values.size,tracegap)
    c = next(color)
    plt.plot(iterations, trace_values[0::tracegap], c = c, label = col)
plt.title("Trace of %s Components Over 10000 Iterations * 3 Chains\n w/ %s Stats and %s Prior Uncs." % (dC, statstype, unctype))
plt.xlabel("Iteration")
plt.ylabel("Posterior Value (Bq)")
plt.legend(prop={'size': 6})
plt.show() 


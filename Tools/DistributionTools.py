"""
"""

import numpy as np

class DistStruct:
    """
    Struct to hold binning settings
    """
    def __init__(self, min, max, bin_wid):
        self.min = min # bin_edges[0]
        self.max = max # bin_edges[-1]
        self.bin_wid = bin_wid

        self.UpdateDerived()

    def UpdateDerived(self):
        min, max, bin_wid = self.min, self.max, self.bin_wid
        self.range = min, max
        self.bins_n = int((max-min)/bin_wid)
        self.bin_centers = np.arange(min + 0.5*bin_wid, max + 0.5*bin_wid, bin_wid)

def FindBin(val, bin_centers, bin_wid):
    """
    Returns the bin index corresponding to a value along the binned axis
    """
    val = np.full(shape = len(bin_centers), fill_value = val)
    return np.where( (bin_centers - bin_wid/2. <= val) & (bin_centers + bin_wid/2. > val) )[0][0]

def Rebin(ndarray, new_shape, operation='sum'):
    """
    Rebin a histogram
    Usage:
        # new units: (new_summed_density/new_bin_wid)
        new_dist = Rebin(old_dist, (new_bins_n,), operation='sum') / new_bin_wid
    Ref:
        bin_ndarray()
        https://gist.github.com/derricw/95eab740e1b08b78c03f
        Bins an ndarray in all axes based on the target shape, by summing or
            averaging.
        Number of output dimensions must match number of input dimensions.
        Example
        -------
        >>> m = np.arange(0,100,1).reshape((10,10))
        >>> n = bin_ndarray(m, new_shape=(5,5), operation='sum')
        >>> print(n)
        [[ 22  30  38  46  54]
         [102 110 118 126 134]
         [182 190 198 206 214]
         [262 270 278 286 294]
         [342 350 358 366 374]]
    """
    if not operation.lower() in ['sum', 'mean', 'average', 'avg']:
        raise ValueError("Operation {} not supported.".format(operation))
    if ndarray.ndim != len(new_shape):
        raise ValueError("Shape mismatch: {} -> {}".format(ndarray.shape,
                                                           new_shape))

    compression_pairs = [(d, c//d) for d, c in zip(new_shape,
                                                   ndarray.shape)]
    flattened = [l for p in compression_pairs for l in p]
    ndarray = ndarray.reshape(flattened)
    for i in range(len(new_shape)):
        if operation.lower() == "sum":
            ndarray = ndarray.sum(-1*(i+1))
        elif operation.lower() in ["mean", "average", "avg"]:
            ndarray = ndarray.mean(-1*(i+1))
    return ndarray

def RebinVarBins(ndarray, var_bin_edges, operation='sum'):
    """
    Rebin a histogram into variable bins.
    The new distribution will be in units c/decay/kg/keV.  Bin contents are added to create the new bin of width > 1keV in integer units.
    The new bin content is then divided by the new bin width in order to give the correct units.
    Usage:
        new_dist = RebinVarBins(old_dist, (new_bins_n,), operation='sum').
    """
    if not operation.lower() in ['sum']:
        raise ValueError("Operation {} not supported.".format(operation))
    if ndarray.ndim != 1:
        raise ValueError("Shape mismatch: {} -> {}".format(ndarray.shape,
                                                           1))
    q = var_bin_edges.index(100) #trim leading bin edges to 100keV bin
    new_var_bin_edges = var_bin_edges[q:]

    #construct new ndarray
    new_ndarray = np.zeros(len(new_var_bin_edges))
    i = 1 #iterator for new_var_bin_edges and new_ndarray
    tmp_element = 0 #added bins
    for j in range(ndarray.size):
      if i < len(new_var_bin_edges):
        if (j+100) == new_var_bin_edges[i]:
          new_ndarray[i-1] = tmp_element/(new_var_bin_edges[i]-new_var_bin_edges[i-1])
          tmp_element = 0 #reset tmp_element
          i += 1
      tmp_element += ndarray[j]
    new_ndarray[i-1] = tmp_element/(3000-new_var_bin_edges[len(new_var_bin_edges)-1]) #fill last bin leading 2996 keV, trailing 3000 keV.

    return new_ndarray

def CropDistribution(dist, new_min, new_max, old_bin_centers, old_bin_wid):
    """
    Crop a distribution
    """
    return dist[FindBin(new_min, old_bin_centers, old_bin_wid):FindBin(new_max, old_bin_centers, old_bin_wid)]

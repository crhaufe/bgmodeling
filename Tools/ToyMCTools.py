"""
"""

import numpy as np
from scipy.stats import rv_discrete
import matplotlib.pyplot as plt
import sys

class ToyMCTools:
    """
    """
    def __init__(self, settings):
        self.settings = settings

    def SetSubModel(self, submodel):
        self.submodel = submodel
        # self.GetExpectedRateDist()

    def GetExpectedRateDist(self):
        """
        Get the expected dist for a submodel, normalized by exposure.
        """
        st = self.settings

        if st.toymc_targeted_vals:
            for component in self.submodel.component_list:
                fixed_dist = np.zeros(component.exp_rate_dist.size)
                floated_dist = np.zeros(component.exp_rate_dist.size)
                break
            for component in self.submodel.component_list: 
                if not component.floated:
                    if 'None' in st.toymc_targeted_vals_dc and 'None' in st.toymc_targeted_vals_comp:
                        new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                        fixed_dist = np.add(fixed_dist,new_exp_rate_dist)
                    elif 'None' not in st.toymc_targeted_vals_dc and 'None' in st.toymc_targeted_vals_comp:
                        if component.component_dict['decay_chain'] in st.toymc_targeted_vals_dc:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            fixed_dist = np.add(fixed_dist,new_exp_rate_dist)
                        else:
                            fixed_dist = np.add(fixed_dist,component.exp_rate_dist)
                    elif 'None' in st.toymc_targeted_vals_dc and 'None' not in st.toymc_targeted_vals_comp:
                        if component.component_dict['hardware_component'] in st.toymc_targeted_vals_comp:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            fixed_dist = np.add(fixed_dist,new_exp_rate_dist)
                        else:
                            fixed_dist = np.add(fixed_dist,component.exp_rate_dist)
                    else:
                        if component.component_dict['decay_chain'] in st.toymc_targeted_vals_dc and component.component_dict['hardware_component'] in st.toymc_targeted_vals_comp:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            fixed_dist = np.add(fixed_dist,new_exp_rate_dist)
                        else:
                            fixed_dist = np.add(fixed_dist,component.exp_rate_dist)
                else:
                    if 'None' in st.toymc_targeted_vals_dc and 'None' in st.toymc_targeted_vals_comp:
                        new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                        floated_dist = np.add(floated_dist,new_exp_rate_dist)
                    elif 'None' not in st.toymc_targeted_vals_dc and 'None' in st.toymc_targeted_vals_comp:
                        if component.component_dict['decay_chain'] in st.toymc_targeted_vals_dc:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            floated_dist = np.add(floated_dist,new_exp_rate_dist)
                            #print('THE DECAY CHAIN IS %s AND THE HARDWARE COMPONENT IS %s' % (component.component_dict['decay_chain'],component.component_dict['hardware_component']))
                        else:
                            floated_dist = np.add(floated_dist,component.exp_rate_dist)
                    elif 'None' in st.toymc_targeted_vals_dc and 'None' not in st.toymc_targeted_vals_comp:
                        if component.component_dict['hardware_component'] in st.toymc_targeted_vals_comp:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            floated_dist = np.add(floated_dist,new_exp_rate_dist)
                        else:
                            floated_dist = np.add(floated_dist,component.exp_rate_dist)
                    else:
                        if component.component_dict['decay_chain'] in st.toymc_targeted_vals_dc and component.component_dict['hardware_component'] in st.toymc_targeted_vals_comp:
                            new_exp_rate_dist = component.exp_rate_dist * st.toymc_targeted_vals_mult
                            floated_dist = np.add(floated_dist,new_exp_rate_dist)
                            print('THE DECAY CHAIN IS %s AND THE HARDWARE COMPONENT IS %s' % (component.component_dict['decay_chain'],component.component_dict['hardware_component']))
                        else:
                            floated_dist = np.add(floated_dist,component.exp_rate_dist)
        else:
            fixed_dist = np.sum([component.exp_rate_dist for component in self.submodel.component_list if not component.floated], axis = 0) # (c/sec)
            floated_dist = np.sum([component.exp_rate_dist for component in self.submodel.component_list if component.floated], axis = 0) # (c/sec)
        self.exp_rate_dist = fixed_dist + floated_dist # (c/yr) actually (c/sec)
        self.exp_rate_dist_integral = np.sum(self.exp_rate_dist)
        self.exp_count_dist_integral = self.exp_rate_dist_integral * self.submodel.runtime #(counts) = (c/sec) * sec

        if False:
            print('ToyMCTools::GetExpectedRateDist(): exposure: %.3f exposure %.3f' % (self.submodel.exposure, np.sum(fixed_dist + floated_dist)/np.sum(self.exp_rate_dist)))
            plt.figure()
            plt.step(st.dft.bin_centers, self.exp_rate_dist, where = 'mid', c = 'k')
            plt.yscale('log', nonposy='clip')
            plt.show()

    def GetExposure(self):
        """
        exposure = draws_n = (toymc_draws / exp_rate_dist_integral) * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral)
        exp_rate_dist_integral * exposure = draws_n = toymc_draws * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral)
        """
        st = self.settings

        # self.exposure = st.toymc_draws / st.largest_exp_rate_dist_integral # st.toymc_draws / np.sum(self.exp_rate_dist)
        # self.exposure_uncert = .01 * self.exposure

        #self.exposure = (st.toymc_draws / self.exp_rate_dist_integral) * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral)
        #self.toymc_exposure = ((((self.exp_count_dist_integral)/(st.largest_exp_count_dist_integral))*st.toymc_draws)/self.submodel.real_count_dist_integral)*self.submodel.exposure
        self.toymc_exposure = st.toymc_mult * self.submodel.exposure  

        self.toymc_exposure_uncert = .01 * self.toymc_exposure
        #print("st.toymc_draws: " + str(st.toymc_draws))
        #print("self.submodel.real_data_hits_integral: " + str(self.submodel.real_count_dist_integral))
        #print("self.exp_count_dist_integral: " + str(self.exp_count_dist_integral))
        #print("st.largest_exp_count_dist_integral: " + str(st.largest_exp_count_dist_integral))
        #print("SCALING FACTOR: " + str(self.exp_count_dist_integral/st.largest_exp_count_dist_integral))
        #sys.exit()

        if False:
            print('ToyMCTools::GetNewExposure(): toymc_draws toymc_exposure %d %.3f+/-%.3f (kg*yr)' \
                % (st.toymc_draws, self.exposure, self.exposure_uncert))

        return self.toymc_exposure, self.toymc_exposure_uncert

    def DrawSamples(self, draws_n = None):
        """
        exposure = draws_n = (toymc_draws / exp_rate_dist_integral) * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral)
        exp_rate_dist_integral * exposure = draws_n = toymc_draws * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral)
        """
        st = self.settings

        if draws_n == None:
            # draws_n = int(np.floor(st.toymc_draws * (np.sum(self.exp_rate_dist)/st.largest_exp_rate_dist_integral)))
            # draws_n = int(np.floor( st.toymc_draws * (self.exp_count_dist_integral / st.largest_exp_count_dist_integral) ))
            #draws_n = self.submodel.real_count_dist_integral * st.toymc_mult
            draws_n = int(np.floor(self.exp_count_dist_integral * st.toymc_mult))

        # INSTANTIATE rv_discrete
        # normalize hist_assay, because rv_discrete seems to require pre-normed values
        pdf = self.exp_rate_dist / np.sum(self.exp_rate_dist) # norm to np.sum of 1, no differential
        
        # if fitting with the variable binning scheme, the bin edges are already integer values so don't need to make adjustment for rv_discrete.rvs
        if st.variable_bin_size:
          rv = rv_discrete(a = st.dft.min, b = st.dft.max, name = 'samples', values = (st.var_bin_edges[st.var_bin_edges.index(st.dft.min):], pdf))
          samples = rv.rvs(size = draws_n)

        else:
          # make the bin centers, xBinCenters, into the integers, xBinIndices
          # this is needed since rv_discrete.rvs seems to only produce integers
          bin_indices = (st.dft.bin_centers + st.dft.bin_wid/2.) / st.dft.bin_wid
          # subclass rv_discrete
          rv = rv_discrete(a = st.dft.min, b = st.dft.max, name = 'samples', values = (bin_indices, pdf))

          # DRAW SAMPLES AND PLOT SAMPLED DATA
          # draw samples
          samples = rv.rvs(size = draws_n)
          # the samples are of integers, xBinIndices, so convert them back into values in xRange
          samples = st.dft.bin_wid * samples - st.dft.bin_wid/2.

        if False:
            # HISTOGRAM AND PLOT
            hist_samples = np.histogram(a = samples, bins = st.dft.bins_n, range = st.dft.range, density = False)[0] # (counts)
            figXLabel = 'energy (%.1f keV bins)' % st.dft.bin_wid
            figYLabel = 'counts'
            plt.figure()
            plt.title('samples = %d' % draws_n)
            plt.xlabel(figXLabel)
            plt.ylabel(figYLabel)
            plt.step(st.dft.bin_centers, pdf * draws_n, where = 'mid', c = 'lightgrey', label = 'scaled total assay pdf', zorder = 0)
            # plt.fill_between(xBinCenters, pdf*nSamples, step = 'mid', color = 'lightgrey')
            # plt.step(xBinCenters, hist_samples, where = 'mid', c = 'k', label = 'samples')
            plt.scatter(st.dft.bin_centers, hist_samples, marker = 'o', s = 1, c = 'k', label = 'samples', zorder = 1)
            plt.legend(prop={'size': 5})
            plt.yscale('log', nonposy='clip')
            plt.show()

        return samples

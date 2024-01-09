"""
"""

import numpy as np
import pickle as pl

from Tools.DistributionTools import *

class Settings:
    """
    """
    def __init__(self, args):
        """
        args: ArgumentParser.parse_args() object with the populated namespace
        """
        # Store the command line options and arguments
        self.args = args
        # Make use of command line options and arguments
        self.InitCommandLineOptions()
        # Initialize distribution settings
        self.InitDistributionSettings()

    def InitCommandLineOptions(self):
        """
        Initiate all of the settings passed as command line options
        """
        args = self.args

        ## Model
        self.model_dirname = args.model_dirname[0].strip('/') # str
        self.model_debug = args.model_debug
        self.model_type = args.model_type[0]
        ## MCMC, Sampling
        self.mcmc_draws = args.mcmc_draws[0]
        self.mcmc_warmup = args.mcmc_warmup[0]
        self.mcmc_chains = args.mcmc_chains[0]
        self.mcmc_cores = args.mcmc_cores[0]
        self.mcmc_step_method = args.mcmc_step_method[0]
        self.mcmc_rand_testvals = args.mcmc_rand_testvals
        self.mcmc_startvals_type = args.mcmc_startvals_type[0]
        self.mcmc_target_accept = args.mcmc_target_accept[0]
        self.mcmc_random_seed = args.mcmc_random_seed
        self.mcmc_seed_number = args.mcmc_seed_number
        self.mcmc_unconstrained = args.mcmc_unconstrained[0]
        self.mcmc_all_flat = args.mcmc_all_flat
        ## Fit Engine
        self.fit_peaks = args.fit_peaks
        self.fit_range = args.fit_range
        ## Distributions
        self.distribution_bin_wid = args.distribution_bin_wid[0]
        self.variable_bin_size = args.variable_bin_size
        self.kco_set_number = args.kco_set_number[0]
        ## Toy MC
        self.toymc = args.toymc
        self.toymc_draws = args.toymc_draws[0]
        self.toymc_mult = args.toymc_mult[0]
        self.toymc_rand_vals = args.toymc_rand_vals
        self.toymc_targeted_vals = args.toymc_targeted_vals
        self.toymc_targeted_vals_mult = args.toymc_targeted_vals_mult[0]
        self.toymc_targeted_vals_dc = args.toymc_targeted_vals_dc
        self.toymc_targeted_vals_comp = args.toymc_targeted_vals_comp
        ## Analysis, Plots
        self.plot_data = args.plot_data
        self.plot_components = args.plot_components
        self.plot_fit_input = args.plot_fit_input
        self.plot_fit_result = args.plot_fit_result
        self.plot_show = args.plot_show
        self.multitrace_analysis = args.multitrace_analysis
        self.combined_groups = args.combined_groups
        self.prior_unc_mult = args.prior_unc_mult[0]
        self.prior_unc_mult_comp = args.prior_unc_mult_comp[0] 
        self.prior_unc_uniform = args.prior_unc_uniform
        self.high_prior_unc_comp = args.high_prior_unc_comp
        self.high_prior_comp = args.high_prior_comp
        self.high_prior_dc = args.high_prior_dc
        self.high_prior_mult = args.high_prior_mult[0]      
        ## Data
        self.data_cal = args.data_cal
        self.data_cal_source = args.data_cal_source[0]

        # Some checks
        if self.mcmc_random_seed:
            self.seed_number = np.random.randint(1000000001)
        else:
            self.seed_number = self.mcmc_seed_number[0]
        self.trace_dirname = self.model_dirname + '/' + 'trace_' + str(self.seed_number)
        if args.model_dirname == None:
            sys.exit('Error: Settings.__init__(): model_dirname must be specified')
        if self.mcmc_draws <= self.mcmc_warmup:
            sys.exit('Error: Settings.__init__(): mcmc_draws <= mcmc_warmup')

    def InitDistributionSettings(self):
        """
        Ranges and binnings for the various distribution types
        """
        # Raw simulations
        self.sim = DistStruct(min = 0., max = 10000., bin_wid = 1.)
        # Default
        self.dft = DistStruct(min = 100., max = 2620., bin_wid = 1.)
        # self.dft = DistStruct(min = 0., max = 2620., bin_wid = 1.)
        # Expected
        self.exp = DistStruct(min = 100., max = 2620., bin_wid = 1.)
        # self.exp = DistStruct(min = 0., max = 2620., bin_wid = 1.)
        # Fit engine
        self.fit = DistStruct(min = 100., max = 2620., bin_wid = 1.)
        # self.fit = DistStruct(min = 0., max = 2620., bin_wid = 1.)
        if self.fit_range[0] < self.fit.min or self.fit_range[1] > self.fit.max:
            sys.exit('Error: Settings.InitDistributionSettings(): self.fit_range[0] < self.fit.min or self.fit_range[1] > self.fit.max')
        # self.fit.min_dft_i, self.fit.max_dft_i = FindBin(self.fit.min, self.dft.bin_centers, self.dft.bin_wid), None # array[i:None] = array[i:] # to convert from dft to fit
        self.fit.min_dft_i = FindBin(self.fit_range[0], self.dft.bin_centers, self.dft.bin_wid)
        if self.fit_range[1] == self.fit.max:
            self.fit.max_dft_i = None
        else:
            self.fit.max_dft_i = FindBin(self.fit_range[1], self.dft.bin_centers, self.dft.bin_wid)
        self.fit.peaks_list = [238.6,583.2,911.2,2614.5,  295.2,351.9,609.3,1764.5,  1460.8,  1173.2,1332.5,  175.0,180.1,199.7] # Th, U, K, Co, Pb (rand E's from ~200 keV hump)
        self.fit.peaks_i = []
        for val in self.fit.peaks_list:
            self.fit.peaks_i.append(FindBin(val, self.fit.bin_centers, self.fit.bin_wid))
        # Bin Edges for Variable Binning (up to 3007 keV)
        if self.variable_bin_size:
            fname = '/Users/crhaufe/bgmodeling/DS5_bins.pkl'
            data = pl.load(open(fname, 'rb'))
            bins = data['MJD']
            var_bin_edges_floats = bins[:555]
            self.var_bin_edges = []
            for x in range(len(var_bin_edges_floats)):
                self.var_bin_edges.append(round(var_bin_edges_floats[x]))

        self.SetBinning(bin_wid = self.distribution_bin_wid)

    def SetBinning(self, min = None, max = None, bin_wid = None):
        """
        Set the default binning, and automatically update the dependent binnings
        kwargs are any of min, max, bin_wid
        """
        dft, exp, fit = self.dft, self.exp, self.fit

        # Default
        if min != None: dft.min = min
        if max != None: dft.max = max
        if bin_wid != None: dft.bin_wid = bin_wid
        dft.UpdateDerived()
        # Expected
        exp.min, exp.max, exp.bin_wid = dft.min, dft.max, dft.bin_wid
        exp.UpdateDerived()
        # Fit engine
        fit.bin_wid = dft.bin_wid # leave the fit range alone
        fit.UpdateDerived()
        if self.fit_range[0] < self.fit.min or self.fit_range[1] > self.fit.max:
            sys.exit('Error: Settings.InitDistributionSettings(): self.fit_range[0] < self.fit.min or self.fit_range[1] > self.fit.max')
        self.fit.min_dft_i = FindBin(self.fit_range[0], self.dft.bin_centers, self.dft.bin_wid)
        if self.fit_range[1] == self.fit.max:
            self.fit.max_dft_i = None
        else:
            self.fit.max_dft_i = FindBin(self.fit_range[1], self.dft.bin_centers, self.dft.bin_wid)
        self.fit.peaks_i = []
        for val in self.fit.peaks_list:
            self.fit.peaks_i.append(FindBin(val, self.fit.bin_centers, self.fit.bin_wid))

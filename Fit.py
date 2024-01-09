"""
Main routine for the FitSpectra package.
"""

import os
import sys
import json
import subprocess
import numpy as np
import pandas as pd
import argparse

import Management.Preprocessor as Preprocessor
import Management.Settings as Settings
import Tools.PlotTools as PlotTools
import Tools.TraceTools as TraceTools
import Classes.Model as Model
import Classes.ModelUnpooled as ModelUnpooled
import Classes.ModelPooled as ModelPooled
import Classes.ModelHierarchical as ModelHierarchical

def main(model, settings):
    """
    """
    st = settings

    # Instantiate PlotTools
    pt = PlotTools.PlotTools(st)
    pt.SetModel(model)
    pt.SetComponentColorList()

    # Print and plot gathered model
    print('Created Model instance:')
    for submodel in model.submodel_list:
        # Print status
        print('    %s' % submodel.name)
        print('        exposure = %.5f +/- %.5f (%s)' % (submodel.exposure, submodel.exposure_uncert, submodel.exposure_units) )
        # print('        exposure tot (0,2) = %.2f +/- %.2f (%s)' % (submodel.exposure, submodel.exposure_uncert, submodel.exposure_units) )
        # print('        exposure nat (0) = %.2f +/- %.2f (%s)' % (submodel.exposure_nat, submodel.exposure_nat_uncert, submodel.exposure_units) )
        # print('        exposure enr (2) = %.2f +/- %.2f (%s)' % (submodel.exposure_enr, submodel.exposure_enr_uncert, submodel.exposure_units) )

        print('        Components:')
        for component in submodel.component_list:
            print('            %s' % component.name)
            # Point PlotTools instance to this component and plot
            if st.plot_components:
                pt.SetComponent(component)
                pt.PlotComponent('sim')
                pt.PlotComponent('sim', differential = True)
                pt.PlotComponent('dft')
                pt.PlotComponent('dft', differential = True)
                pt.PlotComponent('exp')
                pt.PlotComponent('exp', differential = True)
                pt.PlotComponent('fit')
                pt.PlotComponent('fit', differential = True)

        # Point PlotTools instance to this submodel and plot
        if st.plot_data:
            pt.SetSubModel(submodel)
            pt.PlotData()
            pt.PlotData(differential = True)
            pt.PlotData(normalize = True)
            pt.PlotData(normalize = True, differential = True)

    # Plot fit input
    if st.plot_fit_input:
        print('passing plot pre fit')
        pt.SetModel(model)
        pt.PlotExpected()
        #pt.PlotExpectedCombinedSubmodels()
        # pt.PlotExpectedCalString(submodel_name_substr = '101010')
        # pt.PlotExpectedCalString(submodel_name_substr = '101020')
        # pt.PlotExpectedCalString(submodel_name_substr = '101030')
        # pt.PlotExpectedCalString(submodel_name_substr = '101040')
        # pt.PlotExpectedCalString(submodel_name_substr = '101050')
        # pt.PlotExpectedCalString(submodel_name_substr = '101060')
        # pt.PlotExpectedCalString(submodel_name_substr = '101070')
        # pt.PlotExpectedCalString(submodel_name_substr = '102010')
        # pt.PlotExpectedCalString(submodel_name_substr = '102020')
        # pt.PlotExpectedCalString(submodel_name_substr = '102030')
        # pt.PlotExpectedCalString(submodel_name_substr = '102040')
        # pt.PlotExpectedCalString(submodel_name_substr = '102050')
        # pt.PlotExpectedCalString(submodel_name_substr = '102060')
        # pt.PlotExpectedCalString(submodel_name_substr = '102070')

    # Run the Model object to sample the posterior or load saved samples
    model.Sample()
    # Do quick analyses and plots using the Model object
    # model.Summary()
    # top ten expected
    # model.Summary(var_names = ['p_2v_bulk_EnrGe',\
    #     'p_Pb210_pbbrem_RadShieldPb',\
    #     'p_Co60_bulk_RadShieldCuOuter',\
    #     'p_K40_bulk_RadShieldPb',\
    #     'p_Co60_bulk_DUCopperSpringClipCo60',\
    #     'p_U238_bulk_RadShieldPb',\
    #     'p_2v_bulk_NatGe',\
    #     'p_K40_bulk_M2CPHVCables',\
    #     'p_Rn222_surf_N2',\
    #     'p_U238_bulk_LMFEs',\
    # # others of interest
    #     'p_Co60_bulk_NatGe',\
    #     'p_Th232_bulk_M1CrossarmHVCables',\
    #     'p_Th232_bulk_M1CrossarmSigCables',\
    #     'p_Th232_bulk_M1CPHVCables',\
    #     'p_Th232_bulk_M1CPSigCables',\
    #     'p_Th232_bulk_M1StringHVCables',\
    #     'p_Th232_bulk_M1StringSigCables',\
    #     'p_Th232_bulk_M2CrossarmHVCables',\
    #     'p_Th232_bulk_M2CrossarmSigCables',\
    #     'p_Th232_bulk_M2CPHVCables',\
    #     'p_Th232_bulk_M2CPSigCables',\
    #     'p_Th232_bulk_M2StringHVCables',\
    #     'p_Th232_bulk_M2StringSigCables',\
    #     'p_Th232_bulk_M1DUCopper',\
    #     'p_Th232_bulk_M2DUCopper',\
    #     'p_Th232_bulk_M1StringCopper',\
    #     'p_Th232_bulk_M2StringCopper',\
    #     'p_Th232_surf_M1DUCopper',\
    #     'p_Th232_surf_M2DUCopper',\
    #     'p_Th232_surf_M1StringCopper',\
    #     'p_Th232_surf_M2StringCopper'])

    # model.TracePlot(varnames = ['p_2v_bulk_EnrGe',\
    #     'p_Pb210_pbbrem_RadShieldPb'])

    # model.Summary(var_names = ['p_Pb210_pbbrem_RadShieldPb']) # 'p_Pb210_pbbrem_RadShieldPb_pbbrem_02_1_DS0'
    # # model.GraphViz()
    # # Do some other quick analyses and plots using the Model object
    # # model.TracePlot()
    # # model.ForestPlot()
    # # model.PosteriorPlot()
    # # Do some other quick analyses and plots using the Model object, on spec components/params
    # # import pymc3 as pm
    # # component_name, prior_rv_name = 'Component_Pb210_pbbrem_RadShieldPb_pbbrem_02_1_DS0', 'p_Pb210_pbbrem_RadShieldPb'
    # # prior_loc, prior_scale = model.submodel_list[0].dag_df[component_name]['prior_loc'], model.submodel_list[0].dag_df[component_name]['prior_scale']
    # # model.TracePlot(varnames = [prior_rv_name], priors = [ pm.TruncatedNormal.dist(mu = prior_loc, sd = prior_scale, lower = 0.) ], combined = True)
    # # # model.ForestPlot(varnames = [prior_rv_name])
    # # model.PosteriorPlot(varnames = [prior_rv_name])
    #
    # Instantiate TraceTools
    tr = TraceTools.TraceTools(st)
    #
    # if False:
    # Draw posterior predictive samples
    nsamples = 100
    #nsamples_per_loop = 100
    #nloops = int(total_samples/nsamples_per_loop)
    #tr.SetModel(model)
    #tr.SamplePosteriorPredictive(trace_type = 'means', samples = 1, size = 1000)
    #if not os.path.exists(st.model_dirname+'/PPC_Plots/ppcs/ppc_%s.pkl' % str(samples)):
    #    print('Creating ' +st.model_dirname+'/PPC_Plots/ppcs/ppc_%s.pkl' % str(samples))
    #    tr.SamplePosteriorPredictive(trace_type = 'trace', samples = samples, size = 1, save = True)
    #else:
    #    model.ppc_d = None
    #pt.SetModel(model)
    #pt.PlotPosteriorPredictive(samples = samples)
    #
    # Gather trace and do analysis, gather point estimates & intervals, determine convergence (TraceTools)
    tr.SetModel(model)
    #tr.PrintDivergences()
    #pd_trace = tr.GetTraceDataFrame() #Enable if you need to save the trace as a pandas dataframe retroactively
    #pd_trace.to_pickle(st.trace_dirname + "/trace.pkl")
    tr.CalcPointEstimates()
    tr.CalcHPDs()
    tr.PrintConvergenceInfo()

    #~~~~~~~~~~~CODE BLOCK FOR CALCULATING MARGINAL LIKELIHOODS~~~~~~~~~~~~~~~~~~
    #samples = tr.ImportanceSampling(nsamples)
    #marg_likelihood_v2, skip_value = tr.CalculateMarginalLikelihood_v2(samples)

    #print(marg_likelihood_v2)
    #print("Skip value: " + str(skip_value))

    #for component in submodel.component_list:
    #  if component.floated: 
    #    floating_comp = component.name
    #    break
    #tmp_name = floating_comp.lstrip("Component_Th_")
    #tmp_name_partitioned = tmp_name.partition("_")
    #model_name = tmp_name_partitioned[0]
    #csv_name = 'marginal_likelihoods_10000_m1_looseunc.csv'

    #Code for pandas df
    #if model_name == 'M1CPInterfaceCavityBottomSurface':
    #  ml_df = pd.DataFrame(marg_likelihood_v2, index = [0]).T.reset_index()
    #  ml_df.columns = ['Submodel Name', model_name]
    #  ml_df.to_csv(csv_name) 
    #else:  
    #  ml_df = pd.read_csv(csv_name)
    #  ml_df[model_name] = ml_df['Submodel Name'].map(marg_likelihood_v2)
    #  ml_df2 = ml_df.iloc[: , 1:]
    #  ml_df2.to_csv(csv_name)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # # tr.CalcCovCorrMatrices()
    #
    # # Plot posteriors (PlotTools)
    pt.SetModel(model)
    # pt.PlotPosteriors(kde = True)
    # pt.PlotPosteriors(kde = False)

    # pt.PlotPosterior(component_name = 'Component_2v_bulk_EnrGe_bulk_02_2_DS6', kde = True)

    # pt.PlotPosterior(component_name = 'Component_2v_bulk_EnrGe_bulk_02_1_DS6', kde = True)
    # pt.PlotPosterior(component_name = 'Component_Pb210_pbbrem_RadShieldPb_pbbrem_02_2_DS6', kde = True)
    # pt.PlotPosterior(component_name = 'Component_Pb210_pbbrem_RadShieldPb_pbbrem_02_1_DS0', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_2v_bulk_EnrGe_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_Pb210_pbbrem_RadShieldPb_pbbrem_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_2v_bulk_NatGe_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_Co60_bulk_RadShieldCuOuter_bulk_02_1_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_U238_bulk_RadShieldPb_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_Rn222_surf_N2_surf_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_Th232_bulk_RadShieldPb_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_U238_bulk_M1CPHVCables_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_Th232_bulk_M1CPHVCables_bulk_02_2_DS6', kde = True)
    # # pt.PlotPosterior(component_name = 'Component_K40_bulk_RadShieldPb_bulk_02_2_DS6', kde = True)
    # pt.PlotPosterior(component_name = 'Component_Co60_bulk_NatGe_bulk_02_1_DS6', kde = True)
    # # pt.PlotForestPlot()
    #pt.PlotForestPlotForAllDecayChains()
    #pt.PlotIntegratedCountsDecayChain('Th232')
    pt.PlotIntegratedCountsPlotForAllDecayChains()
    #
    # pt.PrintTopResult()
    # pt.PrintTopExpected()
    #
    # if False:
    #     # Plot cov and corr matrices
    #     pt.SetModel(model)
    #     pt.PlotCovMatrix()
    #     pt.PlotCorrMatrix()
    #
    # Plot fit result (PlotTools)
    if st.plot_fit_result:
        pt.SetModel(model)
        #pt.PlotResult() #uncomment later -Chris H. 2-11-21
        pt.PlotResultCombinedSubmodels(normalize = True, differential = True)
    #
    # # Draw posterior predictive samples (Model)
    #
    # # Plot posterior predictive samples

    if st.plot_show:
        pt.Show()

##########################################
# main function
##########################################

if __name__ == "__main__":
    """
    Use:
        $ python Fit.py --help
        $ python Fit.py --model_dirname ./Test/TestModel
        $ python Fit.py --model_dirname ./Tests/TestModel/ --model_debug
                        --model_type unpooled --mcmc_draws 5000 --mcmc_warmup 0
                        --mcmc_chains 3 --mcmc_step_method NUTS --distribution_bin_wid 1.0
                        --toymc --toymc_draws 10000
                        ...
    """
    # Parse command line options and arguments
    parser = argparse.ArgumentParser(description = 'Arguments to Fit.py')
    ## Model
    parser.add_argument('--model_dirname', dest = 'model_dirname', type = str, nargs = 1,\
        help = 'dirname of user\'s model (str)')
    parser.add_argument('--model_debug', dest = 'model_debug', action = 'store_true', default = False,\
        help = 'debug model (bool)')
    parser.add_argument('--model_type', dest = 'model_type', type = str, nargs = 1, default = ['unpooled'],\
        help = 'model type for DAG construction (str) ... options are \'unpooled\',\'pooled\',\'hierarchical\'')
    ## MCMC, Sampling
    parser.add_argument('--mcmc_draws', dest = 'mcmc_draws', type = int, nargs = 1, default = [5000],\
        help = 'Number of MCMC draws (int)')
    parser.add_argument('--mcmc_warmup', dest = 'mcmc_warmup', type = int, nargs = 1, default = [0],\
        help = 'Number of MCMC draws to discard as warmup (int)')
    parser.add_argument('--mcmc_chains', dest = 'mcmc_chains', type = int, nargs = 1, default = [3],\
        help = 'Number of MCMC chains to run (int)')
    parser.add_argument('--mcmc_cores', dest = 'mcmc_cores', type = int, nargs = 1, default = [2],\
        help = 'Number of cores to run MCMC code on in parallel (int)')
    parser.add_argument('--mcmc_step_method', dest = 'mcmc_step_method', type = str, nargs = 1, default = ['NUTS'],\
        help = 'MCMC Sampling algorithm to use (str)')
    parser.add_argument('--mcmc_rand_testvals', dest = 'mcmc_rand_testvals', action = 'store_true', default = False,\
        help = 'Assign random testvals for model (bool)')
    parser.add_argument('--mcmc_startvals_type', dest = 'mcmc_startvals_type', type = str, nargs = 1, default = ['default'],\
        help = 'MCMC start values (str) ... options are \'default\',\'map\',\'test_point\'')
    parser.add_argument('--mcmc_target_accept', dest = 'mcmc_target_accept', type = float, nargs = 1, default = [0.8],\
        help = 'Manually set the target acceptance rate per step (float)')
    parser.add_argument('--mcmc_random_seed', dest = 'mcmc_random_seed', action = 'store_true', default = False,\
        help = 'Set a random seed value for the sampler (bool)')
    parser.add_argument('--mcmc_seed_number', dest = 'mcmc_seed_number', type = int, nargs = 1, default = [0],\
        help = 'Set a specific seed value for the sampler (int)')
    parser.add_argument('--mcmc_unconstrained', dest = 'mcmc_unconstrained', type = str, nargs = 1, default = 'None',\
        help = 'name of random variable that will have an unconstrained half-flat prior (str)')
    parser.add_argument('--mcmc_all_flat', dest = 'mcmc_all_flat', action = 'store_true', default = False,\
        help = 'Set all the priors to have half flat distributions, truncated at zero (bool)')
    ##### to do: perhaps one for grouping type
    ## Fit Engine
    parser.add_argument('--fit_peaks', dest = 'fit_peaks', action = 'store_true', default = False,\
        help = 'Fit engine fits only to certain bins containing known peaks (bool)')
    parser.add_argument('--fit_range', dest = 'fit_range', type = float, nargs = 2, default = [100.,3000.],\
        help = 'Fit range in keV (float)')
    ##### to do: perhaps have this option be more like fit_custom_bins or fit_custom_values
    ## Distributions
    parser.add_argument('--distribution_bin_wid', dest = 'distribution_bin_wid', type = float, nargs = 1, default = [1.],\
        help = 'Bin width for distributions (float)')
    parser.add_argument('--variable_bin_size', dest = 'variable_bin_size', action = 'store_true', default = False,\
        help = 'Use distributions with Anna and Micahs variable binning scheme (bool)')
    parser.add_argument('--kco_set_number', dest = 'kco_set_number', type = int, nargs = 1, default = [0],\
        help = 'Select a particular set of potassium and cobalt priors to use for certain groups (int)')
    ## Toy MC
    parser.add_argument('--toymc', dest = 'toymc', action = 'store_true', default = False,\
        help = 'Generate and use toy MC data (bool)')
    parser.add_argument('--toymc_draws', dest = 'toymc_draws', type = int, nargs = 1, default = [10000],\
        help = 'Number of toy MC draws (int)')
    parser.add_argument('--toymc_mult', dest = 'toymc_mult', type = int, nargs = 1, default = [1],\
        help = 'Specify ratio of simulated dataset statistics to real data statistics (int)')
    parser.add_argument('--toymc_rand_vals', dest = 'toymc_rand_vals', action = 'store_true', default = False,\
        help = 'Assign random values for toy MC data sampling model (bool)')
    parser.add_argument('--toymc_targeted_vals', dest = 'toymc_targeted_vals', action = 'store_true', default = False,\
        help = 'Assign targeted values for toy MC data sampling model (bool)')
    parser.add_argument('--toymc_targeted_vals_mult', dest = 'toymc_targeted_vals_mult', type = float, nargs = 1, default = [1.0],\
        help = 'Multiplier on original prior value that generates targeted value for toy MC data sampling model (float)')
    parser.add_argument('--toymc_targeted_vals_dc', dest = 'toymc_targeted_vals_dc', type = str, nargs = '*', default = ['None'],\
        help = 'Decay chain(s) to recieve targeted value for toy MC data sampling model.  If not specified, targeted values applied to all dcs. (str)')
    parser.add_argument('--toymc_targeted_vals_comp', dest = 'toymc_targeted_vals_comp', type = str, nargs = '*', default = ['None'],\
        help = 'Component(s) to recieve targeted value for toy MC data sampling model.  If not specified, targeted values applied to specified dc. (str)')
    ## Analysis, Plots
    parser.add_argument('--plot_data', dest = 'plot_data', action = 'store_true', default = False,\
        help = 'Plot the data (bool)')
    parser.add_argument('--plot_components', dest = 'plot_components', action = 'store_true', default = False,\
        help = 'Plot the mixture components (bool)')
    parser.add_argument('--plot_fit_input', dest = 'plot_fit_input', action = 'store_true', default = False,\
        help = 'Plot the fit inputs/expected (bool)')
    parser.add_argument('--plot_fit_result', dest = 'plot_fit_result', action = 'store_true', default = False,\
        help = 'Plot the fit result/inferred (bool)')
    parser.add_argument('--plot_show', dest = 'plot_show', action = 'store_true', default = False,\
        help = 'Display the plots (bool)')
    parser.add_argument('--multitrace_analysis', dest = 'multitrace_analysis', action = 'store_true', default = False,\
        help = 'Analyze model results with multiple traces (bool)')
    parser.add_argument('--combined_groups', dest = 'combined_groups', action = 'store_true', default = False,\
        help = 'Combine model results into a smaller number of groups (bool)')
    parser.add_argument('--prior_unc_mult', dest = 'prior_unc_mult', type = float, nargs = 1, default = [1.0],\
        help = 'Multiply the uncertainty of the prior distribution by some integer factor (float)')
    parser.add_argument('--prior_unc_mult_comp', dest = 'prior_unc_mult_comp', type = str, nargs = 1, default = 'None',\
        help = 'Component to recieve multiplier on prior uncertainty value (str)')
    parser.add_argument('--prior_unc_uniform', dest = 'prior_unc_uniform', action = 'store_true', default = False,\
        help = 'Make all prior uncertainties equal to Th232_RadShielCuInner uncertainty (bool)')
    parser.add_argument('--high_prior_mult', dest = 'high_prior_mult', type = float, nargs = 1, default = [1.0],\
        help = 'Multiplier on original prior value (float)')
    parser.add_argument('--high_prior_dc', dest = 'high_prior_dc', type = str, nargs = '*', default = ['None'],\
        help = 'Decay chain(s) to recieve multiplier on original prior value (str)')
    parser.add_argument('--high_prior_comp', dest = 'high_prior_comp', type = str, nargs = '*', default = ['None'],\
        help = 'Component(s) to recieve multiplier on original prior value (str)')
    parser.add_argument('--high_prior_unc_comp', dest = 'high_prior_unc_comp', type = str, nargs = '*', default = ['None'],\
        help = 'Component(s) to recieve 10x multiplier on original prior uncertainty value (str)')
    ## Data
    parser.add_argument('--data_cal', dest = 'data_cal', action = 'store_true', default = False,\
        help = 'Use calibration data rather than background data (bool)')
    parser.add_argument('--data_cal_source', dest = 'data_cal_source', type = int, nargs = 1, default = [1],\
        help = 'The module number of the calibration source (int) ... options are \'1\',\'2\'')

    print('Parsed args:\n    ', parser.parse_args())

    # Instantiate Settings
    st = Settings.Settings(parser.parse_args())

    # Print parsed command line argument
    print('Working with user-created model directory:\n    %s' % st.model_dirname)

    # Create Model.json
    model_dict = Preprocessor.main(st)
    # print(json.dumps(model_dict, indent = 2))
    # Get model_dict from Model.json
    # with open(model_dirname + '/' + 'Model.json') as file:
    #     model_dict = json.load(file)

    # Instantiate Model object
    if st.model_type == 'unpooled': model = ModelUnpooled.ModelUnpooled(model_dict, st)
    if st.model_type == 'pooled': model = ModelPooled.ModelPooled(model_dict, st)
    if st.model_type == 'hierarchical': model = ModelHierarchical.ModelHierarchical(model_dict, st)

    if st.model_debug: model.Debug()

    print(model.pymc_model.test_point)

    main(model, st)

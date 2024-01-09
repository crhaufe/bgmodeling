"""
"""
import sys
import os
import copy
import glob
import operator
import math as mt
import numpy as np
import pickle as pl
from pymc3.plots.kdeplot import fast_kde
from natsort import natsorted
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
plt.rc('font', family = 'serif', serif = 'DejaVu Serif')
plt.rc('lines', linewidth = 1.5)
plt.rc('axes', titlesize = 17)
plt.rc('axes', labelsize = 17)
plt.rc('xtick', labelsize = 15)
plt.rc('ytick', labelsize = 15)
plt.rc('legend', fontsize = 15)
import seaborn as sns

import Management.Private_ConfigData as ConfigData
cfgd = ConfigData.ConfigData()

import Tools.TraceTools as TraceTools

# SOME GLOBAL VARIABLES
sim_data_cut_dict = {1:'RD',2:'RMD',3:'RMAD',4:'RAD',6:'RmD'}
detector_type_dict = {'0':'Nat','2':'Enr','02':'All','20':'All',None:'All'}
openness_dict = {'open':'open','blind':'blind','openblind':'open+blind','blindopen':'open+blind',None:'open+blind'}

sns.set(style="white")
cmap = sns.diverging_palette(220, 10, as_cmap=True)

class PlotTools:
    """
    """
    def __init__(self, settings):
        self.settings = settings

        self.c_list = None
        self.c_list_dict = None
        self.component_varname_dict = None

    def Show(self):
        plt.show()

    def SetModel(self, model):
        self.model = model
        self.submodels_n = len(model.submodel_list)

    def SetSubModel(self, submodel):
        self.submodel = submodel
        self.name = submodel.name
        self.dataset = self.submodel.submodel_dict['data']['dataset']
        self.openness = self.submodel.submodel_dict['data']['openness']
        self.cut = self.submodel.submodel_dict['data']['cut']
        self.detector_type = self.submodel.submodel_dict['data']['detector_type']
        self.exposure = self.submodel.exposure
        self.exposure_units = self.submodel.exposure_units
        self.module = self.submodel.submodel_dict['data']['module']
        self.components_n = len(submodel.component_list)

    def SetComponent(self, component):
        self.component = component
        self.name = component.name
        self.config = self.component.component_dict['config']
        self.cut = self.component.component_dict['cut']
        self.detector_type = self.component.component_dict['detector_type']

    def SetComponentColorList(self):
        """
        Must follow SetModel()
        """
        model = self.model

        varname_list = []
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated:
                    for rv_name_type in ['hp_rv_name', 'p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only use each var once
                        if varname in varname_list: continue
                        else: varname_list.append(varname)

        n = len(varname_list)
        self.c_list = self.GetColorList(n)
        self.c_list_dict = {}
        for i, varname in enumerate(varname_list):
            self.c_list_dict[varname] = self.c_list[i]

    def SetComponentVarnameDict(self):
        """
        Must follow SetModel()
        """
        model = self.model

        self.component_varname_dict = {}
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated:
                    for rv_name_type in ['p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only use each var once
                        if varname in self.component_varname_dict: continue
                        else: self.component_varname_dict[component.name] = varname

    def GetColorList(self, n):
        # c_list = []
        # for i in range(n):
        #     r,g,b = np.random.rand(3)
        #     c_list.append( (r, g, b, 1) ) # using RGBA tuples
        # return c_list

        r = np.random.choice(n, size = n, replace = False)/n
        g = np.random.choice(n, size = n, replace = False)/n
        b = np.random.choice(n, size = n, replace = False)/n
        c_list = []
        [c_list.append( (r[i], g[i], b[i], 1) ) for i in range(n)]
        return c_list

    def GetDecayChainColor(self, dC, annacolors = True):
        """
        Get the color for a plot based on the decay chain
        """
        if annacolors:
          colorDict = {
                      'Th': 'tab:green',
                      'U': 'tab:gray',
                      '228Th': 'tab:green',
                      'Rn': 'midnightblue',
                      'Pb': 'tab:red',
                      'PbBrem': 'tab:red',
                      'Co': 'tab:purple',
                      '57Co': 'tab:cyan',
                      '68Ge': 'tab:olive',
                      'K': 'tab:pink',
                      '0v': 'tab:orange',
                      '2v': 'tab:orange',
                      '54Mn': 'tab:brown',
                      'DCR': 'tab:orange'
                      }
        else:
          colorDict = {
                      'Th232': 'tab:red',
                      'U238': 'tab:green',
                      'Th228': 'tab:red',
                      'Rn222': 'tab:brown',
                      'Pb210': 'tab:olive',
                      'Co60': 'tab:orange',
                      'Co57': 'tab:blue',
                      'Ge68': 'tab:cyan',
                      'K40': 'tab:purple',
                      '0v': 'tab:gray',
                      '2v': 'tab:gray',
                      'Mn54': 'midnightblue',
                      'DCR': 'tab:pink'
                      }
        return colorDict[dC]

    def PlotData(self, normalize = False, differential = False):
        """
        Must follow SetSubModel()
        """
        st = self.settings
        name, dataset, openness, cut, detector_type, exposure, exposure_units = \
            self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units

        figName = 'fig_%s' % name.replace('SubModel', 'data')
        figName += '_norm' if normalize else '_counts'
        figTitle = '%s %s\n%sGe %s' % (dataset, openness_dict[openness], detector_type_dict[detector_type], sim_data_cut_dict[cut])
        figXLabel = 'energy (%.1f keV bins)' % st.dft.bin_wid
        figYLabel = 'c/kg/yr' if normalize else 'counts'
        dist = self.submodel.rate_dist if normalize else self.submodel.count_dist
        bin_centers = st.dft.bin_centers
        if differential:
            figName += '_diff'
            figYLabel += '/%.1fkeV' % st.dft.bin_wid
            dist = dist / st.dft.bin_wid

        plt.figure(figName)
        plt.title(figTitle)
        plt.xlabel(figXLabel)
        plt.ylabel(figYLabel)
        plt.step(bin_centers, dist, where = 'mid', c = 'k', \
            label = 'data %.2f %s' % (exposure, exposure_units) )
        plt.legend()

    def PlotComponent(self, dist_str = 'dft', differential = False):
        """
        Must follow SetComponent()
        dist_str is one of  'sim', 'dft', 'exp', 'fit'
        """
        st = self.settings
        name, config, cut, detector_type = \
            self.name, self.config, self.cut, self.detector_type

        figName = 'fig_%s' % name.replace('Component', dist_str)
        figTitle = '%s\n%sGe %s' % (config, detector_type_dict[detector_type], sim_data_cut_dict[cut])
        figXLabel = 'energy (%.1f keV bins)' % st.dft.bin_wid

        if dist_str == 'sim':
            figYLabel = self.component.sim_units
            dist = self.component.sim_dist
            bin_centers = st.sim.bin_centers
            if differential:
                figName += '_diff'
                figYLabel += '/%.1fkeV' % st.sim.bin_wid
                dist = dist / st.sim.bin_wid
        elif dist_str == 'dft':
            figYLabel = self.component.dft_units
            dist = self.component.dft_dist
            bin_centers = st.dft.bin_centers
            if differential:
                figName += '_diff'
                figYLabel += '/%.1fkeV' % st.dft.bin_wid
                dist = dist / st.dft.bin_wid
        elif dist_str == 'exp':
            figYLabel = self.component.exp_units
            dist = self.component.exp_dist
            bin_centers = st.exp.bin_centers
            if differential:
                figName += '_diff'
                figYLabel += '/%.1fkeV' % st.exp.bin_wid
                dist = dist / st.exp.bin_wid
        elif dist_str == 'fit':
            figYLabel = self.component.fit_units
            dist = self.component.fit_dist
            bin_centers = st.fit.bin_centers
            if differential:
                figName += '_diff'
                figYLabel += '/%.1fkeV' % st.fit.bin_wid
                dist = dist / st.fit.bin_wid
        else:
            sys.exit('Error: PlotTools::PlotDist(): dist_str %s not recognized' % dist_str)

        plt.figure(figName)
        plt.title(figTitle)
        plt.xlabel(figXLabel)
        plt.ylabel(figYLabel)
        plt.step(bin_centers, dist, where = 'mid', c = 'k', \
            label = '%s' % name)
        plt.legend()

    def PlotExpectedCalString(self, submodel_name_substr = '101010', normalize = False, differential = False):
        """
        Must follow SetModel()
        """
        st = self.settings
        model = self.model

        # Create the figure
        fig_name = 'fig_model_expected_M%dCalSource_%s_RD_open_02_5b' % (st.data_cal_source, submodel_name_substr)
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)

        submodels_n_substr = 0
        string_submodel_list = []
        for i, submodel in enumerate(model.submodel_list):
            if submodel_name_substr in submodel.name:
                submodels_n_substr += 1
                string_submodel_list.append(submodel)
        rows, cols = 5, submodels_n_substr
        gs = gridspec.GridSpec(rows, cols)
        gs.update(top=0.965,bottom=0.085,left=0.06,right=0.98,hspace=0.2,wspace=0.2)

        ax_spectra, ax_resid = [], []
        for i, submodel in enumerate(string_submodel_list):
            # Setup the figure
            if i == 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i]) )
            if i > 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i], sharey = ax_spectra[0]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i], sharey = ax_resid[0]) )
                plt.setp(ax_spectra[i].get_yticklabels(), visible = False)
                plt.setp(ax_resid[i].get_yticklabels(), visible = False)
            plt.setp(ax_spectra[i].get_xticklabels(), visible = False)
            ax_spectra[i].set_xlim(st.exp.min,st.exp.max)
            ax_resid[i].set_xlim(st.exp.min,st.exp.max)

            # Label the figure
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            # title = '%s %s\n%sGe %s' % (dataset, openness_dict[openness], detector_type_dict[detector_type], sim_data_cut_dict[cut])
            xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
            ylabel = 'counts'
            if normalize: ylabel = 'c/kg/yr'
            if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
            # ax_spectra[i].set_title(title)
            ax_resid[i].set_xlabel(xlabel)
            ax_spectra[0].set_ylabel(ylabel)
            ax_resid[0].set_ylabel('(data-model)/$\sigma_{data}$')

            # Draw the data and total distributions
            observed_dist = submodel.count_dist
            fixed_dist = np.sum([component.fit_dist * component.prior_loc for component in submodel.component_list if not component.floated], axis = 0)
            floated_dist = np.sum([component.exp_dist for component in submodel.component_list if component.floated], axis = 0)
            if normalize:
                observed_dist = observed_dist / exposure
                fixed_dist = fixed_dist / exposure
                floated_dist = floated_dist / exposure
            if differential:
                observed_dist = observed_dist / st.exp.bin_wid
                fixed_dist = fixed_dist / st.exp.bin_wid
                floated_dist = floated_dist / st.exp.bin_wid
            if np.sum(fixed_dist) == 0.:
                print('PlotTools::PlotExpected(): no fixed_dist')
                fixed_dist = np.zeros(shape = (st.exp.bins_n,))
            # ax_spectra[i].step(st.exp.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
                # label = 'Model to-be-fixed total')
            # ax_spectra[i].step(st.exp.bin_centers, floated_dist, where = 'mid', c = 'blue', \
                # label = 'Model to-be-floated total')
            ax_spectra[i].step(st.exp.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
                label = 'Model total')
            ax_spectra[i].scatter(st.exp.bin_centers, observed_dist, c = 'k', s = 1., \
                label = 'Data %.2f %s' % (exposure, exposure_units), zorder = 10)

            # print('PlotTools::PlotExpected():')
            # print('    exposure = %.3f' % exposure)
            # print('    np.sum(observed_dist) = %.3f' % np.sum(observed_dist))
            # print('    np.sum(fixed_dist + floated_dist) = %.3f' % np.sum(fixed_dist + floated_dist))

            cpd = 'C' + str(submodel.detector[2]) + 'P' + str(submodel.detector[4]) + 'D' + str(submodel.detector[6])
            title = '%s %sGe' % (cpd, detector_type_dict[detector_type])
            ax_spectra[i].set_title(title)

            bboxProps = dict(boxstyle = 'square', facecolor = 'white', alpha = 1.)
            textStr = '%.5f kg*yr' % (exposure)
            ax_spectra[i].text(x = .96, y = .97, s = textStr, horizontalalignment = 'right', \
                verticalalignment = 'top', transform = ax_spectra[i].transAxes, fontsize = 12, bbox = bboxProps)

            # Draw the components
            # for j, component in enumerate(submodel.component_list):
            #     if component.floated:
            #         dist = component.exp_dist
            #         if normalize:
            #             dist = dist / exposure
            #         if differential:
            #             dist = dist / st.exp.bin_wid
            #         ax_spectra[i].step(st.exp.bin_centers, dist, where = 'mid', c = self.c_list[j], \
            #             label = component.name + ' expected')

            # # Draw the residuals
            # pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
            # ax_resid[i].scatter(st.exp.bin_centers, pulls, marker = 'o', s = 1., c = 'k')
            # # Draw the residuals hist from the right
            # pulls[pulls == -np.inf] = 0.
            # tmp_hist, tmp_bin_edges = np.histogram(a = pulls, bins = 'rice', density = False)
            # tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            # tmp_x_max = ax_resid[i].get_xlim()[1]
            # tmp_hist  = -1 * tmp_hist
            # tmp_hist_left = tmp_x_max
            # ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

            # Draw the residuals
            pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
            pulls = pulls[st.fit.min_dft_i:st.fit.max_dft_i]
            pulls_masked = np.ma.masked_where(observed_dist[st.fit.min_dft_i:st.fit.max_dft_i] == 0, pulls, copy=True) # mask zeros
            bin_centers_pulls_masked = np.ma.masked_where(observed_dist[st.fit.min_dft_i:st.fit.max_dft_i] == 0, st.fit.bin_centers[st.fit.min_dft_i:st.fit.max_dft_i], copy=True) # mask zeros
            # pulls_masked = np.ma.masked_where(observed_dist == 0, pulls, copy=True) # mask zeros
            # bin_centers_pulls_masked = np.ma.masked_where(observed_dist == 0, st.exp.bin_centers, copy=True) # mask zeros
            ax_resid[i].scatter(bin_centers_pulls_masked, pulls_masked, marker = 'o', s = 1., c = 'k')
            # Draw the residuals hist from the right
            pulls_for_hist = pulls_masked[~pulls_masked.mask]
            tmp_hist, tmp_bin_edges = np.histogram(a = pulls_for_hist, bins = 'rice', density = False)
            tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            tmp_x_max = ax_resid[i].get_xlim()[1]
            tmp_hist  = -1 * tmp_hist
            tmp_hist_left = tmp_x_max
            ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        ax_spectra[0].set_yscale("log", nonposy='clip')
        # fig = plt.figure('fig_model_expected_legend')
        # ax = fig.gca()
        # ax.legend(*ax_spectra[0].get_legend_handles_labels(), loc='center')
        # ax.axis('off')

    def PlotExpected(self, normalize = False, differential = False):
        """
        Must follow SetModel()
        """
        st = self.settings
        model = self.model

        # Create the figure
        fig_name = 'fig_model_expected'
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)

        rows, cols = 5, self.submodels_n
        gs = gridspec.GridSpec(rows, cols)
        gs.update(hspace = 0, wspace = 0)

        ax_spectra, ax_resid = [], []
        for i, submodel in enumerate(model.submodel_list):
            # Setup the figure
            if i == 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i]) )
            if i > 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i], sharey = ax_spectra[0]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i], sharey = ax_resid[0]) )
                plt.setp(ax_spectra[i].get_yticklabels(), visible = False)
                plt.setp(ax_resid[i].get_yticklabels(), visible = False)
            plt.setp(ax_spectra[i].get_xticklabels(), visible = False)
            ax_spectra[i].set_xlim(st.exp.min,st.exp.max)
            ax_resid[i].set_xlim(st.exp.min,st.exp.max)

            # Label the figure
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            title = '%s %s\n%sGe %s' % (dataset, openness_dict[openness], detector_type_dict[detector_type], sim_data_cut_dict[cut])
            xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
            ylabel = 'counts'
            if normalize: ylabel = 'c/kg/yr'
            if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
            ax_spectra[i].set_title(title)
            ax_resid[i].set_xlabel(xlabel)
            ax_spectra[0].set_ylabel(ylabel)
            ax_resid[0].set_ylabel('(data-model)/$\sigma_{data}$')

            # Draw the data and total distributions
            observed_dist = submodel.count_dist
            fixed_dist = np.sum([component.fit_dist * component.prior_loc for component in submodel.component_list if not component.floated], axis = 0)
            floated_dist = np.sum([component.exp_dist for component in submodel.component_list if component.floated], axis = 0)
            if normalize:
                observed_dist = observed_dist / exposure
                fixed_dist = fixed_dist / exposure
                floated_dist = floated_dist / exposure
            if differential:
                observed_dist = observed_dist / st.exp.bin_wid
                fixed_dist = fixed_dist / st.exp.bin_wid
                floated_dist = floated_dist / st.exp.bin_wid
            if np.sum(fixed_dist) == 0.:
                print('PlotTools::PlotExpected(): no fixed_dist')
                fixed_dist = np.zeros(shape = (st.exp.bins_n,))
            ax_spectra[i].step(st.exp.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
                label = 'Model to-be-fixed total')
            ax_spectra[i].step(st.exp.bin_centers, floated_dist, where = 'mid', c = 'blue', \
                label = 'Model to-be-floated total')
            ax_spectra[i].step(st.exp.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
                label = 'Model total')
            ax_spectra[i].scatter(st.exp.bin_centers, observed_dist, c = 'k', s = 1., \
                label = 'Data %.2f %s' % (exposure, exposure_units))

            print('PlotTools::PlotExpected():')
            print('    exposure = %.3f' % exposure)
            print('    np.sum(observed_dist) = %.3f' % np.sum(observed_dist))
            print('    np.sum(fixed_dist + floated_dist) = %.3f' % np.sum(fixed_dist + floated_dist))

            # Draw the components
            k = 0
            for j, component in enumerate(submodel.component_list):
                if component.floated:
                    dist = component.exp_dist
                    if normalize:
                        dist = dist / exposure
                    if differential:
                        dist = dist / st.exp.bin_wid
                    ax_spectra[i].step(st.exp.bin_centers, dist, where = 'mid', c = self.c_list[k], \
                        label = component.name + ' to-be-floated')
                    k += 1
            del k

            # # Draw the residuals
            # pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
            # ax_resid[i].scatter(st.exp.bin_centers, pulls, marker = 'o', s = 1., c = 'k')
            # # Draw the residuals hist from the right
            # pulls[pulls == -np.inf] = 0.
            # tmp_hist, tmp_bin_edges = np.histogram(a = pulls, bins = 'rice', density = False)
            # tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            # tmp_x_max = ax_resid[i].get_xlim()[1]
            # tmp_hist  = -1 * tmp_hist
            # tmp_hist_left = tmp_x_max
            # ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

            # Draw the residuals
            pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
            pulls_masked = np.ma.masked_where(observed_dist == 0, pulls, copy=True) # mask zeros
            bin_centers_pulls_masked = np.ma.masked_where(observed_dist == 0, st.exp.bin_centers, copy=True) # mask zeros
            ax_resid[i].scatter(bin_centers_pulls_masked, pulls_masked, marker = 'o', s = 1., c = 'k')
            # Draw the residuals hist from the right
            pulls_for_hist = pulls_masked[~pulls_masked.mask]
            tmp_hist, tmp_bin_edges = np.histogram(a = pulls_for_hist, bins = 'rice', density = False)
            tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            tmp_x_max = ax_resid[i].get_xlim()[1]
            tmp_hist  = -1 * tmp_hist
            tmp_hist_left = tmp_x_max
            ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        fig = plt.figure('fig_model_expected_legend')
        ax = fig.gca()
        ax.legend(*ax_spectra[0].get_legend_handles_labels(), loc='center')
        ax.axis('off')

    def PlotExpectedCombinedSubmodels(self, normalize = False, differential = False):
        """
        Must follow SetModel() and CalcPointEstimates()
        """
        st = self.settings
        model = self.model
        self.SetComponentVarnameDict()

        # Create the figure
        fig_name = 'fig_model_expectedcombinedsubmodels'
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)

        rows, cols = 5, 1
        gs = gridspec.GridSpec(rows, cols)
        gs.update(top=0.995,bottom=0.08,left=0.075,right=0.98,hspace=0.2,wspace=0.2)

        exposure_total = 0
        exposure_units_total = ''
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            exposure_total += exposure
            exposure_units_total = exposure_units

        ax_spectra, ax_resid = [], []
        # Setup the figure and dists
        ax_spectra.append( fig.add_subplot(gs[:2,0]) )
        ax_spectra.append( fig.add_subplot(gs[2:rows-1,0]) )
        ax_resid.append( fig.add_subplot(gs[rows-1,0], sharex = ax_spectra[0]) )
        plt.setp(ax_spectra[0].get_xticklabels(), visible = False)
        plt.setp(ax_spectra[1].get_xticklabels(), visible = False)
        ax_spectra[0].set_xlim(st.exp.min,st.exp.max)
        ax_spectra[1].set_xlim(st.exp.min,st.exp.max)
        ax_resid[0].set_xlim(st.exp.min,st.exp.max)

        observed_dist = np.zeros(shape=st.fit.bins_n)
        fixed_dist = np.zeros(shape=st.fit.bins_n)
        floated_dist = np.zeros(shape=st.fit.bins_n)
        dC_dist_dict = {}
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            dag_df = submodel.dag_df
            observed_dist += submodel.count_dist
            fixed_dist += np.sum([component.fit_dist * dag_df[component.name]['prior_loc'] for component in submodel.component_list if not component.floated], axis = 0)
            floated_dist += np.sum([component.exp_dist for component in submodel.component_list if component.floated], axis = 0)

            # Collect the decay chains, including floated and non-floated
            for j, component in enumerate(submodel.component_list):
                if component.floated:
                    tmp_dist = component.exp_dist
                if not component.floated:
                    tmp_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                dC = component.component_dict['decay_chain']
                if dC not in dC_dist_dict:
                    dC_dist_dict[dC] = np.zeros(shape=st.fit.bins_n)
                dC_dist_dict[dC] += tmp_dist

        if normalize:
            observed_dist = observed_dist / exposure_total
            fixed_dist = fixed_dist / exposure_total
            floated_dist = floated_dist / exposure_total
        if differential:
            observed_dist = observed_dist / st.exp.bin_wid
            fixed_dist = fixed_dist / st.exp.bin_wid
            floated_dist = floated_dist / st.exp.bin_wid
        if np.sum(fixed_dist) == 0.:
            print('PlotTools::PlotResult(): no fixed_dist')
            fixed_dist = np.zeros(shape = (st.fit.bins_n,))
        # ax_spectra[0].step(st.fit.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
        #     label = 'Model fixed total')
        # ax_spectra[0].step(st.fit.bin_centers, floated_dist, where = 'mid', c = 'blue', \
        #     label = 'Model floated total')
        # ax_spectra[0].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
        #     label = 'Model total')
        ax_spectra[0].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', color = 'lightgrey', \
            label = 'Model total')
        ax_spectra[0].fill_between(st.fit.bin_centers, fixed_dist + floated_dist, step='mid', color = 'lightgrey')
        ax_spectra[0].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
            label = 'Data %.4f %s' % (exposure_total, exposure_units_total), zorder = 100)
        ax_spectra[1].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', color = 'lightgrey', \
            label = 'Model total')
        ax_spectra[1].fill_between(st.fit.bin_centers, fixed_dist + floated_dist, step='mid', color = 'lightgrey')
        ax_spectra[1].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
            label = 'Data %.4f %s' % (exposure_total, exposure_units_total), zorder = 100)

        for dC in dC_dist_dict:
            tmp_dist = dC_dist_dict[dC]
            if normalize:
                tmp_dist = tmp_dist / exposure_total
            if differential:
                tmp_dist = tmp_dist / st.exp.bin_wid
            ax_spectra[0].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                label = dC + ' expected')
            ax_spectra[1].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                label = dC + ' expected')

        xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
        ylabel = 'counts'
        if normalize: ylabel = 'c/kg/yr'
        if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
        ax_spectra[0].set_ylabel(ylabel)
        ax_spectra[1].set_ylabel(ylabel)
        ax_resid[0].set_xlabel(xlabel)
        ax_resid[0].set_ylabel('(data-model)/$\sigma_{data}$')

        # Draw the residuals
        pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
        pulls = pulls[st.fit.min_dft_i:st.fit.max_dft_i]
        pulls_masked = np.ma.masked_where(observed_dist[st.fit.min_dft_i:st.fit.max_dft_i] == 0, pulls, copy=True) # mask zeros
        bin_centers_pulls_masked = np.ma.masked_where(observed_dist[st.fit.min_dft_i:st.fit.max_dft_i] == 0, st.fit.bin_centers[st.fit.min_dft_i:st.fit.max_dft_i], copy=True) # mask zeros
        ax_resid[0].scatter(bin_centers_pulls_masked, pulls_masked, marker = 'o', s = 1., c = 'k')
        # Draw the residuals hist from the right
        pulls_for_hist = pulls_masked[~pulls_masked.mask]
        tmp_hist, tmp_bin_edges = np.histogram(a = pulls_for_hist, bins = 'rice', density = False)
        tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
        tmp_x_max = ax_resid[0].get_xlim()[1]
        tmp_hist = -1 * tmp_hist
        tmp_hist_left = tmp_x_max
        ax_resid[0].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        ax_spectra[1].set_yscale("log", nonposy='clip')

        #ax_spectra[0].legend()

        fig = plt.figure('fig_model_expectedcombinedsubmodels_legend')
        ax = fig.gca()
        ax.legend(*ax_spectra[-1].get_legend_handles_labels(), loc='center') # prop={'size': 12}
        ax.axis('off')

        bins1 = observed_dist[st.fit.min_dft_i:st.fit.max_dft_i]
        bins2 = (fixed_dist + floated_dist)[st.fit.min_dft_i:st.fit.max_dft_i]
        stat, p = chstwo(bins1, bins2)
        print('chstwo', stat, p)

    def PlotResult(self, normalize = False, differential = False):
        """
        Must follow SetModel() and CalcPointEstimates()
        """
        st = self.settings
        model = self.model
        self.SetComponentVarnameDict()

        # Create the figure
        fig_name = 'fig_model_result'
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)

        rows, cols = 5, self.submodels_n
        gs = gridspec.GridSpec(rows, cols)
        gs.update(hspace = 0, wspace = 0)

        ax_spectra, ax_resid = [], []
        for i, submodel in enumerate(model.submodel_list):
            # Setup the figure
            if i == 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i]) )
            if i > 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i], sharey = ax_spectra[0]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i], sharey = ax_resid[0]) )
                plt.setp(ax_spectra[i].get_yticklabels(), visible = False)
                plt.setp(ax_resid[i].get_yticklabels(), visible = False)
            plt.setp(ax_spectra[i].get_xticklabels(), visible = False)
            ax_spectra[i].set_xlim(st.exp.min,st.exp.max)
            ax_resid[i].set_xlim(st.exp.min,st.exp.max)

            # Label the figure
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            title = '%s %s\n%sGe %s' % (dataset, openness_dict[openness], detector_type_dict[detector_type], sim_data_cut_dict[cut])
            xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
            ylabel = 'counts'
            if normalize: ylabel = 'c/kg/yr'
            if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
            ax_spectra[i].set_title(title)
            ax_resid[i].set_xlabel(xlabel)
            ax_spectra[0].set_ylabel(ylabel)
            ax_resid[0].set_ylabel('(data-model)/$\sigma_{data}$')

            # Draw the data and total distributions
            observed_dist = submodel.count_dist
            dag_df = submodel.dag_df
            fixed_dist = np.sum([component.fit_dist * dag_df[component.name]['prior_loc'] for component in submodel.component_list if not component.floated], axis = 0)
            # fixed_dist = np.sum([component.fit_dist * component.prior_loc for component in submodel.component_list if not component.floated], axis = 0)
            floated_dist = np.sum([component.fit_dist * component.p_mode for component in submodel.component_list if component.floated], axis = 0)
            if normalize:
                observed_dist = observed_dist / exposure
                fixed_dist = fixed_dist / exposure
                floated_dist = floated_dist / exposure
            if differential:
                observed_dist = observed_dist / st.exp.bin_wid
                fixed_dist = fixed_dist / st.exp.bin_wid
                floated_dist = floated_dist / st.exp.bin_wid
            if np.sum(fixed_dist) == 0.:
                print('PlotTools::PlotResult(): no fixed_dist')
                fixed_dist = np.zeros(shape = (st.fit.bins_n,))
            ax_spectra[i].step(st.fit.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
                label = 'Model fixed total')
            ax_spectra[i].step(st.fit.bin_centers, floated_dist, where = 'mid', c = 'blue', \
                label = 'Model floated total')
            ax_spectra[i].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
                label = 'Model total')
            ax_spectra[i].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
                label = 'Data %.2f %s' % (exposure, exposure_units))

            # Draw the components
            varname_list = []
            for j, component in enumerate(submodel.component_list):
                if component.floated:
                    dist = component.fit_dist * component.p_mode
                    if normalize:
                        dist = dist / exposure
                    if differential:
                        dist = dist / st.fit.bin_wid
                    varname = self.component_varname_dict[component.name]
                    color = self.c_list_dict[varname]
                    if varname in varname_list:
                        ax_spectra[i].step(st.fit.bin_centers, dist, where = 'mid', c = color)
                    else:
                        varname_list.append(varname)
                        ax_spectra[i].step(st.fit.bin_centers, dist, where = 'mid', c = color, \
                            label = varname + ' floated')

            # Draw the residuals
            pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
            pulls_masked = np.ma.masked_where(observed_dist == 0, pulls, copy=True) # mask zeros
            bin_centers_pulls_masked = np.ma.masked_where(observed_dist == 0, st.exp.bin_centers, copy=True) # mask zeros
            ax_resid[i].scatter(bin_centers_pulls_masked, pulls_masked, marker = 'o', s = 1., c = 'k')
            # Draw the residuals hist from the right
            pulls_for_hist = pulls_masked[~pulls_masked.mask]
            tmp_hist, tmp_bin_edges = np.histogram(a = pulls_for_hist, bins = 'rice', density = False)
            tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            tmp_x_max = ax_resid[i].get_xlim()[1]
            tmp_hist  = -1 * tmp_hist
            tmp_hist_left = tmp_x_max
            ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        fig = plt.figure('fig_model_result_legend')
        ax = fig.gca()
        ax.legend(*ax_spectra[-1].get_legend_handles_labels(), loc='center', prop={'size': 5})
        ax.axis('off')

    def PlotResultCombinedSubmodels(self, normalize = False, differential = False):
        """
        Must follow SetModel() and CalcPointEstimates()
        """
        st = self.settings
        model = self.model
        self.SetComponentVarnameDict()

        # Create the figure
        fig_name = 'fig_model_resultcombinedsubmodels' #default is fig_model_resultcombinedsubmodels
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)
        base_dir = os.environ['MODEL_DIR']
        model_dir = st.model_dirname.lstrip('../../FitSpectra_Models/')
        plot_dir = base_dir + '/' + model_dir + '/Spectra/'

        rows, cols = 3, 1 #Normally rows, cols = 5, 1 - changed to compare with Anna
        gs = gridspec.GridSpec(rows, cols)
        gs.update(hspace = 0, wspace = 0)

        # Create custom submodel groupings
        custom_submodel_list = []
        # DS1-6a M==1 All
        ds16acut2all_list = ['SubModel_0_2_DS12_open','SubModel_0_2_DS345a5b5c6a_open','SubModel_2_2_DS12_open','SubModel_2_2_DS345a5b5c6a_open']
        # DS1-6a M>1 All
        ds16acut6all_list = ['SubModel_0_6_DS12_open','SubModel_0_6_DS345a5b5c6a_open','SubModel_2_6_DS12_open','SubModel_2_6_DS345a5b5c6a_open']
        # DS1-6a M>=1 Enr
        ds16acut26enr_list = ['SubModel_2_2_DS12_open','SubModel_2_2_DS345a5b5c6a_open','SubModel_2_6_DS12_open','SubModel_2_6_DS345a5b5c6a_open']
        # DS1-6a M>=1 Nat
        ds16acut26nat_list = ['SubModel_0_2_DS12_open','SubModel_0_2_DS345a5b5c6a_open','SubModel_0_6_DS12_open','SubModel_0_6_DS345a5b5c6a_open']
        
        for q, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            if self.name in ds16acut26nat_list:
                custom_submodel_list.append(submodel)

        exposure_total = 0
        exposure_units_total = ''
        for i, submodel in enumerate(model.submodel_list): #can be model.submodel_list or custom_submodel_list
            self.SetSubModel(submodel)
            print(self.name)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            exposure_total += exposure
            exposure_units_total = exposure_units

        ax_spectra, ax_resid = [], []
        # Setup the figure and dists
        #ax_spectra.append( fig.add_subplot(gs[:2,0]) )
        ax_spectra.append( fig.add_subplot(gs[:rows-1,0]) ) #normally gs[2:rows-1,0]
        ax_resid.append( fig.add_subplot(gs[rows-1:rows,0], sharex = ax_spectra[0]) )
        #plt.setp(ax_spectra[0].get_xticklabels(), visible = False)
        #plt.setp(ax_spectra[1].get_xticklabels(), visible = False)
        ax_spectra[0].set_xlim(st.exp.min,st.exp.max)
        #ax_spectra[1].set_xlim(st.exp.min,st.exp.max)
        if st.toymc_mult == 1:
          ax_spectra[0].set_ylim(10e-2,10e3) #normally with ax_spectra[1]
        if st.toymc_mult == 10:
          ax_spectra[0].set_ylim(10e-2,10e4)
        if st.toymc_mult == 100:
          ax_spectra[0].set_ylim(10e-2,10e5)
        if st.toymc_mult == 1000:
          ax_spectra[0].set_ylim(10e-2,10e6)
        ax_resid[0].set_xlim(st.exp.min,st.exp.max)

        observed_dist = np.zeros(shape=st.fit.bins_n)
        fixed_dist = np.zeros(shape=st.fit.bins_n)
        floated_dist = np.zeros(shape=st.fit.bins_n)
        dC_dist_dict = {}
        for i, submodel in enumerate(model.submodel_list): #can be model.submodel_list or custom_submodel_list
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            dag_df = submodel.dag_df
            observed_dist += submodel.count_dist
            fixed_dist += np.sum([component.fit_dist * dag_df[component.name]['prior_loc'] for component in submodel.component_list if not component.floated], axis = 0)
            floated_dist += np.sum([component.fit_dist * component.p_mode for component in submodel.component_list if component.floated], axis = 0)

            # Collect the decay chains, including floated and non-floated
            for j, component in enumerate(submodel.component_list):
                if component.floated:
                    tmp_dist = component.fit_dist * component.p_mode
                if not component.floated:
                    tmp_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                dC = component.component_dict['decay_chain']
                if dC not in dC_dist_dict:
                    dC_dist_dict[dC] = np.zeros(shape=st.fit.bins_n)
                if 'Rn222' in dC: #Code block to combine Rn222 and U238 spectra, since they're somewhat correlated (and to compare to Anna)
                    if 'U238' not in dC_dist_dict:
                        dC_dist_dict['U238'] = np.zeros(shape=st.fit.bins_n)
                    dC_dist_dict['U238'] += tmp_dist
                else:
                    dC_dist_dict[dC] += tmp_dist

        if normalize:
            observed_dist = (observed_dist / exposure_total) * 1000.0
            fixed_dist = (fixed_dist / exposure_total) * 1000.0
            floated_dist = (floated_dist / exposure_total) * 1000.0 #temp conversion to ct/t-yr
        if differential:
            observed_dist = observed_dist / st.exp.bin_wid
            fixed_dist = fixed_dist / st.exp.bin_wid
            floated_dist = floated_dist / st.exp.bin_wid
        if np.sum(fixed_dist) == 0.:
            print('PlotTools::PlotResult(): no fixed_dist')
            fixed_dist = np.zeros(shape = (st.fit.bins_n,))
        # ax_spectra[0].step(st.fit.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
        #     label = 'Model fixed total')
        # ax_spectra[0].step(st.fit.bin_centers, floated_dist, where = 'mid', c = 'blue', \
        #     label = 'Model floated total')
        # ax_spectra[0].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
        #     label = 'Model total')
        ax_spectra[0].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', color = 'lightgrey', \
            label = 'Model total') #previously uncommented
        ax_spectra[0].fill_between(st.fit.bin_centers, fixed_dist + floated_dist, step='mid', color = 'lightgrey')
        ax_spectra[0].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
            label = 'Data', zorder = 100)
        #ax_spectra[0].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
        #    label = 'Data %.2f %s' % (exposure_total, exposure_units_total), zorder = 100)
        #ax_spectra[1].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', color = 'lightgrey', \
        #    label = 'Model total')
        #ax_spectra[1].fill_between(st.fit.bin_centers, fixed_dist + floated_dist, step='mid', color = 'lightgrey')
        #ax_spectra[1].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
        #    label = 'Data %.2f %s' % (exposure_total, exposure_units_total), zorder = 100)

        for dC in dC_dist_dict:
            if 'Rn' in dC: #Combining Rn222 and U238 spectra for now, so no need to display Rn222
                continue
            tmp_dist = dC_dist_dict[dC]
            if normalize:
                tmp_dist = (tmp_dist / exposure_total) * 1000.0 #temp converstion to ct/t-yr
            if differential:
                tmp_dist = tmp_dist / st.exp.bin_wid
            if 'U' in dC:
                ax_spectra[0].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                    label = 'U/Rn')
                #ax_spectra[1].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                #    label = 'U238/Rn222' + ' floated')
            else:
                ax_spectra[0].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                    label = dC)
                #ax_spectra[1].step(st.fit.bin_centers, tmp_dist, where = 'mid', c = self.GetDecayChainColor(dC), \
                #    label = dC + ' floated')

        xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
        ylabel = 'counts'
        if normalize: ylabel = 'c/t/yr' #normally c/kg/yr
        if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
        ax_spectra[0].set_ylabel(ylabel)
        ax_spectra[0].set_title("Fit to DS0-7 Simulated Dataset with multiplier %i" % st.toymc_mult)
        #ax_spectra[0].set_title("Fit to DS0-7 Open and Blind Data")
        ax_spectra[0].set_yscale('log')
        #ax_spectra[1].set_ylabel(ylabel)
        ax_resid[0].set_xlabel(xlabel)
        ax_resid[0].set_ylabel('(data-model)/$\sigma_{data}$')

        # Draw the residuals #ENABLE THIS IF YOU WANT RESIDUALS
        pulls = (observed_dist - (fixed_dist + floated_dist))/np.sqrt(observed_dist)
        print("Shape of pulls: " + str(pulls.shape))
        pulls_masked = np.ma.masked_where(observed_dist == 0, pulls, copy=True) # mask zeros
        print("Shape of pulls_masked: " + str(pulls_masked.shape))
        bin_centers_pulls_masked = np.ma.masked_where(observed_dist == 0, st.exp.bin_centers, copy=True) # mask zeros
        ax_resid[0].scatter(bin_centers_pulls_masked, pulls_masked, marker = 'o', s = 1., c = 'k')
        # Draw the residuals hist from the right
        pulls_for_hist = pulls_masked[~pulls_masked.mask]
        tmp_hist, tmp_bin_edges = np.histogram(a = pulls_for_hist, bins = 'rice', density = False)
        tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
        tmp_x_max = ax_resid[0].get_xlim()[1]
        tmp_hist = -1 * tmp_hist
        tmp_hist_left = tmp_x_max
        ax_resid[0].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        #Find mean and standard deviation of pulls in region near the K40 peak and a bit below to capture the 60Co contribution from spring clips (800-1440):
        region_pulls = pulls[70:135]
        rms = np.sqrt(np.mean(np.square(region_pulls)))
        std = np.std(region_pulls)
        print("RMS of pulls in range 800-1440 kev: " + str(rms))
        print("Std of pulls in range 800-1440 kev: " + str(std))
        print("Pull at bin below 40K peak (1450-1460): " + str(pulls[135]))


        #plt.title("Fit to DS1-6a ToyMC Dataset (No Cuts)\n w/Excess in %s" % st.toymc_targeted_vals_comp)

        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)
        fig_filename = plot_dir + fig_name + '_' + str(st.mcmc_seed_number) + '.png'
        ax_spectra[0].legend(ncol=3,loc='upper right',fontsize="6")
        plt.savefig(fig_filename, bbox_inches='tight',dpi=720)

        ax_spectra[0].set_yscale("log", nonposy='clip') #normally ax_spectra[1]
        fig = plt.figure('fig_model_resultcombinedsubmodels_legend')
        ax = fig.gca()
        ax.legend(*ax_spectra[-1].get_legend_handles_labels(), loc='center') # prop={'size': 12}
        ax.axis('off')

    def PrintTopExpected(self, normalize = False, differential = False):
        """
        Must follow SetModel()
        """
        st = self.settings
        model = self.model
        self.SetComponentVarnameDict()

        exposure_total = 0
        exposure_units_total = ''
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            exposure_total += exposure
            exposure_units_total = exposure_units

        observed_dist = np.zeros(shape=st.fit.bins_n)
        dC_hwC_dict = {}
        dC_hwC_ubqkg_dict = {}
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            dag_df = submodel.dag_df
            observed_dist += submodel.count_dist
            for component in submodel.component_list:
                if not component.floated:
                    dist = component.fit_dist * dag_df[component.name]['prior_loc']
                if component.floated:
                    dist = component.fit_dist * dag_df[component.name]['prior_loc']

                dC = component.component_dict['decay_chain']
                hwC = component.component_dict['hardware_component']
                dC_hwC = '%s_%s' % (dC, hwC)
                if dC_hwC not in dC_hwC_dict:
                    dC_hwC_dict[dC_hwC] = 0
                    dC_hwC_ubqkg_dict[dC_hwC] = {}
                    dC_hwC_ubqkg_dict[dC_hwC]['prior_loc'] = 1e6 * dag_df[component.name]['prior_loc'] / cfgd.hardwareComponentDict[hwC]['mass']
                    dC_hwC_ubqkg_dict[dC_hwC]['prior_scale'] = 1e6 * dag_df[component.name]['prior_scale'] / cfgd.hardwareComponentDict[hwC]['mass']
                else:
                    dC_hwC_dict[dC_hwC] += np.sum(dist)

        sorted_dC_hwC_tuple_list = sorted(dC_hwC_dict.items(), key=operator.itemgetter(1))
        counts_total = np.sum(observed_dist)
        print('Total Counts:', counts_total)
        print('Total Exposure:', exposure_total)
        print('Sorted dC_hwC contributors')
        for tup in sorted_dC_hwC_tuple_list:
            print(tup[0], tup[1], 100*tup[1]/counts_total, dC_hwC_ubqkg_dict[tup[0]]['prior_loc'], dC_hwC_ubqkg_dict[tup[0]]['prior_scale'])

    # def PrintTopResult(self, normalize = False, differential = False):
    #     """
    #     Must follow SetModel()
    #     """
    #     st = self.settings
    #     model = self.model
    #     self.SetComponentVarnameDict()
    #
    #     exposure_total = 0
    #     exposure_units_total = ''
    #     for i, submodel in enumerate(model.submodel_list):
    #         self.SetSubModel(submodel)
    #         name, dataset, openness, cut, detector_type, exposure, exposure_units = \
    #             self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
    #         exposure_total += exposure
    #         exposure_units_total = exposure_units
    #
    #     observed_dist = np.zeros(shape=st.fit.bins_n)
    #     dC_hwC_dict = {}
    #     for i, submodel in enumerate(model.submodel_list):
    #         self.SetSubModel(submodel)
    #         name, dataset, openness, cut, detector_type, exposure, exposure_units = \
    #             self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
    #         dag_df = submodel.dag_df
    #         observed_dist += submodel.count_dist
    #         for component in submodel.component_list:
    #             if not component.floated:
    #                 dist = component.fit_dist * dag_df[component.name]['prior_loc']
    #             if component.floated:
    #                 dist = component.fit_dist * component.p_mode
    #             dC = component.component_dict['decay_chain']
    #             hwC = component.component_dict['hardware_component']
    #             dC_hwC = '%s_%s' % (dC, hwC)
    #             if dC_hwC not in dC_hwC_dict:
    #                 dC_hwC_dict[dC_hwC] = 0
    #             else:
    #                 dC_hwC_dict[dC_hwC] += np.sum(dist)
    #
    #     sorted_dC_hwC_tuple_list = sorted(dC_hwC_dict.items(), key=operator.itemgetter(1))
    #     counts_total = np.sum(observed_dist)
    #     print('Total Counts:', counts_total)
    #     print('Total Exposure:', exposure_total)
    #     print('Sorted dC_hwC contributors')
    #     for tup in sorted_dC_hwC_tuple_list:
    #         print(tup[0], tup[1], tup[1]/counts_total)

    def PrintTopResult(self, normalize = False, differential = False):
        """
        Must follow SetModel()
        """
        st = self.settings
        model = self.model
        self.SetComponentVarnameDict()

        exposure_total = 0
        exposure_units_total = ''
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            exposure_total += exposure
            exposure_units_total = exposure_units

        observed_dist = np.zeros(shape=st.fit.bins_n)
        dC_hwC_dict = {}
        dC_hwC_ubqkg_dict = {}
        for i, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units
            dag_df = submodel.dag_df
            observed_dist += submodel.count_dist
            for component in submodel.component_list:
                if not component.floated:
                    dist = component.fit_dist * dag_df[component.name]['prior_loc']
                if component.floated:
                    dist = component.fit_dist * component.p_mode

                dC = component.component_dict['decay_chain']
                hwC = component.component_dict['hardware_component']
                dC_hwC = '%s_%s' % (dC, hwC)
                if dC_hwC not in dC_hwC_dict:
                    dC_hwC_dict[dC_hwC] = 0
                    dC_hwC_ubqkg_dict[dC_hwC] = {}
                    dC_hwC_ubqkg_dict[dC_hwC]['prior_loc'] = 1e6 * dag_df[component.name]['prior_loc'] / cfgd.hardwareComponentDict[hwC]['mass']
                    dC_hwC_ubqkg_dict[dC_hwC]['prior_scale'] = 1e6 * dag_df[component.name]['prior_scale'] / cfgd.hardwareComponentDict[hwC]['mass']
                    dC_hwC_ubqkg_dict[dC_hwC]['p_loc'] = 1e6 * component.p_mean / cfgd.hardwareComponentDict[hwC]['mass']
                    dC_hwC_ubqkg_dict[dC_hwC]['p_scale'] = 1e6 * component.p_std / cfgd.hardwareComponentDict[hwC]['mass']
                else:
                    dC_hwC_dict[dC_hwC] += np.sum(dist)

        sorted_dC_hwC_tuple_list = sorted(dC_hwC_dict.items(), key=operator.itemgetter(1))
        counts_total = np.sum(observed_dist)
        print('Total Counts:', counts_total)
        print('Total Exposure:', exposure_total)
        print('Sorted dC_hwC contributors')
        for tup in sorted_dC_hwC_tuple_list:
            print(tup[0], tup[1], 100*tup[1]/counts_total, dC_hwC_ubqkg_dict[tup[0]]['prior_loc'], dC_hwC_ubqkg_dict[tup[0]]['prior_scale'], dC_hwC_ubqkg_dict[tup[0]]['p_loc'], dC_hwC_ubqkg_dict[tup[0]]['p_scale'])


    def PlotPosteriors(self, kde = False):
        """
        Plot posteriors against their priors
        Must follow SetModel()
        Ref:
            https://github.com/pymc-devs/pymc3/blob/master/pymc3/plots/artists.py#L26
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        tr.SetModel(model)

        print('PlotTools::PlotPosteriors():')

        # Create the figure
        vars_n = len(model.pymc_model.deterministics)
        cols = 5
        if vars_n < cols:
            cols = vars_n
        gs = gridspec.GridSpec(vars_n // cols + 1, cols)
        gs.update(top=.9, bottom=.1, left=.1, right=.9, hspace=.75, wspace=.23)
        fig_name = 'fig_model_posteriors'
        if kde: fig_name += '_kde'
        fig = plt.figure(fig_name)
        ax = []
        i = -1
        varname_list = []
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated:
                    for rv_name_type in ['hp_rv_name', 'p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only plot each var once
                        if varname in varname_list: continue
                        else: varname_list.append(varname)

                        # Setup the axes
                        i += 1
                        row = (i // cols)
                        col = i % cols
                        ax.append(fig.add_subplot(gs[row, col]))
                        ax[-1].yaxis.set_ticks([])

                        # Label the figure
                        ax[-1].set_title(varname)
                        ax[-1].set_xlabel(component.prior_units)
                        ax[-1].ticklabel_format(axis = 'x', style = 'sci', scilimits = (-3,3))

                        # Prepare figure inputs
                        std, mean, mode, hpd = \
                            dag_df[component.name][h('p_std')], dag_df[component.name][h('p_mean')], dag_df[component.name][h('p_mode')], dag_df[component.name][h('p_hpd')]
                        trace_values = tr.GetTraceValues(varname)
                        posterior_range = (mean-3*std, mean+3*std)

                        prior_loc, prior_scale = dag_df[component.name][h('prior_loc')], dag_df[component.name][h('prior_scale')]
                        prior_range = (prior_loc-3*prior_scale, prior_loc+3*prior_scale)

                        # print('   ', component.name, dag_df[component.name][h('p_rv_name')],\
                        #     'input %.6f %.6f' % (prior_loc, prior_scale),\
                        #     'result %.6f %.6f' % (mean, std),\
                        #     'result/input %.6f %.6f' % (mean/prior_loc, std/prior_scale))

                        x_min = prior_range[0] if prior_range[0] < posterior_range[0] else posterior_range[0]
                        x_max = prior_range[1] if prior_range[1] > posterior_range[1] else posterior_range[1]
                        if x_min < 0: x_min = 0

                        if kde:
                            # bin_centers = np.linspace(x_min, x_max, 1000)
                            #
                            # posterior_dist, l, u = fast_kde(trace_values, bw = 4.5)
                            #
                            # prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(bin_centers).eval())
                            #
                            # ax[-1].plot(bin_centers, prior_dist, c = 'k', linestyle = '--')
                            # ax[-1].plot(bin_centers, posterior_dist, c = 'k')
                            # ax[-1].fill_between(bin_centers, posterior_dist, color = 'k', alpha = 0.5)

                            posterior_dist, l, u = fast_kde(trace_values, bw = 4.5)
                            posterior_bin_centers = np.linspace(l, u, len(posterior_dist))

                            prior_bin_centers = np.linspace(x_min, x_max, int(np.ceil((x_max-x_min)*len(posterior_dist)/(u-l))) )
                            prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(prior_bin_centers).eval())

                            ax[-1].plot(prior_bin_centers, prior_dist, c = 'k', linestyle = '--')
                            ax[-1].plot(posterior_bin_centers, posterior_dist, c = 'k')
                            ax[-1].fill_between(posterior_bin_centers, posterior_dist, color = 'k', alpha = 0.5)
                        else:
                            bin_edges = np.histogram_bin_edges(a = trace_values, bins = 'rice', range = (x_min, x_max))
                            bin_wid = bin_edges[1] - bin_edges[0]
                            bin_centers = bin_edges[:-1] + bin_wid/2. # convert tmp_bin_edges from 'pre' to 'mid'

                            posterior_dist, tmp_bin_edges = np.histogram(a = trace_values, bins = bin_edges, range = (x_min, x_max), density = False)
                            posterior_dist = posterior_dist / (np.sum(posterior_dist) * bin_wid)

                            prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(bin_centers).eval())
                            prior_dist = prior_dist / (np.sum(prior_dist) * bin_wid)

                            ax[-1].step(bin_centers, prior_dist, where = 'mid', c = 'k', linestyle = '--')
                            ax[-1].step(bin_centers, posterior_dist, where = 'mid', c = 'k')
                            ax[-1].fill_between(bin_centers, posterior_dist, step = 'mid', color = 'k', alpha = 0.5)

                        y_min = 0
                        y_max = 1.1*np.max(prior_dist) if np.max(prior_dist) > np.max(posterior_dist) else 1.1*np.max(posterior_dist)
                        ax[-1].set_xlim(x_min,x_max)
                        ax[-1].set_ylim(y_min,y_max)

                        ax[-1].vlines(x = prior_loc, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = '--', colors = 'tab:purple')
                        ax[-1].vlines(x = hpd, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], colors = 'lightgrey')
                        ax[-1].vlines(x = mean, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = '--', colors = 'lightgrey')
                        ax[-1].vlines(x = mode, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = ':', colors = 'lightgrey')


    def PlotPosterior(self, component_name, kde = False, unit = 'uBq/kg'):
        """
        Plot posteriors against their priors
        Must follow SetModel()
        Ref:
            https://github.com/pymc-devs/pymc3/blob/master/pymc3/plots/artists.py#L26
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        tr.SetModel(model)

        # Create the figure
        vars_n = 1
        cols = 1
        if vars_n < cols:
            cols = vars_n
        gs = gridspec.GridSpec(vars_n // cols + 1, cols)
        gs.update(top=.9, bottom=.1, left=.1, right=.9, hspace=.75, wspace=.23)
        fig_name = 'fig_model_posterior_%s' % component_name
        if kde: fig_name += '_kde'
        fig = plt.figure(fig_name)
        ax = []
        i = -1
        varname_list = []
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated and component.name == component_name:
                    for rv_name_type in ['hp_rv_name', 'p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only plot each var once
                        if varname in varname_list: continue
                        else: varname_list.append(varname)

                        # Setup the axes
                        i += 1
                        row = (i // cols)
                        col = i % cols
                        ax.append(fig.add_subplot(gs[row, col]))
                        ax[-1].yaxis.set_ticks([])

                        # Label the figure
                        # ax[-1].set_title(varname)
                        ax[-1].set_xlabel(unit) # component.prior_units
                        ax[-1].ticklabel_format(axis = 'x', style = 'sci', scilimits = (-3,3))

                        # Prepare figure inputs
                        std, mean, mode, hpd = \
                            copy.deepcopy(dag_df[component.name][h('p_std')]),\
                            copy.deepcopy(dag_df[component.name][h('p_mean')]),\
                            copy.deepcopy(dag_df[component.name][h('p_mode')]),\
                            copy.deepcopy(dag_df[component.name][h('p_hpd')])
                        trace_values = np.copy(tr.GetTraceValues(varname))

                        prior_loc, prior_scale = \
                            copy.deepcopy(dag_df[component.name][h('prior_loc')]),\
                            copy.deepcopy(dag_df[component.name][h('prior_scale')])

                        if unit == 'uBq/kg':
                            hwC = component.component_dict['hardware_component']
                            mass = cfgd.hardwareComponentDict[hwC]['mass']
                            std = 1e6 * std / mass
                            mean = 1e6 * mean / mass
                            mode = 1e6 * mode / mass
                            hpd[0], hpd[1] = 1e6 * hpd[0] / mass, 1e6 * hpd[1] / mass
                            trace_values = 1e6 * trace_values / mass
                            prior_loc = 1e6 * prior_loc / mass
                            prior_scale = 1e6 * prior_scale / mass
                        elif unit == 'Bq':
                            pass
                        else:
                            sys.exit('Error: PlotForestPlot(): invalid unit arg')

                        posterior_range = (mean-3*std, mean+3*std)
                        prior_range = (prior_loc-3*prior_scale, prior_loc+3*prior_scale)

                        print('   ', component.name, dag_df[component.name][h('p_rv_name')])
                        print('   ', 'mass %.6f' % (cfgd.hardwareComponentDict[hwC]['mass']))
                        print('   ', 'untransformed prior loc scale %.6f %.6f\n' % (dag_df[component.name][h('prior_loc')], dag_df[component.name][h('prior_scale')]))
                        print('   ', 'prior loc scale %.6f %.6f\n' % (prior_loc, prior_scale))
                        print('   ', 'result loc scale %.6f %.6f\n' % (mean, std))
                        print('   ', 'result/input loc scale %.6f %.6f' % (mean/prior_loc, std/prior_scale))

                        x_min = prior_range[0] if prior_range[0] < posterior_range[0] else posterior_range[0]
                        x_max = prior_range[1] if prior_range[1] > posterior_range[1] else posterior_range[1]
                        if x_min < 0: x_min = 0

                        if kde:
                            # bin_centers = np.linspace(x_min, x_max, 1000)
                            #
                            # posterior_dist, l, u = fast_kde(trace_values, bw = 4.5)
                            #
                            # prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(bin_centers).eval())
                            #
                            # ax[-1].plot(bin_centers, prior_dist, c = 'k', linestyle = '--')
                            # ax[-1].plot(bin_centers, posterior_dist, c = 'k')
                            # ax[-1].fill_between(bin_centers, posterior_dist, color = 'k', alpha = 0.5)

                            posterior_dist, l, u = fast_kde(trace_values, bw = 4.5)
                            posterior_bin_centers = np.linspace(l, u, len(posterior_dist))

                            prior_bin_centers = np.linspace(x_min, x_max, int(np.ceil((x_max-x_min)*len(posterior_dist)/(u-l))) )
                            #prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(prior_bin_centers).eval())
                            a, b = (0 - prior_loc) / prior_scale, np.inf
                            prior_dist = stats.truncnorm.pdf(x = prior_bin_centers, a = a, b = b, loc = prior_loc, scale = prior_scale)

                            ax[-1].plot(prior_bin_centers, prior_dist, c = 'k', linestyle = '--')
                            ax[-1].plot(posterior_bin_centers, posterior_dist, c = 'k')
                            ax[-1].fill_between(posterior_bin_centers, posterior_dist, color = 'k', alpha = 0.5)
                        else:
                            bin_edges = np.histogram_bin_edges(a = trace_values, bins = 'rice', range = (x_min, x_max))
                            bin_wid = bin_edges[1] - bin_edges[0]
                            bin_centers = bin_edges[:-1] + bin_wid/2. # convert tmp_bin_edges from 'pre' to 'mid'

                            posterior_dist, tmp_bin_edges = np.histogram(a = trace_values, bins = bin_edges, range = (x_min, x_max), density = False)
                            posterior_dist = posterior_dist / (np.sum(posterior_dist) * bin_wid)

                            # prior_dist = np.exp(dag_df[component.name][h('p_rv_dist')].logp(bin_centers).eval())
                            a, b = (0 - prior_loc) / prior_scale, np.inf
                            prior_dist = stats.truncnorm.pdf(x = prior_bin_centers, a = a, b = b, loc = prior_loc, scale = prior_scale)
                            prior_dist = prior_dist / (np.sum(prior_dist) * bin_wid)

                            ax[-1].step(bin_centers, prior_dist, where = 'mid', c = 'k', linestyle = '--')
                            ax[-1].step(bin_centers, posterior_dist, where = 'mid', c = 'k')
                            ax[-1].fill_between(bin_centers, posterior_dist, step = 'mid', color = 'k', alpha = 0.5)

                        y_min = 0
                        y_max = 1.1*np.max(prior_dist) if np.max(prior_dist) > np.max(posterior_dist) else 1.1*np.max(posterior_dist)
                        ax[-1].set_xlim(x_min,x_max)
                        ax[-1].set_ylim(y_min,y_max)

                        ax[-1].vlines(x = prior_loc, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = '--', colors = 'tab:purple')
                        ax[-1].vlines(x = hpd, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], colors = 'lightgrey')
                        ax[-1].vlines(x = mean, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = '--', colors = 'lightgrey')
                        ax[-1].vlines(x = mode, ymin = plt.gca().get_ylim()[0], ymax = plt.gca().get_ylim()[1], linestyle = ':', colors = 'lightgrey')

    def PlotForestPlot(self, unit = 'uBq/kg'):
        """
        Plot with transformed into uBq/kg
        Then offer option to normalize to get each component on same scale
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        tr.SetModel(model)

        fig_name = 'fig_forestplot'
        fig = plt.figure(fig_name)

        vars_n = len(model.pymc_model.deterministics)

        varname_list = []
        varname_y_list = []
        mean_list = []
        hpd_list = []
        prior_loc_list = []
        prior_sdlim_list = []
        y = 0
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated:
                    for rv_name_type in ['hp_rv_name', 'p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only plot each var once
                        if varname in varname_list: continue
                        else: varname_list.append(varname)

                        # Prepare figure inputs
                        mean, hpd = \
                            copy.deepcopy(dag_df[component.name][h('p_mean')]), copy.deepcopy(dag_df[component.name][h('p_hpd')])
                        prior_loc, prior_scale = \
                            copy.deepcopy(dag_df[component.name][h('prior_loc')]), copy.deepcopy(dag_df[component.name][h('prior_scale')])
                        prior_sdlim = [prior_loc - prior_scale, prior_loc + prior_scale]
                        if prior_loc - prior_scale < 0: prior_sdlim[0] = 0

                        if unit == 'uBq/kg':
                            hwC = component.component_dict['hardware_component']
                            mass = cfgd.hardwareComponentDict[hwC]['mass']
                            mean = 1e6 * mean / mass
                            hpd[0], hpd[1] = 1e6 * hpd[0] / mass, 1e6 * hpd[1] / mass
                            prior_loc = 1e6 * prior_loc / mass
                            prior_sdlim[0], prior_sdlim[1] = 1e6 * prior_sdlim[0] / mass, 1e6 * prior_sdlim[1] / mass
                        elif unit == 'Bq':
                            pass
                        else:
                            sys.exit('Error: PlotForestPlot(): invalid unit arg')

                        mean_list.append(mean)
                        hpd_list.append(hpd)
                        prior_loc_list.append(prior_loc)
                        prior_sdlim_list.append(prior_sdlim)
                        y += 1
                        varname_y_list.append(y)

        hpd_list = np.array(hpd_list)
        prior_sdlim_list = np.array(prior_sdlim_list)
        varname_y_list = np.array(varname_y_list)
        offset = 0.08
        plt.hlines(varname_y_list+offset, hpd_list[:,0], hpd_list[:,1])
        plt.scatter(mean_list, varname_y_list+offset, s = 5., c = 'k')
        plt.hlines(varname_y_list-offset, prior_sdlim_list[:,0], prior_sdlim_list[:,1], colors = 'grey')
        plt.scatter(prior_loc_list, varname_y_list-offset, s = 5., c = 'grey')
        plt.yticks(ticks = varname_y_list, labels = varname_list)
        if unit == 'uBq/kg':
            xLabel = '$\mu$Bq/kg or $\mu$Bq/m$^2$'
        else: xLabel = unit
        plt.xlabel(xLabel)
        plt.xlim(-0.1, 1.1*np.amax(hpd_list[:,1]))

    def PlotForestPlotForAllDecayChains(self, unit = 'uBq/kg'):
        for dC in ['Th232','U238','Rn222','Pb210','Co60','Co57','Ge68','K40','2v','Mn54']:
            self.PlotForestPlotDecayChain(dC, unit)

    def PlotForestPlotDecayChain(self, dC, unit = 'uBq/kg'):
        """
        Plot with transformed into uBq/kg
        Then offer option to normalize to get each component on same scale
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        tr.SetModel(model)

        fig_name = 'fig_forestplot_%s' % dC
        fig = plt.figure(fig_name)

        vars_n = len(model.pymc_model.deterministics)

        varname_list = []
        varname_y_list = []
        mean_list = []
        hpd_list = []
        prior_loc_list = []
        prior_sdlim_list = []
        y = 0
        for submodel in model.submodel_list:
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated and component.component_dict['decay_chain'] == dC:
                    for rv_name_type in ['hp_rv_name', 'p_rv_name']:
                        if rv_name_type == 'hp_rv_name':
                            def h(str):
                                return 'h' + str
                        if rv_name_type == 'p_rv_name':
                            def h(str):
                                return str

                        varname = dag_df[component.name][h('p_rv_name')]
                        if varname == None: continue

                        # Only plot each var once
                        if varname in varname_list: continue
                        else: varname_list.append(varname)

                        # Prepare figure inputs
                        mean, hpd = \
                            copy.deepcopy(dag_df[component.name][h('p_mean')]), copy.deepcopy(dag_df[component.name][h('p_hpd')])
                        prior_loc, prior_scale = \
                            copy.deepcopy(dag_df[component.name][h('prior_loc')]), copy.deepcopy(dag_df[component.name][h('prior_scale')])
                        prior_sdlim = [prior_loc - prior_scale, prior_loc + prior_scale]
                        if prior_loc - prior_scale < 0: prior_sdlim[0] = 0

                        if unit == 'uBq/kg':
                            hwC = component.component_dict['hardware_component']
                            mass = cfgd.hardwareComponentDict[hwC]['mass']
                            mean = 1e6 * mean / mass
                            hpd[0], hpd[1] = 1e6 * hpd[0] / mass, 1e6 * hpd[1] / mass
                            prior_loc = 1e6 * prior_loc / mass
                            prior_sdlim[0], prior_sdlim[1] = 1e6 * prior_sdlim[0] / mass, 1e6 * prior_sdlim[1] / mass
                        elif unit == 'Bq':
                            pass
                        else:
                            sys.exit('Error: PlotForestPlot(): invalid unit arg')

                        mean_list.append(mean)
                        hpd_list.append(hpd)
                        prior_loc_list.append(prior_loc)
                        prior_sdlim_list.append(prior_sdlim)
                        y += 1
                        varname_y_list.append(y)

        hpd_list = np.array(hpd_list)
        prior_sdlim_list = np.array(prior_sdlim_list)
        varname_y_list = np.array(varname_y_list)
        offset = 0.08
        if len(varname_list) > 0:
            plt.hlines(varname_y_list+offset, hpd_list[:,0], hpd_list[:,1], colors = self.GetDecayChainColor(dC))
            plt.scatter(mean_list, varname_y_list+offset, s = 5., c = self.GetDecayChainColor(dC))
            plt.hlines(varname_y_list-offset, prior_sdlim_list[:,0], prior_sdlim_list[:,1], colors = 'grey')
            plt.scatter(prior_loc_list, varname_y_list-offset, s = 5., c = 'grey')
            plt.yticks(ticks = varname_y_list, labels = varname_list)
            if unit == 'uBq/kg':
                xLabel = '$\mu$Bq/kg or $\mu$Bq/m$^2$'
            else: xLabel = unit
            plt.xlabel(xLabel)
            plt.xlim(-0.1, 1.1*np.amax(hpd_list[:,1]))

    def PlotIntegratedCountsPlotForAllDecayChains(self):
        for dC in ['Th','U','Rn','Pb','Co','57Co','K','68Ge','2v','54Mn']:
            self.PlotIntegratedCountsDecayChain_v2(dC)        

    def PlotIntegratedCountsDecayChain(self, dC):
        """
        Plotting integrated counts from prior and posterior in bar graph form
        for each decay chain.
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        #tr.SetModel(model)

        fig_name = 'fig_intCounts_%s' % dC
        fig = plt.figure(fig_name)
        base_dir = os.environ['MODEL_DIR']
        model_dir = st.model_dirname.lstrip('../../FitSpectra_Models/')
        plot_dir = base_dir + '/' + model_dir + '/DCIntCtPlots/'

        #vars_n = len(model.pymc_model.deterministics)

        prior_counts_dict = {}
        prior_counts_error_dict = {}
        posterior_counts_error_dict = {}
        posterior_counts_dict = {}
        toymc_counts_dict = {}
        prior_values_list = []
        prior_values_error_list = []
        posterior_values_error_list = []
        posterior_values_list = []
        toymc_values_list = []
        key_name_list = []
        varname_list = []
        varname_x_list = []
        posterior_int_counts_list = []
        posterior_int_counts_error_list = []
        prior_int_counts_list = []
        prior_int_counts_error_list = []
        toymc_int_counts_list = []
        posterior_key_list = []
        prior_key_list = []

        #combined group vars
        M1Near_prior = 0.0
        M1Near_prior_error = 0.0
        M1Near_posterior = 0.0
        M1Near_posterior_error = 0.0
        M1Near_toymc = 0.0
        M2Near_prior = 0.0
        M2Near_prior_error = 0.0
        M2Near_posterior = 0.0
        M2Near_posterior_error = 0.0
        M2Near_toymc = 0.0
        M1Middle_prior = 0.0
        M1Middle_prior_error = 0.0
        M1Middle_posterior = 0.0
        M1Middle_posterior_error = 0.0
        M1Middle_toymc = 0.0
        M2Middle_prior = 0.0
        M2Middle_prior_error = 0.0
        M2Middle_posterior = 0.0
        M2Middle_posterior_error = 0.0
        M2Middle_toymc = 0.0
        M1Bellows_prior = 0.0
        M1Bellows_prior_error = 0.0
        M1Bellows_posterior = 0.0
        M1Bellows_posterior_error = 0.0
        M1Bellows_toymc = 0.0
        M2Bellows_prior = 0.0
        M2Bellows_prior_error = 0.0
        M2Bellows_posterior = 0.0
        M2Bellows_posterior_error = 0.0
        M2Bellows_toymc = 0.0
        RadShieldPb_prior = 0.0
        RadShieldPb_prior_error = 0.0
        RadShieldPb_posterior = 0.0
        RadShieldPb_posterior_error = 0.0
        RadShieldPb_toymc = 0.0
        RadShieldCuOuter_prior = 0.0
        RadShieldCuOuter_prior_error = 0.0
        RadShieldCuOuter_posterior = 0.0
        RadShieldCuOuter_posterior_error = 0.0
        RadShieldCuOuter_toymc = 0.0
        RadShieldCuInner_prior = 0.0
        RadShieldCuInner_prior_error = 0.0
        RadShieldCuInner_posterior = 0.0
        RadShieldCuInner_posterior_error = 0.0
        RadShieldCuInner_toymc = 0.0
        N2_prior = 0.0
        N2_prior_error = 0.0
        N2_posterior = 0.0
        N2_posterior_error = 0.0
        N2_toymc = 0.0

        M1Middle_groups = ['M1Connectors','M1TSS','M1CrossarmAndCPCables','M1CryostatCopperNear','M1CryostatCopperFar','M1Seals', 'M1CryostatCopperNearWeldedCopperCo60', 'M1CryostatCopperFarWeldedCopperCo60']
        M2Middle_groups = ['M2Connectors','M2TSS','M2CrossarmAndCPCables','M2CryostatCopperNear','M2CryostatCopperFar','M2Seals', 'M2CryostatCopperNearWeldedCopperCo60', 'M2CryostatCopperFarWeldedCopperCo60']
        M1Near_groups = ['M1LMFEs','M1DUPTFE','M1DUStringCopper','M1StringCables', 'M1DUStringCopperSpringClipCo60', 'M1EnrGe', 'M1NatGe']
        M2Near_groups = ['M2LMFEs','M2DUPTFE','M2DUStringCopper','M2StringCables', 'M2DUStringCopperSpringClipCo60', 'M2EnrGe', 'M2NatGe']

        #This is where to choose the submodels to sum over for a
        #complete match to data without overcounting.  Leave manual
        #for now, but eventually call a get_custom_submodel_list method.

        custom_submodel_list = []
        # DS1-6a M==1 All
        ds16acut2all_list = ['SubModel_0_2_DS12_open','SubModel_0_2_DS345a5b5c6a_open','SubModel_2_2_DS12_open','SubModel_2_2_DS345a5b5c6a_open']
        # DS1-6a M>1 All
        ds16acut6all_list = ['SubModel_0_6_DS12_open','SubModel_0_6_DS345a5b5c6a_open','SubModel_2_6_DS12_open','SubModel_2_6_DS345a5b5c6a_open']
        # DS1-6a M>=1 Enr
        ds16acut26enr_list = ['SubModel_2_2_DS12_open','SubModel_2_2_DS345a5b5c6a_open','SubModel_2_6_DS12_open','SubModel_2_6_DS345a5b5c6a_open']
        # DS1-6a M>=1 Nat
        ds16acut26nat_list = ['SubModel_0_2_DS12_open','SubModel_0_2_DS345a5b5c6a_open','SubModel_0_6_DS12_open','SubModel_0_6_DS345a5b5c6a_open']
        
        for q, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            if self.name in ds16acut26enr_list:
                custom_submodel_list.append(submodel)

        if st.multitrace_analysis:
            avg_p_modes, p_scales = tr.GetAvgModeAndError()

        for i, submodel in enumerate(model.submodel_list): #change to custom_submodel_list if using a custom list
            self.SetSubModel(submodel)
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated and component.component_dict['decay_chain'] == dC:
                    def h(str):
                        return str

                    varname = dag_df[component.name][h('p_rv_name')]
                    if varname == None: continue
                    if 'bulk' in varname: varname = varname.lstrip("p_%s_bulk_" % dC)
                    elif 'surf' in varname: varname = varname.lstrip("p_%s_surf_" % dC)
                    elif 'linesource' in varname: varname = varname.lstrip("p_%s_linesource_" % dC)
                    else: varname = varname.lstrip("p_%s_" % dC)
                    if 'RadShieldPb' in varname: varname = "RadShieldPb"
                    if 'Thermosyphon' in varname and 'M1' in varname: varname = "M1TSS"
                    if 'Thermosyphon' in varname and 'M2' in varname: varname = "M2TSS"

                    # Prepare figure inputs
                    if st.multitrace_analysis:
                        #avg_p_modes, p_scales = tr.GetAvgModeAndError()
                        posterior_dist = component.fit_dist * avg_p_modes[dag_df[component.name][h('p_rv_name')]]
                        posterior_dist_error = component.fit_dist * p_scales[dag_df[component.name][h('p_rv_name')]]
                    else:	
                        posterior_dist = component.fit_dist * component.p_mode
                        posterior_dist_error = 0
                    prior_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                    prior_dist_error = component.fit_dist * dag_df[component.name]['prior_scale']
                    #print("COMPONENT: %s | PRIOR_SCALE: %f" % (component.name,dag_df[component.name]['prior_scale']))
                    toymc_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                    tmp_name = dag_df[component.name][h('p_rv_name')].lstrip("p_%s_" % dC)
                    print(tmp_name)
                    sys.exit()
                    if dag_df[component.name][h('p_rv_name')].lstrip("p_%s_" % dC) in st.toymc_targeted_vals_comp and dC=='Th':
                        print('VARNAME IS %s' % varname)
                        toymc_dist = toymc_dist * st.toymc_targeted_vals_mult
                    if varname not in posterior_counts_dict.keys():
                        posterior_counts_dict[varname] = np.sum(posterior_dist)
                        posterior_counts_error_dict[varname] = (np.sum(posterior_dist_error))**2
                        prior_counts_dict[varname] = np.sum(prior_dist)
                        prior_counts_error_dict[varname] = (np.sum(prior_dist_error))**2
                        toymc_counts_dict[varname] = np.sum(toymc_dist)
                    else:
                        posterior_counts_dict[varname] = posterior_counts_dict[varname] + np.sum(posterior_dist)
                        posterior_counts_error_dict[varname] = posterior_counts_error_dict[varname] + (np.sum(posterior_dist_error))**2
                        prior_counts_dict[varname] = prior_counts_dict[varname] + np.sum(prior_dist)
                        prior_counts_error_dict[varname] = prior_counts_error_dict[varname] + (np.sum(prior_dist_error))**2
                        toymc_counts_dict[varname] = toymc_counts_dict[varname] + np.sum(toymc_dist)

        
        posterior_values_list = list(posterior_counts_dict.values())
        prior_values_list = list(prior_counts_dict.values())
        toymc_values_list = list(toymc_counts_dict.values())
        key_name_list = list(posterior_counts_dict.keys())
        if st.combined_groups:
            k = 0
            for key in key_name_list:
                if key in M1Near_groups:
                    M1Near_prior += prior_values_list[k]
                    M1Near_toymc += toymc_values_list[k]
                    M1Near_posterior += posterior_values_list[k]
                elif key in M2Near_groups:
                    M2Near_prior += prior_values_list[k]
                    M2Near_toymc += toymc_values_list[k]
                    M2Near_posterior += posterior_values_list[k]
                elif key in M1Middle_groups:
                    M1Middle_prior += prior_values_list[k]
                    M1Middle_toymc += toymc_values_list[k]
                    M1Middle_posterior += posterior_values_list[k]
                elif key in M2Middle_groups:
                    M2Middle_prior += prior_values_list[k]
                    M2Middle_toymc += toymc_values_list[k]
                    M2Middle_posterior += posterior_values_list[k]
                elif 'M1Bellows' in key:
                    M1Bellows_prior += prior_values_list[k]
                    M1Bellows_toymc += toymc_values_list[k]
                    M1Bellows_posterior += posterior_values_list[k]
                elif 'M2Bellows' in key:
                    M2Bellows_prior += prior_values_list[k]
                    M2Bellows_toymc += toymc_values_list[k]
                    M2Bellows_posterior += posterior_values_list[k]
                elif 'RadShieldPb' in key:
                    RadShieldPb_prior += prior_values_list[k]
                    RadShieldPb_toymc += toymc_values_list[k]
                    RadShieldPb_posterior += posterior_values_list[k]
                elif 'RadShieldCuOuter' in key:
                    RadShieldCuOuter_prior += prior_values_list[k]
                    RadShieldCuOuter_toymc += toymc_values_list[k]
                    RadShieldCuOuter_posterior += posterior_values_list[k]
                elif 'RadShieldCuInner' in key:
                    RadShieldCuInner_prior += prior_values_list[k]
                    RadShieldCuInner_toymc += toymc_values_list[k]
                    RadShieldCuInner_posterior += posterior_values_list[k]
                elif 'EnrGe' in key:
                    EnrGe_prior += prior_values_list[k]
                    EnrGe_toymc += toymc_values_list[k]
                    EnrGe_posterior += posterior_values_list[k]
                elif 'NatGe' in key:
                    NatGe_prior += prior_values_list[k]
                    NatGe_toymc += toymc_values_list[k]
                    NatGe_posterior += posterior_values_list[k]
                elif 'N2wM2Blank' in key:
                    N2wM2Blank_prior += prior_values_list[k]
                    N2wM2Blank_toymc += toymc_values_list[k]
                    N2wM2Blank_posterior += posterior_values_list[k]
                elif 'N2' in key:
                    N2_prior += prior_values_list[k]
                    N2_toymc += toymc_values_list[k]
                    N2_posterior += posterior_values_list[k]                   
                else:
                    print("ERROR, MISPLACED GROUP!: %s" % key)
                k+=1
            cg_posterior_int_counts_list = np.array([M1Near_posterior, M2Near_posterior, M1Middle_posterior, M2Middle_posterior, M1Bellows_posterior, M2Bellows_posterior, RadShieldPb_posterior, RadShieldCuOuter_posterior, RadShieldCuInner_posterior])
            cg_prior_int_counts_list = np.array([M1Near_prior, M2Near_prior, M1Middle_prior, M2Middle_prior, M1Bellows_prior, M2Bellows_prior, RadShieldPb_prior, RadShieldCuOuter_prior, RadShieldCuInner_prior])
            cg_toymc_int_counts_list = np.array([M1Near_toymc, M2Near_toymc, M1Middle_toymc, M2Middle_toymc, M1Bellows_toymc, M2Bellows_toymc, RadShieldPb_toymc, RadShieldCuOuter_toymc, RadShieldCuInner_toymc])
            cg_varname_list = np.array(['M1Near','M2Near','M1Middle','M2Middle','M1Bellows','M2Bellows','RadShieldPb','RadShieldCuOuter','RadShieldCuInner'])
            cg_varname_x_list = np.arange(1,10)

            #Adjustments for Ge68 groups
            if EnrGe_prior > 0: #if counts in prior, then should enable EnrGe and NatGe
                cg_posterior_int_counts_list = np.append(cg_posterior_int_counts_list,[EnrGe_posterior, NatGe_posterior])
                cg_prior_int_counts_list = np.append(cg_prior_int_counts_list,[EnrGe_prior, NatGe_prior])
                cg_toymc_int_counts_list = np.append(cg_toymc_int_counts_list,[EnrGe_toymc, NatGe_toymc])
                cg_varname_list = np.append(cg_varname_list,['EnrGe','NatGe'])
                cg_varname_x_list = np.append(cg_varname_x_list,[10,11])

            #Adjustments for Rn222 groups
            if N2_prior > 0: #if counts in prior, then should enable N2 and N2wM2Blank
                cg_posterior_int_counts_list = np.append(cg_posterior_int_counts_list,[N2_posterior, N2wM2Blank_posterior])
                cg_prior_int_counts_list = np.append(cg_prior_int_counts_list,[N2_prior, N2wM2Blank_prior])
                cg_toymc_int_counts_list = np.append(cg_toymc_int_counts_list,[N2_toymc, N2wM2Blank_toymc])
                cg_varname_list = np.append(cg_varname_list,['N2','N2wM2Blank'])
                cg_varname_x_list = np.append(cg_varname_x_list,[10,11])

        posterior_int_counts_list = np.array(posterior_values_list)
        prior_int_counts_list = np.array(prior_values_list)
        toymc_int_counts_list = np.array(toymc_values_list)
        varname_list = np.array(key_name_list)
        varname_x_list = np.arange(1,len(key_name_list)+1)
        offset = 0.33
        
        #Prepare list of errors
        for varname in varname_list:
            posterior_counts_error_dict[varname] = mt.sqrt(posterior_counts_error_dict[varname])
            prior_counts_error_dict[varname] = mt.sqrt(prior_counts_error_dict[varname])
        posterior_values_error_list = list(posterior_counts_error_dict.values())
        prior_values_error_list = list(prior_counts_error_dict.values())
        if st.combined_groups:
            k = 0
            for key in key_name_list:
                if key in M1Near_groups:
                    M1Near_prior_error += (prior_values_error_list[k])**2
                    M1Near_posterior_error += (posterior_values_error_list[k])**2
                elif key in M2Near_groups:
                    M2Near_prior_error += (prior_values_error_list[k])**2
                    M2Near_posterior_error += (posterior_values_error_list[k])**2
                elif key in M1Middle_groups:
                    M1Middle_prior_error += (prior_values_error_list[k])**2
                    M1Middle_posterior_error += (posterior_values_error_list[k])**2
                elif key in M2Middle_groups:
                    M2Middle_prior_error += (prior_values_error_list[k])**2
                    M2Middle_posterior_error += (posterior_values_error_list[k])**2
                elif 'M1Bellows' in key:
                    M1Bellows_prior_error += (prior_values_error_list[k])**2
                    M1Bellows_posterior_error += (posterior_values_error_list[k])**2
                elif 'M2Bellows' in key:
                    M2Bellows_prior_error += (prior_values_error_list[k])**2
                    M2Bellows_posterior_error += (posterior_values_error_list[k])**2
                elif 'RadShieldPb' in key:
                    RadShieldPb_prior_error += (prior_values_error_list[k])**2
                    RadShieldPb_posterior_error += (posterior_values_error_list[k])**2
                elif 'RadShieldCuOuter' in key:
                    RadShieldCuOuter_prior_error += (prior_values_error_list[k])**2
                    RadShieldCuOuter_posterior_error += (posterior_values_error_list[k])**2
                elif 'RadShieldCuInner' in key:
                    RadShieldCuInner_prior_error += (prior_values_error_list[k])**2
                    RadShieldCuInner_posterior_error += (posterior_values_error_list[k])**2
                elif 'EnrGe' in key:
                    EnrGe_prior_error += (prior_values_error_list[k])**2
                    EnrGe_posterior_error += (posterior_values_error_list[k])**2
                elif 'NatGe' in key:
                    NatGe_prior_error += (prior_values_error_list[k])**2
                    NatGe_posterior_error += (posterior_values_error_list[k])**2
                elif 'N2wM2Blank' in key:
                    N2wM2Blank_prior_error += (prior_values_error_list[k])**2
                    N2wM2Blank_posterior_error += (posterior_values_error_list[k])**2
                elif 'N2' in key:
                    N2_prior_error += (prior_values_error_list[k])**2
                    N2_posterior_error += (posterior_values_error_list[k])**2
                else:
                    print("ERROR, MISPLACED GROUP!: %s" % key)
                k+=1
            cg_posterior_int_counts_error_list = np.array([mt.sqrt(M1Near_posterior_error), mt.sqrt(M2Near_posterior_error), mt.sqrt(M1Middle_posterior_error), mt.sqrt(M2Middle_posterior_error), mt.sqrt(M1Bellows_posterior_error), mt.sqrt(M2Bellows_posterior_error), mt.sqrt(RadShieldPb_posterior_error), mt.sqrt(RadShieldCuOuter_posterior_error), mt.sqrt(RadShieldCuInner_posterior_error)])
            cg_prior_int_counts_error_list = [mt.sqrt(M1Near_prior_error), mt.sqrt(M2Near_prior_error), mt.sqrt(M1Middle_prior_error), mt.sqrt(M2Middle_prior_error), mt.sqrt(M1Bellows_prior_error), mt.sqrt(M2Bellows_prior_error), mt.sqrt(RadShieldPb_prior_error), mt.sqrt(RadShieldCuOuter_prior_error), mt.sqrt(RadShieldCuInner_prior_error)]
            
            #Adjustments for Ge68 groups
            if EnrGe_prior_error > 0:
                cg_posterior_int_counts_error_list = np.append(cg_posterior_int_counts_error_list,[EnrGe_posterior_error, NatGe_posterior_error])
                cg_prior_int_counts_error_list = np.append(cg_prior_int_counts_error_list,[EnrGe_prior_error, NatGe_prior_error])

            #Adjustments for Rn222 groups
            if N2_prior_error > 0:
                cg_posterior_int_counts_error_list = np.append(cg_posterior_int_counts_error_list,[N2_posterior_error, N2wM2Blank_posterior_error])
                cg_prior_int_counts_error_list = np.append(cg_prior_int_counts_error_list,[N2_prior_error, N2wM2Blank_prior_error])

            cg_prior_upper_error_limits = cg_prior_int_counts_error_list
            cg_prior_lower_error_limits = []
            index = 0
            for value in cg_prior_int_counts_error_list:
                if value > cg_prior_int_counts_list[index]: cg_prior_lower_error_limits.append(cg_prior_int_counts_list[index])
                else: cg_prior_lower_error_limits.append(value)
                index += 1
            final_cg_prior_int_counts_error_list = [cg_prior_lower_error_limits, cg_prior_upper_error_limits]
        posterior_int_counts_error_list = np.array(posterior_values_error_list)
        prior_upper_error_limits = prior_values_error_list
        prior_lower_error_limits = []
        index = 0
        for value in prior_values_error_list:
            if value > prior_int_counts_list[index]: prior_lower_error_limits.append(prior_int_counts_list[index])
            else: prior_lower_error_limits.append(value)
            index += 1
        prior_int_counts_error_list = [prior_lower_error_limits, prior_upper_error_limits]

        #Debug
        #posterior_key_list = list(posterior_counts_dict.keys())
        #prior_key_list = list(prior_counts_dict.keys())
        #debug_x_list = np.arange(len(key_name_list))
        #print('')
        #for index in debug_x_list:
        #    print('Varname: %s | Posterior_counts_dict: %s | Prior_counts_dict: %s' % (varname_list[index], posterior_key_list[index], prior_key_list[index]))
        #print('')

        if len(varname_list) > 0 and not st.combined_groups:
            #plt.hlines(varname_y_list+offset, hpd_list[:,0], hpd_list[:,1], colors = self.GetDecayChainColor(dC))
            if 'U238' in dC or 'Rn222' in dC: #Since default color of U238/Rn222 is already gray, change it to black so that prior remains gray.
                plt.bar(varname_x_list+offset, posterior_int_counts_list , width = 0.33, color = 'k', yerr = posterior_int_counts_error_list, ecolor ='red', label = 'Posterior Cts. (%.3e)' % sum(posterior_int_counts_list))
            else:
                plt.bar(varname_x_list+offset, posterior_int_counts_list , width = 0.33, color = self.GetDecayChainColor(dC), yerr = posterior_int_counts_error_list, ecolor ='k', label = 'Posterior Cts. (%.3e)' % sum(posterior_int_counts_list))
            plt.bar(varname_x_list, toymc_int_counts_list, width = 0.33, color = 'blue', label = 'ToyMC Dataset Cts. (%.3e)' % sum(toymc_int_counts_list))
            plt.bar(varname_x_list-offset, prior_int_counts_list, width = 0.33, color = 'grey', yerr = prior_int_counts_error_list, ecolor = 'k', label = 'Prior Cts. (%.3e)' % sum(prior_int_counts_list))
            plt.xticks(ticks = varname_x_list, labels = varname_list, rotation = 90, fontsize = 10)
            if st.toymc_targeted_vals_comp != None:
                comps = st.toymc_targeted_vals_comp
            elif st.high_prior_comp != None:
                comps = st.high_prior_comp
            else:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Groupings w/ No Excess\n ' % dC)
            if 'bulk_M1StringCables' in comps:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Groupings w/ Excess in Cables\n ' % dC)
            else:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Groupings w/ Excess in\n %s\n ' % (dC,comps))
            plt.xlabel('Component Groups')
            if 'Rn222' in dC or 'Co60' in dC or 'Ge68' in dC:
                plt.yscale('log')
            plt.ylabel('Integrated cts.')
            plt.legend()
            if not os.path.exists(plot_dir):
                os.makedirs(plot_dir)
            fig_filename = plot_dir + fig_name + '.png'
            plt.savefig(fig_filename, bbox_inches='tight')
            #plt.xlim(-0.1, 1.1*np.amax(hpd_list[:,1]))
        if len(varname_list) > 0 and st.combined_groups:
            if 'U238' in dC or 'Rn222' in dC: #Since default color of U238/Rn222 is already gray, change it to black so that prior remains gray.
                plt.bar(cg_varname_x_list+offset, cg_posterior_int_counts_list , width = 0.33, color = 'k', yerr = cg_posterior_int_counts_error_list, ecolor ='red', label = 'Posterior Cts. (%.3e)' % sum(cg_posterior_int_counts_list))
            else:
                plt.bar(cg_varname_x_list+offset, cg_posterior_int_counts_list , width = 0.33, color = self.GetDecayChainColor(dC), yerr = cg_posterior_int_counts_error_list, ecolor ='k', label = 'Posterior Cts. (%.3e)' % sum(cg_posterior_int_counts_list))
            plt.bar(cg_varname_x_list, cg_toymc_int_counts_list, width = 0.33, color = 'blue', label = 'ToyMC Dataset Cts. (%.3e)' % sum(cg_toymc_int_counts_list))
            plt.bar(cg_varname_x_list-offset, cg_prior_int_counts_list, width = 0.33, color = 'grey', yerr = final_cg_prior_int_counts_error_list, ecolor = 'k', label = 'Prior Cts. (%.3e)' % sum(cg_prior_int_counts_list))
            plt.xticks(ticks = cg_varname_x_list, labels = cg_varname_list, rotation = 90, fontsize = 10)
            if st.toymc_targeted_vals_comp != None:
                comps = st.toymc_targeted_vals_comp
            elif st.high_prior_comp != None:
                comps = st.high_prior_comp
            else:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Combined Groupings w/ No Excess\n ' % dC)
            if 'bulk_M1StringCables' in comps:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Combined Groupings w/ Excess in Cables\n ' % dC)
            else:
                plt.title('Integrated Cts. (%s) from the Prior, Posterior, and ToyMC Distributions\n of Combined Groupings w/ Excess in\n %s\n ' % (dC,comps))
            plt.xlabel('Combined Component Groups')
            if 'Rn222' in dC or 'Co60' in dC or 'Ge68' in dC:
                plt.yscale('log')
            plt.ylabel('Integrated cts.')
            plt.legend()
            plt.ylim(0,None)
            if not os.path.exists(plot_dir):
                os.makedirs(plot_dir)
            fig_filename = plot_dir + fig_name + '_combined.png'
            plt.savefig(fig_filename, bbox_inches='tight')

    def PlotPosteriorPredictive(self, normalize = False, differential = False, samples = None):
        """
        Must follow SetModel() and SamplePosteriorPredictive()
        """
        st = self.settings
        model = self.model

        # Create the figure
        fig_name = 'fig_posterior_predictive'
        if normalize: fig_name += '_norm'
        if differential: fig_name += '_diff'
        fig = plt.figure(fig_name)
        base_dir = os.environ['MODEL_DIR']
        model_dir = st.model_dirname.lstrip('../../FitSpectra_Models/')
        plot_dir = base_dir + '/' + model_dir + '/PPC_Plots/'

        #Load ppc array if it exists
        ppc_d = None
        file = st.model_dirname+'/PPC_Plots/ppcs/ppc_%s.pkl' % str(samples)
        if os.path.exists(file):
            with open(file, 'rb') as pklfile:
                ppc_d = pl.load(pklfile)
            print("Loading ppc with filename: %s" % file)
        elif os.path.exists(plot_dir+'ppcs/'):
            files = glob.glob(plot_dir+'ppcs/*.pkl')
            sorted_files = natsorted(files)
            with open(sorted_files[len(sorted_files)], 'rb') as pklfile:
                ppc_d = pl.load(pklfile) #load the file with the largest number of samples if a number isn't specified
            print("Loading ppc with filename: %s" % sorted_files[len(sorted_files)]) 
        else:
            print("Could not find a saved ppc, using recently calculated ppc.")

        rows, cols = 5, self.submodels_n
        gs = gridspec.GridSpec(rows, cols)
        gs.update(hspace = 0, wspace = 0)

        ax_spectra, ax_resid = [], []
        for i, submodel in enumerate(model.submodel_list):
            # Setup the figure
            if i == 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i]) )
            if i > 0:
                ax_spectra.append( fig.add_subplot(gs[:rows-1,i], sharey = ax_spectra[0]) )
                ax_resid.append( fig.add_subplot(gs[rows-1,i], sharex = ax_spectra[i], sharey = ax_resid[0]) )
                plt.setp(ax_spectra[i].get_yticklabels(), visible = False)
                plt.setp(ax_resid[i].get_yticklabels(), visible = False)
            plt.setp(ax_spectra[i].get_xticklabels(), visible = False, fontsize = '5')
            ax_spectra[i].set_xlim(st.exp.min,st.exp.max)
            ax_resid[i].set_xlim(st.exp.min,st.exp.max)

            # Label the figure
            self.SetSubModel(submodel)
            name, dataset, openness, cut, detector_type, exposure, exposure_units, module = \
                self.name, self.dataset, self.openness, self.cut, self.detector_type, self.exposure, self.exposure_units, self.module
            #title = '%s %s\n%sGe %s' % (dataset, openness_dict[openness], detector_type_dict[detector_type], sim_data_cut_dict[cut])
            title = 'M%s%s\n%s' % (module, detector_type_dict[detector_type], sim_data_cut_dict[cut])
            #xlabel = 'energy (%.1f keV bins)' % st.exp.bin_wid
            xlabel = 'E(keV)'
            ylabel = 'counts'
            if normalize: ylabel = 'c/kg/yr'
            if differential: ylabel += '/%.1fkeV' % st.exp.bin_wid
            ax_spectra[i].set_title(title)
            #ax_spectra[i].set_xlabel(xlabel)
            ax_resid[i].set_xlabel(xlabel)
            ax_spectra[0].set_ylabel(ylabel)
            ax_resid[0].set_ylabel('(data-mean_ppc)/$\sigma_{data}$')

            # Draw the data and total distributions
            observed_dist = submodel.count_dist
            # fixed_dist = np.sum([component.fit_dist * component.prior_loc for component in submodel.component_list if not component.floated], axis = 0)
            # floated_dist = np.sum([component.fit_dist * component.p_mode for component in submodel.component_list if component.floated], axis = 0)
            if normalize:
                observed_dist = observed_dist / exposure
                # fixed_dist = fixed_dist / exposure
                # floated_dist = floated_dist / exposure
            if differential:
                observed_dist = observed_dist / st.exp.bin_wid
                # fixed_dist = fixed_dist / st.exp.bin_wid
                # floated_dist = floated_dist / st.exp.bin_wid
            # if np.sum(fixed_dist) == 0.:
            #     print('PlotTools::PlotResult(): no fixed_dist')
            #     fixed_dist = np.zeros(shape = (st.fit.bins_n,))
            ax_spectra[i].scatter(st.fit.bin_centers, observed_dist, c = 'k', s = 1., \
                label = 'data %.2f %s' % (exposure, exposure_units))
            # ax_spectra[i].step(st.fit.bin_centers, fixed_dist, where = 'mid', c = 'orange', \
            #     label = 'model fixed total')
            # ax_spectra[i].step(st.fit.bin_centers, floated_dist, where = 'mid', c = 'blue', \
            #     label = 'model floated total')
            # ax_spectra[i].step(st.fit.bin_centers, fixed_dist + floated_dist, where = 'mid', c = 'red', \
            #     label = 'model total')

            # Draw the components
            L_name = submodel.name.replace('SubModel', 'L')
            if ppc_d is not None: 
                ppc_dists = np.asarray(ppc_d[L_name])
            else: ppc_dists = np.asarray(self.model.ppc_d[L_name]) # convert from theano array
            if len(ppc_dists.shape) == 3:
                if ppc_dists.shape[0] == 1:
                    ppc_dists = ppc_dists[0]
                else:
                    sys.exit('PlotTools::PlotPosteriorPredictive(): unexpected shape')
            print("number of ppc_dists is %i" % ppc_dists.shape[0])
            mean_ppc_dist = np.mean(ppc_dists,axis=0) #get mean counts per bin to look at residuals
            for j in range(ppc_dists.shape[0]):
                dist = ppc_dists[j]
                #if j==1: print(dist)
                if normalize:
                    dist = dist / exposure
                if differential:
                    dist = dist / st.fit.bin_wid
                ax_spectra[i].step(st.fit.bin_centers, dist, where = 'mid', c = 'tab:orange', alpha = 1/256, zorder = 0, label='%i ppc_dists' % ppc_dists.shape[0])

            # Draw the residuals
            pulls = (observed_dist - mean_ppc_dist)/np.sqrt(observed_dist) #replaced fixed_dist+floated_dist with mean_ppc_dist
            ax_resid[i].scatter(st.fit.bin_centers, pulls, marker = 'o', s = 1., c = 'k')
            # Draw the residuals hist from the right
            pulls[pulls == -np.inf] = 0.
            tmp_hist, tmp_bin_edges = np.histogram(a = pulls, bins = 'rice', density = False)
            tmp_bin_wid = tmp_bin_edges[1] - tmp_bin_edges[0]
            tmp_x_max = ax_resid[i].get_xlim()[1]
            tmp_hist  = -1 * tmp_hist
            tmp_hist_left = tmp_x_max
            ax_resid[i].barh(tmp_bin_edges[:-1], tmp_hist, align = 'edge', height = tmp_bin_wid, left = tmp_hist_left, color = 'k', alpha = 0.3, zorder = 0)

        #fig = plt.figure('fig_model_result_legend')
        #ax = fig.gca()
        #ax.legend(*ax_spectra[0].get_legend_handles_labels(), loc='center', fontsize='5')
        #ax.axis('off')

        fig_filename = plot_dir + fig_name + '.png'
        plt.savefig(fig_filename, format='png', dpi=720)

    def PlotIntegratedCountsDecayChain_v2(self, dC):
        """
        Plotting integrated counts from prior and posterior in bar graph form
        for each decay chain.
        """
        st = self.settings
        model = self.model
        tr = TraceTools.TraceTools(st)
        #tr.SetModel(model)

        fig_name = 'fig_intCounts_%s' % dC
        fig = plt.figure(fig_name)
        base_dir = os.environ['MODEL_DIR']
        model_dir = st.model_dirname.lstrip('../../FitSpectra_Models/')
        plot_dir = base_dir + '/' + model_dir + '/DCIntCtPlots/'

        prior_counts_dict = {}
        prior_counts_error_dict = {}
        posterior_counts_error_dict = {}
        posterior_counts_dict = {}
        toymc_counts_dict = {}
        prior_values_list = []
        prior_values_error_list = []
        posterior_values_error_list = []
        posterior_values_list = []
        toymc_values_list = []
        key_name_list = []
        varname_list = []
        varname_x_list = []
        posterior_int_counts_list = []
        posterior_int_counts_error_list = []
        prior_int_counts_list = []
        prior_int_counts_error_list = []
        toymc_int_counts_list = []
        posterior_key_list = []
        prior_key_list = []

        if st.multitrace_analysis:
            avg_p_modes, p_scales = tr.GetAvgModeAndError()
        
        for q, submodel in enumerate(model.submodel_list):
            self.SetSubModel(submodel)
            dag_df = submodel.dag_df
            for component in submodel.component_list:
                if component.floated and component.component_dict['decay_chain'] == dC:
                    def h(str):
                        return str

                    varname = dag_df[component.name][h('p_rv_name')]
                    if varname == None: continue
                    if 'bulk' in varname: varname = varname.lstrip("p_%s_bulk_" % dC)
                    elif 'surf' in varname: varname = varname.lstrip("p_%s_surf_" % dC)
                    elif 'linesource' in varname: varname = varname.lstrip("p_%s_linesource_" % dC)
                    else: varname = varname.lstrip("p_%s_" % dC)
                    if 'RadShieldPb' in varname: varname = "RadShieldPb"
                    if 'Thermosyphon' in varname and 'M1' in varname: varname = "M1TSS"
                    if 'Thermosyphon' in varname and 'M2' in varname: varname = "M2TSS"

                    # Prepare figure inputs
                    if st.multitrace_analysis:
                        #avg_p_modes, p_scales = tr.GetAvgModeAndError()
                        posterior_dist = component.fit_dist * avg_p_modes[dag_df[component.name][h('p_rv_name')]]
                        posterior_dist_error = component.fit_dist * p_scales[dag_df[component.name][h('p_rv_name')]]
                    else:	
                        posterior_dist = component.fit_dist * component.p_mode
                        posterior_dist_error = 0
                    prior_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                    prior_dist_error = component.fit_dist * dag_df[component.name]['prior_scale']
                    if st.toymc:
                      toymc_dist = component.fit_dist * dag_df[component.name]['prior_loc']
                      if dag_df[component.name][h('p_rv_name')].lstrip("p_%s_" % dC) in st.toymc_targeted_vals_comp and dC=='Th':
                          print('VARNAME IS %s' % varname)
                          toymc_dist = toymc_dist * st.toymc_targeted_vals_mult

                    if varname not in posterior_counts_dict.keys():
                        posterior_counts_dict[varname] = np.sum(posterior_dist)
                        posterior_counts_error_dict[varname] = (np.sum(posterior_dist_error))**2
                        prior_counts_dict[varname] = np.sum(prior_dist)
                        prior_counts_error_dict[varname] = (np.sum(prior_dist_error))**2
                        if st.toymc: toymc_counts_dict[varname] = np.sum(toymc_dist)
                    else:
                        posterior_counts_dict[varname] = posterior_counts_dict[varname] + np.sum(posterior_dist)
                        posterior_counts_error_dict[varname] = posterior_counts_error_dict[varname] + (np.sum(posterior_dist_error))**2
                        prior_counts_dict[varname] = prior_counts_dict[varname] + np.sum(prior_dist)
                        prior_counts_error_dict[varname] = prior_counts_error_dict[varname] + (np.sum(prior_dist_error))**2
                        if st.toymc: toymc_counts_dict[varname] = toymc_counts_dict[varname] + np.sum(toymc_dist)

        posterior_values_list = list(posterior_counts_dict.values())
        prior_values_list = list(prior_counts_dict.values())
        if st.toymc: toymc_values_list = list(toymc_counts_dict.values())
        key_name_list = list(posterior_counts_dict.keys())
        posterior_int_counts_list = np.array(posterior_values_list)
        prior_int_counts_list = np.array(prior_values_list)
        if st.toymc: toymc_int_counts_list = np.array(toymc_values_list)
        varname_list = np.array(key_name_list)
        varname_x_list = np.arange(1,len(key_name_list)+1)
        if st.toymc:
          offset = 0.33
          width = 0.33
        else:
          offset = 0.25
          width = 0.5

        #Errors
        for varname in varname_list:
            posterior_counts_error_dict[varname] = mt.sqrt(posterior_counts_error_dict[varname])
            prior_counts_error_dict[varname] = mt.sqrt(prior_counts_error_dict[varname])
        posterior_values_error_list = list(posterior_counts_error_dict.values())
        prior_values_error_list = list(prior_counts_error_dict.values())
        posterior_int_counts_error_list = np.array(posterior_values_error_list)
        prior_upper_error_limits = prior_values_error_list
        prior_lower_error_limits = []
        index = 0
        for value in prior_values_error_list:
            if value > prior_int_counts_list[index]: prior_lower_error_limits.append(prior_int_counts_list[index])
            else: prior_lower_error_limits.append(value)
            index += 1
        prior_int_counts_error_list = [prior_lower_error_limits, prior_upper_error_limits]

        #Plotting
        if len(varname_list) > 0 and not st.combined_groups:
            if 'U' in dC or 'Rn' in dC: #Since default color of U238/Rn222 is already gray, change it to black so that prior remains gray.
                plt.bar(varname_x_list+offset, posterior_int_counts_list , width = width, color = 'k', yerr = posterior_int_counts_error_list, ecolor ='red', label = 'Posterior Cts. (%.3e)' % sum(posterior_int_counts_list))
            else:
                plt.bar(varname_x_list+offset, posterior_int_counts_list , width = width, color = self.GetDecayChainColor(dC), yerr = posterior_int_counts_error_list, ecolor ='k', label = 'Posterior Cts. (%.3e)' % sum(posterior_int_counts_list))
            if st.toymc: plt.bar(varname_x_list, toymc_int_counts_list, width = width, color = 'blue', label = 'ToyMC Dataset Cts. (%.3e)' % sum(toymc_int_counts_list))
            plt.bar(varname_x_list-offset, prior_int_counts_list, width = width, color = 'grey', yerr = prior_int_counts_error_list, ecolor = 'k', label = 'Prior Cts. (%.3e)' % sum(prior_int_counts_list))
            plt.xticks(ticks = varname_x_list, labels = varname_list, rotation = 90, fontsize = 10)
            if st.toymc:
              plt.title('Integrated Cts. (%s) from the Prior, Posterior, and SimDataset ' % dC)
            else:
              plt.title('Integrated Cts. (%s) from the Prior and Posterior' % dC)
            plt.xlabel('Component Groups')
            if 'Rn' in dC or 'Co' in dC or '68Ge' in dC:
                plt.yscale('log')
            plt.ylabel('Integrated cts.')
            plt.legend()
            if not os.path.exists(plot_dir):
                os.makedirs(plot_dir)
            fig_filename = plot_dir + fig_name + '_' + str(st.mcmc_seed_number) + '.png'
            plt.savefig(fig_filename, bbox_inches='tight')


    def PlotCovMatrix(self):
        cov = self.model.cov

        fig, ax = plt.subplots(num = 'fig_cov', figsize=(11, 9))
        plt.subplots_adjust(left=.12, bottom=.19, right=.98, top=.945)
        g = sns.heatmap(cov, mask=None, cmap=cmap, vmax=.3, center=0,
        square=True, linewidths=.5, cbar_kws={"shrink": .5})
        g.set_yticklabels(g.get_yticklabels(), rotation = 0, fontsize = 8)
        g.set_xticklabels(g.get_xticklabels(), rotation = 90, fontsize = 8)

    def PlotCorrMatrix(self):
        corr = self.model.corr

        fig, ax = plt.subplots(num = 'fig_corr', figsize=(11, 9))
        plt.subplots_adjust(left=.12, bottom=.19, right=.98, top=.945)
        g = sns.heatmap(corr, mask=None, cmap=cmap, vmax=.3, center=0,
        square=True, linewidths=.5, cbar_kws={"shrink": .5})
        g.set_yticklabels(g.get_yticklabels(), rotation = 0, fontsize = 8)
        g.set_xticklabels(g.get_xticklabels(), rotation = 90, fontsize = 8)

def _count(a, axis=None):
    """
    Count the number of non-masked elements of an array.
    This function behaves like np.ma.count(), but is much faster
    for ndarrays.
    Ref: https://github.com/scipy/scipy/blob/v0.14.0/scipy/stats/stats.py#L3467
    """
    if hasattr(a, 'count'):
        num = a.count(axis=axis)
        if isinstance(num, np.ndarray) and num.ndim == 0:
            # In some cases, the `count` method returns a scalar array (e.g.
            # np.array(3)), but we want a plain integer.
            num = int(num)
    else:
        if axis is None:
            num = a.size
        else:
            num = a.shape[axis]
    return num

def chstwo(bins1, bins2, ddof=0, axis=0):
    """
    Chi-square test for difference between two data sets. Return the statistic and the p-value.
    Uses _count() to drop from the chi-square sum any entries for which both values are 0; the degrees of freedom are decremented for each dropped case.

    Comments on relation to NRC's chstwo() and SciPy's chi2.sf():
        -bins1 :: f_obs
        -bins2 :: f_exp
        -ddof :: adjustment to dof ... related to knstrn ... dof = num_obs - 1 - ddof ... see NRC discussion of arguments to chstwo algorithm.
            ... if data sets are of equal integral (perhaps normalized) then knstrn = 0, ddof = 0, dof = num_obs - 1 - 0
            ... if data sets are not of equal integral then knstrn = -1, ddof = -1, dof = num_obs - 1 - (-1) = num_obs
        -Evaluating the prob from the chi2 distribution:
            ... NRC defines gammq as 1 - P, where P is probability that the observed chi2 for a correct model should be less than a value chi2.
                gammq(0.5*df, 0.5*chi2)
            ... For scipy, we'd have gammq = 1 - scipy.stats.chi2.cdf(x, df, loc=0, scale=1)
                or gammq = scipy.stats.chi2.sf(x, df, loc=0, scale=1) ... sf is survival function (also defined as 1 - cdf, but sf is sometimes more accurate)
    """
    # check inputs
    if len(bins1) != len(bins2):
        return 'Error: chstwo: len(bins1) != len(bins2)'
    # where bins1[i]=bins2[i]=0, mask entry i
    bins1, bins2 = np.ma.masked_where(condition = [(bins1 == bins2) & (bins1==0), (bins2 == bins1) & (bins2==0)], a = [bins1, bins2])
    # Do the test
    terms = (bins1 - bins2)**2 / (bins1 + bins2) # Terms with division by zero have been masked out. Terms evaluating to zero are kept.
    stat = terms.sum(axis=axis)
    num_obs = _count(terms, axis=axis) # returns number of non-masked terms in stat
    ddof = np.asarray(ddof)
    p = stats.chi2.sf(stat, num_obs - 1 - ddof)
    print('chi2.sf(x = %f, df = %d), num_obs = %d, ddof = %d' % (stat, num_obs - 1 - ddof, num_obs, ddof))
    return stat, p

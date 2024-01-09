"""
A custom PyMC model holding submodels and their components. This class also
handles the structuring of the directed acyclic graph.
Ref:
	https://docs.pymc.io/api/model.html
"""
import sys
import os
import time
import numpy as np
import pandas as pd
import pymc3 as pm
from theano import function
import theano.tensor as tt

import Management.Private_ConfigData_v7 as ConfigData
cfgd = ConfigData.ConfigData()
import Tools.ToyMCTools as ToyMCTools
import Tools.TraceTools as TraceTools
import Classes.SubModel as SubModel
from pymc3.backends.tracetab import trace_to_dataframe

#hw_nickname_dict = {
#    'bulk_RadShieldAssembly_001_RadShieldCuInner_001': 'bulk_RadShieldCuInner',
#    'bulk_RadShieldAssembly_001_RadShieldCuOuter_001': 'bulk_RadShieldCuOuter',
#    'bulk_RadShieldAssembly_001_RadShieldPb': 'bulk_RadShieldPb',
#    'pbbrem_RadShieldAssembly_001_RadShieldPb_001': 'pbbrem_RadShieldPb'
#}

class Model():
	"""
	"""

	def __init__(self, model_dict, settings):
		self.model_dict = model_dict
		self.settings = settings
		st = self.settings

		self.pymc_model = pm.Model()

		# Initialize some vars
		self.map_d = None

		# Begin: overall procedure needed for handling real data or toymc
		self.InitSubModelList()
		self.ConstructDAGDataFrame()
		for submodel in self.submodel_list:
			for component in submodel.component_list:
				component.InitDists()
			submodel.InitExposure()
			submodel.InitRuntime()
			
		if st.toymc:
			# exp_rate_dist_integral_list = []
			exp_count_dist_integral_list = []
			for submodel in self.submodel_list:
				# submodel.GetExpectedRateDistIntegral()
				# exp_rate_dist_integral_list.append(submodel.exp_rate_dist_integral)
				submodel.GetExpectedCountDistIntegral()
				exp_count_dist_integral_list.append(submodel.exp_count_dist_integral)
			# settings.largest_exp_rate_dist_integral = max(exp_rate_dist_integral_list)
			# print('Model::__init__():', exp_rate_dist_integral_list)
			settings.largest_exp_count_dist_integral = max(exp_count_dist_integral_list)
			print('Model::__init__():', exp_count_dist_integral_list)
			for submodel in self.submodel_list:
				submodel.InitHits()
				submodel.InitToyMCExposure()
		startTime = time.time()
		for submodel in self.submodel_list:
			# submodel.InitData()
			submodel.InitHits()
			#submodel.InitRuntime()
			submodel.InitDists()
			for component in submodel.component_list:
				component.InitRemainingDists()
			submodel.AppendFitEngineDistsToDAGDF()
		executionTime = (time.time() - startTime)
		print(' ')
		print('Sampling time to create toymc datasets for all submodels: %f seconds' % executionTime)
		print(' ')
		self.InsertLikelihoods()
		# End: overall procedure needed for handling real data or toymc

	def InitSubModelList(self):
		st = self.settings

		self.submodel_name_list = sorted(self.model_dict.keys())
		self.submodel_list = []

		# Loop submodels
		for submodel_name in self.submodel_name_list:
			# Create SubModel instance
			submodel_dict = self.model_dict[submodel_name]
			submodel = SubModel.SubModel(submodel_name, submodel_dict, st)
			# Add SubModel instance into Model instance
			self.AddSubModel(submodel)

	def AddSubModel(self, submodel):
		self.submodel_list.append(submodel)

	#####################
	# Methods for setting up and probing pymc model
	#####################

	def MixtureDensity(self, submodel):
		"""
		Evaluation of the floated dist mixture, given weigths,
		for use in a McmcModel likelihood term
		"""
		w = tt.stack(submodel.dag_df.loc['p_rv'].values.tolist()) # convert from pandas series to numpy ndarray to python list
		dist = tt.stack(submodel.dag_df.loc['fit_engine_dist'].values.tolist())
		#print(str(len(submodel.dag_df.loc['fit_engine_dist'].values.tolist()))+'    '+submodel.name)
		logp = tt.log(w) + tt.log(dist).T
		return tt.sum(tt.exp(logp), axis=1)

	def InsertLikelihoods(self):
		"""
		Insert the submodel likelihoods into the model context.
		"""
		with self.pymc_model:
			for submodel in self.submodel_list:
				label = 'L_%s' % submodel.name.replace('SubModel_','')
				pm.Poisson(label, mu = self.MixtureDensity(submodel), observed = submodel.fit_engine_dist, testval = submodel.dag_df.loc['prior_loc'])

	def Sample(self):
		"""
		Do sampling for posterior inference. Save or load trace.
		Ref:
			https://docs.pymc.io/api/inference.html
		"""
		st = self.settings

		if os.path.isdir(st.trace_dirname):
			self.trace = self.LoadTrace(st.trace_dirname)
		else:
			with self.pymc_model:
				step = self.GetStep()
				start = self.GetStart()
				self.trace = pm.sample(chains = st.mcmc_chains, cores = st.mcmc_cores, draws = st.mcmc_draws, step = step, start = start, target_accept = st.mcmc_target_accept, random_seed = st.seed_number)
                                #added cores option and target_accept option and random_seed option -Chris
			self.SaveTrace()

	def GetStep(self, step_method = None):
		st = self.settings

		if st.mcmc_step_method == None: return None
		if st.mcmc_step_method == 'NUTS': return pm.NUTS()
		if st.mcmc_step_method == 'Hamiltonian': return pm.Hamiltonian()
		if st.mcmc_step_method == 'Metropolis': return pm.Metropolis()

	def GetStart(self, startvals_type = None):
		st = self.settings

		if st.mcmc_startvals_type == 'default': return None
		if st.mcmc_startvals_type == 'map': return self.FindMap()
		if st.mcmc_startvals_type == 'test_point': return self.pymc_model.test_point

	def FindMap(self):
		"""
		Find MAP estimate of model
		"""
		st = self.settings

		if self.map_d == None:
			print('Model::FindMap(): MAP already calculated. Returning map_d')
			return self.map_d

		with self.pymc_model:
			self.map_d = pm.find_MAP()

		return self.map_d

	def LoadTrace(self, trace_dirname):
		"""
		Load a trace.
		"""
		st = self.settings

		print('Loading saved trace: %s' % trace_dirname)
		return pm.load_trace(trace_dirname, self.pymc_model)

	def SaveTrace(self):
		"""
		Save the mcmc trace object.
		The directory will be created, if it does not already exist
		"""
		st = self.settings

		print('Saving trace: %s' % st.trace_dirname)
		pm.save_trace(self.trace, st.trace_dirname)
		pd_trace = trace_to_dataframe(self.trace)
		pd_trace.to_pickle(st.trace_dirname + "/trace.pkl")

	def Debug(self):
		"""
		Ref:
			https://docs.pymc.io/api/model.html
		"""
		print('Fit: checking set params for free_RVs (logp(testval).eval() is not transformed)')
		varname_list = []
		for submodel in self.submodel_list:
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
					if varname in varname_list: continue
					else: varname_list.append(varname)
					print('    ', varname, dag_df[component.name][h('prior_loc')], dag_df[component.name][h('prior_scale')], dag_df[component.name][h('p_rv_testval')])
					mu, sd, testval = dag_df[component.name][h('prior_loc')], dag_df[component.name][h('prior_scale')], dag_df[component.name][h('p_rv_testval')]
					print('      logp(testval).eval() = ', pm.TruncatedNormal.dist(mu = mu, sd = sd, lower = 0., upper = np.inf).logp(testval).eval())
		print('Debugging pymc_model:')
		with self.pymc_model:
			print('    vars')
			for item in self.pymc_model.vars:
				print('       ', item.name, item.logp(self.pymc_model.test_point))
			print('    named_vars')
			for item in self.pymc_model.named_vars:
				print('       ', item, type(item))
			print('    basic_RVs')
			for item in self.pymc_model.basic_RVs:
				print('       ', item.name, item.logp(self.pymc_model.test_point))
			print('    free_RVs')
			for item in self.pymc_model.free_RVs:
				print('       ', item.name, item.logp(self.pymc_model.test_point))
			print('    observed_RVs')
			for item in self.pymc_model.observed_RVs:
				print('       ', item.name, item.logp(self.pymc_model.test_point))
			print('    unobserved_RVs')
			for item in self.pymc_model.unobserved_RVs:
				print('       ', item.name)
			print('    deterministics')
			for item in self.pymc_model.deterministics:
				print('       ', item.name)
		sys.exit('Model::Debug(): Exited debugging')

	def GetRVName(self, component, model_pool_type = None):
		"""
		Component_<detector>_<decay_chain>_<hardware_component>_<generator>
		_<detector_type>_<cut>_<config>
		'p_' for prior
		'hp_' for hyperprior
		"""
		st = self.settings

		# Allow for temporarily selecting the naming convention
		if model_pool_type == None:
			model_pool_type = st.model_pool_type

		if model_pool_type == 'unpooled':
			return 'p_%s' % component.name.replace('Component_','')
		if model_pool_type == 'match_all_but_cut':
			name = component.name.split('_')
			del name[-2] # Remove cut so other cuts can match
			name = '_'.join(name)
			return 'p_%s' % name.replace('Component_','')
		if model_pool_type == 'match_dc_hw':
			dC = component.component_dict['decay_chain']
			hwC = component.component_dict['hardware_component']
			# if '_' in hwC:
			# 	hwC = hwC.split('_')[-2]
			tmp_hwC = hwC
			#if hwC in hw_nickname_dict:
				#tmp_hwC = hw_nickname_dict[hwC]
			name = '_'.join([dC, tmp_hwC])
			return 'p_%s' % name
		if model_pool_type == 'match_dc_mtr':
			dC = component.component_dict['decay_chain']
			hwC = component.component_dict['hardware_component']
			material = cfgd.hardwareComponentDict[hwC]['material'] # Replace the hwC with material, so other hwCs can match
			name = '_'.join([dC, material])
			return 'p_%s' % name

	#####################
	# Analysis
	#####################

	def Summary(self, var_names = None):
		"""
		Ref:
			https://docs.pymc.io/api/stats.html
		"""
		print(pm.summary(self.trace, var_names))

	def TracePlot(self, varnames = None, priors = None, combined = False):
		"""
		Ref:
			https://docs.pymc.io/api/plots.html
		"""
		pm.traceplot(self.trace, varnames = varnames, priors = priors, combined = combined)

	def ForestPlot(self, varnames = None, rhat = False):
		"""
		Ref:
			https://docs.pymc.io/api/plots.html
		"""
		pm.forestplot(self.trace, varnames = varnames, rhat = rhat)

	def PosteriorPlot(self, varnames = None):
		"""
		Ref:
			https://docs.pymc.io/api/plots.html
		"""
		pm.plot_posterior(self.trace, varnames = varnames)

	def GraphViz(self):
		"""
		Visualize the directed acyclic graph using a graphviz Digraph (directed
		graph) object
		Ref:
			https://github.com/pymc-devs/pymc3/blob/master/pymc3/model_graph.py
			https://graphviz.readthedocs.io/en/stable/
			https://graphviz.readthedocs.io/en/stable/manual.html#attributes
			https://www.graphviz.org/doc/info/attrs.html#d:ratio
		"""
		st = self.settings

		graph = pm.model_to_graphviz(self.pymc_model)
		graph.attr(size = '10,7.5') # width,height
		graph.attr(ratio = 'fill') # height/width
		graph.render('graph.gv', view = False, cleanup = True)
		basename = 'graph.gv.pdf'
		os.rename(basename, st.model_dirname + '/' + basename)

	#####################
	# Methods to be overridden by subclasses for specific model types
	#####################

	def ConstructDAGDataFrame(self):
		"""
		Determine any parent and child links in DAG.
		Construct the masked arrays, jagged arrays, matrices, or linked lists for
		calculation of total L according to DAG.
		"""
		print('Model::ConstructDAGDataFrame()', 'Overide?')

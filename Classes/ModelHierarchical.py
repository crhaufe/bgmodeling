"""
A custom PyMC model holding submodels and their components. This class also
handles the structuring of the directed acyclic graph.
Ref:
	https://docs.pymc.io/api/model.html
	https://docs.pymc.io/notebooks/multilevel_modeling.html
	http://www.stat.columbia.edu/~gelman/research/published/multi2.pdf
"""
import sys
import numpy as np
import pandas as pd
import pymc3 as pm

from Tools.DistributionTools import *
import Management.Private_ConfigData as ConfigData
cfgd = ConfigData.ConfigData()
import Classes.Model as Model

class ModelHierarchical(Model.Model):
	"""
	"""

	def GetUniqueHyperParams(self):
		st = self.settings

		print('    Gathering hyper parameters. pool_type = %s' % 'match_dc_mtr')
		with self.pymc_model:
			# This dict of hyper params spans all submodels
			hyper_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					# Check that hyper param will represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] != None:
						name = 'h' + self.GetRVName(component, 'match_dc_mtr')
						if (name not in hyper_d) and component.floated:
							print('        %s' % name)
							hyper_d[name] = {}
							hyper_d[name]['hprior_loc'] = component.prior_loc
							hyper_d[name]['hprior_scale'] = component.prior_scale
							hmu, hsd = hyper_d[name]['hprior_loc'], hyper_d[name]['hprior_scale']
							if st.toymc:
								if st.toymc_rand_vals:
									# Center this hyper param on a rand value from the expected dist
									hyper_d[name]['hprior_loc'] = pm.TruncatedNormal.dist(mu = hmu, sd = 3*hsd, lower = 0., upper = np.inf).random()
									hmu = hyper_d[name]['hprior_loc']
							if st.mcmc_rand_testvals: testval = pm.TruncatedNormal.dist(mu = hmu, sd = 3*hsd, lower = 0., upper = np.inf).random()
							else: testval = hmu
							hyper_d[name]['hp_rv_testval'] = testval
							hyper_d[name]['hp_rv_dist'] = pm.TruncatedNormal.dist(mu = hmu, sd = hsd, lower = 0., upper = np.inf)
							hyper_d[name]['hp_rv'] = pm.TruncatedNormal(name, mu = hmu, sd = hsd, lower = 0., testval = testval)
		return hyper_d

	def GetUniquePooledParams(self, hyper_d):
		st = self.settings

		print('    Gathering subsequent pooled parameters. pool_type = %s' % 'match_dc_hw')
		with self.pymc_model:
			# This dict of pooled params spans all submodels
			pooled_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					# Check that param will represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] != None:
						name = self.GetRVName(component, 'match_dc_hw')
						hname = 'h' + self.GetRVName(component, 'match_dc_mtr')
						if (name not in pooled_d) and component.floated:
							print('        %s' % name)
							pooled_d[name] = {}
							pooled_d[name]['prior_loc'] = component.prior_loc
							pooled_d[name]['prior_scale'] = component.prior_scale
							mu, sd = pooled_d[name]['prior_loc'], pooled_d[name]['prior_scale']
							hmu, hsd = hyper_d[hname]['hprior_loc'], hyper_d[hname]['hprior_scale']
							if st.toymc:
								# Treat this true pooled param as a sample from the hyper param's dist
								pooled_d[name]['prior_loc'] = hyper_d[hname]['hp_rv_dist'].random() # don't exaggerate distribution scale/sd here
								component.prior_loc = pooled_d[name]['prior_loc']
								mu = pooled_d[name]['prior_loc']
							if st.mcmc_rand_testvals: testval = pm.TruncatedNormal.dist(mu = hmu, sd = 3*pooled_d[name]['prior_scale'], lower = 0., upper = np.inf).random()
							else: testval = mu
							pooled_d[name]['p_rv_testval'] = testval
							pooled_d[name]['p_rv_dist'] = hyper_d[hname]['hp_rv_dist']
							pooled_d[name]['p_rv'] = pm.TruncatedNormal(name, mu = hyper_d[hname]['hp_rv'], sd = pooled_d[name]['prior_scale'], lower = 0., testval = testval)
							# Note that *prior_* and component.*prior_* remain as the true values.
							# In the case of toymc they are the true drawn value, and in the case of real data they match hprior_* values
							# Note that p_rv_* is what would be available/assumed when using real data.
							# Note that component.*prior_* gets used to make the toymc spectrum.
							# Note that *prior_* gets used for posterior vs prior ratios
							# Note that PlotPosteriors will use p_rv_dist for the available/assumed prior dist, and in the case of toymc pooled hier params the true *prior_* will be also shown
		return pooled_d

	def GetUniqueUnpooledParams(self):
		st = self.settings

		print('    Gathering unpooled parameters. pool_type = %s' % 'unpooled')
		with self.pymc_model:
			# This dict of unpooled params spans all submodels
			unpooled_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					# Check that param does not represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] == None:
						name = self.GetRVName(component, 'unpooled')
						if (name not in unpooled_d) and component.floated:
							print('        %s' % name)
							unpooled_d[name] = {}
							unpooled_d[name]['prior_loc'] = component.prior_loc
							unpooled_d[name]['prior_scale'] = component.prior_scale
							mu, sd = unpooled_d[name]['prior_loc'], unpooled_d[name]['prior_scale']
							if st.toymc:
								if st.toymc_rand_vals:
									# Center this unpooled param on a rand value from the expected dist
									unpooled_d[name]['prior_loc'] = pm.TruncatedNormal.dist(mu = mu, sd = 3*sd, lower = 0., upper = np.inf).random()
									component.prior_loc = unpooled_d[name]['prior_loc']
									mu = unpooled_d[name]['prior_loc']
							if st.mcmc_rand_testvals: testval = pm.TruncatedNormal.dist(mu = mu, sd = 3*sd, lower = 0., upper = np.inf).random()
							else: testval = mu
							unpooled_d[name]['p_rv_testval'] = testval
							unpooled_d[name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = mu, sd = sd, lower = 0., upper = np.inf)
							unpooled_d[name]['p_rv'] = pm.TruncatedNormal(name, mu = mu, sd = sd, lower = 0., testval = testval)
		return unpooled_d

	def GetUniqueFixedParams(self):
		st = self.settings

		print('    Gathering fixed parameters.')
		with self.pymc_model:
			# This dict of fixed params spans all submodels
			fixed_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					name = self.GetRVName(component, 'unpooled')
					if (name not in fixed_d) and not component.floated:
						fixed_d[name] = {}
						print('        %s' % name)
						fixed_d[name] = {}
						fixed_d[name]['prior_loc'] = component.prior_loc
						fixed_d[name]['prior_scale'] = component.prior_scale
						mu, sd = fixed_d[name]['prior_loc'], fixed_d[name]['prior_scale']
						if st.toymc:
							if st.toymc_rand_vals:
								# Center this unpooled param on a rand value from the expected dist
								fixed_d[name]['prior_loc'] = pm.TruncatedNormal.dist(mu = mu, sd = 3*sd, lower = 0., upper = np.inf).random()
								component.prior_loc = fixed_d[name]['prior_loc']
								mu = fixed_d[name]['prior_loc']
						if 'prior_loc_fitfixed' in component.component_dict and component.component_dict['prior_loc_fitfixed'] != None:
							fixed_d[name]['prior_loc'] = component.component_dict['prior_loc_fitfixed']
							mu = fixed_d[name]['prior_loc']
						fixed_d[name]['p_rv'] = mu
		return fixed_d

	#####################
	# Methods to be overridden by subclasses for specific model types
	#####################

	def ConstructDAGDataFrame(self):
		st = self.settings

		print('Constructing DAG:')

		hyper_d = self.GetUniqueHyperParams()
		pooled_d = self.GetUniquePooledParams(hyper_d)
		unpooled_d = self.GetUniqueUnpooledParams()
		fixed_d = self.GetUniqueFixedParams()

		# Loop and connect components to their respective params
		print('    Connecting components and parameters.')
		with self.pymc_model:
			for submodel in self.submodel_list:
				# A different d (~dag_df) for each submodel
				dag_d = {}
				for component in submodel.component_list:
					dag_d[component.name] = {}

					# Check if pooled or hyper
					# Check that param will represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] != None:
						name = 'h' + self.GetRVName(component, 'match_dc_mtr')
						if name in hyper_d:
							dag_d[component.name]['hprior_loc'] = hyper_d[name]['hprior_loc']
							dag_d[component.name]['hprior_scale'] = hyper_d[name]['hprior_scale']
							dag_d[component.name]['hp_rv_name'] = name
							dag_d[component.name]['hp_rv_testval'] = hyper_d[name]['hp_rv_testval']
							dag_d[component.name]['hp_rv_dist'] = hyper_d[name]['hp_rv_dist']
							dag_d[component.name]['hp_rv'] = hyper_d[name]['hp_rv']
							print('        %s' % dag_d[component.name]['hp_rv_name'])
						name = self.GetRVName(component, 'match_dc_hw')
						if name in pooled_d:
							dag_d[component.name]['prior_loc'] = pooled_d[name]['prior_loc']
							dag_d[component.name]['prior_scale'] = pooled_d[name]['prior_scale']
							dag_d[component.name]['p_rv_name'] = name
							dag_d[component.name]['p_rv_testval'] = pooled_d[name]['p_rv_testval']
							dag_d[component.name]['p_rv_dist'] = pooled_d[name]['p_rv_dist']
							dag_d[component.name]['p_rv'] = pooled_d[name]['p_rv']
							print('        %s' % dag_d[component.name]['p_rv_name'])

					# Check if unpooled
					name = self.GetRVName(component, 'unpooled')
					if name in unpooled_d:
						dag_d[component.name]['hprior_loc'] = None
						dag_d[component.name]['hprior_scale'] = None
						dag_d[component.name]['hp_rv_name'] = None
						dag_d[component.name]['hp_rv_testval'] = None
						dag_d[component.name]['hp_rv_dist'] = None
						dag_d[component.name]['hp_rv'] = None

						dag_d[component.name]['prior_loc'] = unpooled_d[name]['prior_loc']
						dag_d[component.name]['prior_scale'] = unpooled_d[name]['prior_scale']
						dag_d[component.name]['p_rv_name'] = name
						dag_d[component.name]['p_rv_testval'] = unpooled_d[name]['p_rv_testval']
						dag_d[component.name]['p_rv_dist'] = unpooled_d[name]['p_rv_dist']
						dag_d[component.name]['p_rv'] = unpooled_d[name]['p_rv']
						print('        %s' % dag_d[component.name]['p_rv_name'])

					# Check if fixed
					name = self.GetRVName(component, 'unpooled')
					if name in fixed_d:
						dag_d[component.name]['hprior_loc'] = None
						dag_d[component.name]['hprior_scale'] = None
						dag_d[component.name]['hp_rv_name'] = None
						dag_d[component.name]['hp_rv_testval'] = None
						dag_d[component.name]['hp_rv_dist'] = None
						dag_d[component.name]['hp_rv'] = None

						dag_d[component.name]['prior_loc'] = fixed_d[name]['prior_loc']
						dag_d[component.name]['prior_scale'] = fixed_d[name]['prior_scale']
						dag_d[component.name]['p_rv_name'] = None
						dag_d[component.name]['p_rv_testval'] = None
						dag_d[component.name]['p_rv_dist'] = None
						dag_d[component.name]['p_rv'] = fixed_d[name]['p_rv']
						print('        %s (fixed)' % name)

				submodel.dag_df = pd.DataFrame.from_dict(dag_d)

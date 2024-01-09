"""
A custom PyMC model holding submodels and their components. This class also
handles the structuring of the directed acyclic graph.
Ref:
	https://docs.pymc.io/api/model.html
"""
import sys
import numpy as np
import pandas as pd
import pymc3 as pm
from Tools.DistributionTools import *
import Management.Private_ConfigData as ConfigData
cfgd = ConfigData.ConfigData()
import Classes.Model as Model

class ModelPooled(Model.Model):
	"""
	"""

	def GetUniquePooledParams(self):
		st = self.settings

		print('    Gathering pooled parameters. pool_type = %s' % 'match_dc_hw')
		with self.pymc_model:
			# This dict of pooled params spans all submodels
			pooled_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					# Check that param will represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] != None:
						name = self.GetRVName(component, 'match_dc_hw')
						if (name not in pooled_d) and component.floated:
							print('        %s' % name)
							pooled_d[name] = {}
							pooled_d[name]['prior_loc'] = component.prior_loc
							pooled_d[name]['prior_scale'] = component.prior_scale
							mu, sd = pooled_d[name]['prior_loc'], pooled_d[name]['prior_scale']
							if st.toymc:
								if st.toymc_rand_vals:
									# Center this pooled param on a rand value from the expected dist
									pooled_d[name]['prior_loc'] = pm.TruncatedNormal.dist(mu = mu, sd = 3*sd, lower = 0., upper = np.inf).random()
									component.prior_loc = pooled_d[name]['prior_loc']
									mu = pooled_d[name]['prior_loc']
							if st.mcmc_rand_testvals: testval = pm.TruncatedNormal.dist(mu = mu, sd = 3*sd, lower = 0., upper = np.inf).random()
							else: testval = mu
							pooled_d[name]['p_rv_testval'] = testval
							if st.mcmc_unconstrained == name:
								pooled_d[name]['p_rv_dist'] = pm.HalfFlat.dist()
								pooled_d[name]['p_rv'] = pm.HalfFlat(name, testval = testval)
								print('USING HALF FLAT PRIOR')
								print('Prior mean = ' + str(testval))
							elif st.mcmc_all_flat:
								pooled_d[name]['p_rv_dist'] = pm.HalfFlat.dist()
								pooled_d[name]['p_rv'] = pm.HalfFlat(name, testval = testval)
								print('USING HALF FLAT PRIOR')
								print('Prior mean = ' + str(testval))
							else:
								pooled_d[name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = mu, sd = sd, lower = 0., upper = np.inf)
								pooled_d[name]['p_rv'] = pm.TruncatedNormal(name, mu = mu, sd = sd, lower = 0., testval = testval)
								print('Prior mean = ' + str(testval))
								print('Prior scale = ' + str(sd))
		#sys.exit()
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
					print(name)
					if (name not in fixed_d) and not component.floated:
						fixed_d[name] = {}
						print('        %s' % name)
						fixed_d[name] = {}
						if 'p_Th_M1CPInterfaceCavityBottomSurface_bulk' in name or 'p_Th_M2CPInterfaceCavityBottomSurface_bulk' in name and st.toymc:
							fixed_d[name]['prior_loc'] = 0.0 #For fits to SimData where cavity is in sim dataset but fixed to 0.0 in fit
						else:
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
						print('Prior mean = ' + str(mu))
		#sys.exit()
		return fixed_d

	#####################
	# Methods to be overridden by subclasses for specific model types
	#####################

	def ConstructDAGDataFrame(self):

		print('Constructing DAG:')

		pooled_d = self.GetUniquePooledParams()
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

					# Check if pooled
					# Check that param will represent level 1 or 2 sims post-processing
					if component.component_dict['hardware_component'] != None:
						name = self.GetRVName(component, 'match_dc_hw')
						if name in pooled_d:
							dag_d[component.name]['hprior_loc'] = None
							dag_d[component.name]['hprior_scale'] = None
							dag_d[component.name]['hp_rv_name'] = None
							dag_d[component.name]['hp_rv_testval'] = None
							dag_d[component.name]['hp_rv_dist'] = None
							dag_d[component.name]['hp_rv'] = None

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

	# For tracking component distributions as deterministics in graph
	# name = 'd_%s' % component.name.replace('Component_','')
	# d[component.name]['deterministic'] = pm.Deterministic(name, tt.log(d[component.name]['p_rv']) + tt.log(d[component.name]['fit_engine_dist']) )
	# For tracking component distributions as deterministics in graph
	# logp = tt.stack(submodel.dag_df.loc['deterministic'].values.tolist()).T
	# return tt.sum(tt.exp(logp), axis=1)

	# def ConstructDAGDataFrame(self):
	# 	"""
	# 	Determine any parent and child links in DAG.
	# 	Construct the masked arrays, jagged arrays, matrices, or linked lists for
	# 	calculation of total L according to DAG.
	# 	'p_' for prior
	# 	'hp_' for hyperprior
	# 	"""
	# 	st = self.settings
	#
	# 	print('Constructing DAG:')
	#
	# 	# Loop to gather the component names for which params will be pooled
	# 	print('    Gathering pooled parameters. pool_type = %s' % st.model_pool_type)
	# 	with self.pymc_model:
	# 		# This dict of pooled params spans all submodels
	# 		pooled_d = {}
	# 		for submodel in self.submodel_list:
	# 			for component in submodel.component_list:
	# 				# Check that param will represent level 1 or 2 sims post-processing
	# 				if component.component_dict['hardware_component'] != None:
	# 					name = self.GetRVName(component)
	# 					if (name not in pooled_d) and component.floated:
	# 						print('        %s' % name)
	# 						testval = component.prior_loc # insert starting values / starting guesses here
	# 						pooled_d[name] = pm.TruncatedNormal(name, mu = component.prior_loc, sd = component.prior_scale, lower = 0., testval = testval)
	#
	# 	# Loop and connect components to their respective params
	# 	print('    Gathering unpooled parameters (and connecting parameters).')
	# 	with self.pymc_model:
	# 		for submodel in self.submodel_list:
	# 			# A different d (~dag_df) for each submodel
	# 			d = {}
	# 			for component in submodel.component_list:
	# 				d[component.name] = {}
	# 				d[component.name]['submodel_name'] = submodel.name
	# 				d[component.name]['prior_loc'] = component.prior_loc
	# 				d[component.name]['prior_scale'] = component.prior_scale
	# 				d[component.name]['fit_engine_dist'] = component.fit_engine_dist
	# 				# Connect the relevant pooled param
	# 				if component.floated and (component.component_dict['hardware_component'] != None):
	# 					name = self.GetRVName(component)
	# 					d[component.name]['p_rv_name'] = name
	# 					d[component.name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = component.prior_loc, sd = component.prior_scale, lower = 0., upper = np.inf)
	# 					d[component.name]['p_rv'] = pooled_d[name]
	# 				# Create params for floated unpooled components
	# 				elif component.floated and (component.component_dict['hardware_component'] == None):
	# 					name = self.GetRVName(component, 'unpooled')
	# 					print('        %s' % name)
	# 					testval = component.prior_loc # insert starting values / starting guesses here
	# 					d[component.name]['p_rv_name'] = name
	# 					d[component.name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = component.prior_loc, sd = component.prior_scale, lower = 0., upper = np.inf)
	# 					d[component.name]['p_rv'] = pm.TruncatedNormal(name, mu = component.prior_loc, sd = component.prior_scale, lower = 0., testval = testval)
	# 				# For fixed components, set a fixed value and 'none' name as place holders
	# 				elif not component.floated:
	# 					d[component.name]['p_rv_name'] = 'none'
	# 					d[component.name]['p_rv'] = component.prior_loc
	# 				else:
	# 					sys.exit('Error: ModelPooled::ConstructDAGDataFrame(): Unexpected component type')
	# 			submodel.dag_df = pd.DataFrame.from_dict(d)

	# # Pool matching decay chain and all else
	# if st.model_pool_type == 'match_all_but_cut':
	# 	# Loop to gather the component names for which params will be pooled
	# 	with self.pymc_model:
	# 		# The dictionary of pooled params should span all submodels
	# 		pooled_d = {}
	# 		for submodel in self.submodel_list:
	# 			for component in submodel.component_list:
	# 				# Add pooled params into dict
	# 				name = self.GetRVName(component)
	# 				if (name not in pooled_d) and component.floated:
	# 					print('    %s' % name)
	# 					testval = component.prior_loc # insert starting values / starting guesses here
	# 					pooled_d[name] = pm.TruncatedNormal(name, mu = component.prior_loc, sd = component.prior_scale, lower = 0., testval = testval)
	# 	# Loop and connect components to their respective params
	# 	with self.pymc_model:
	# 		for submodel in self.submodel_list:
	# 			# A different d for each submodel
	# 			d = {}
	# 			for component in submodel.component_list:
	# 				d[component.name] = {}
	# 				d[component.name]['submodel_name'] = submodel.name
	# 				d[component.name]['prior_loc'] = component.prior_loc
	# 				d[component.name]['prior_scale'] = component.prior_scale
	# 				d[component.name]['fit_engine_dist'] = component.fit_engine_dist
	# 				if component.floated:
	# 					# Connect the relevant pooled param
	# 					name = self.GetRVName(component)
	# 					d[component.name]['p_rv_name'] = name
	# 					d[component.name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = component.prior_loc, sd = component.prior_scale, lower = 0.)
	# 					d[component.name]['p_rv'] = pooled_d[name]
	# 				else:
	# 					d[component.name]['p_rv_name'] = 'none'
	# 					d[component.name]['p_rv'] = component.prior_loc
	# 			submodel.dag_df = pd.DataFrame.from_dict(d)

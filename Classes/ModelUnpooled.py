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
import Classes.Model as Model

class ModelUnpooled(Model.Model):
	"""
	"""

	def GetUniqueUnpooledParams(self):
		st = self.settings

		print('    Gathering unpooled parameters. pool_type = %s' % 'unpooled')
		with self.pymc_model:
			# This dict of unpooled params spans all submodels
			unpooled_d = {}
			for submodel in self.submodel_list:
				for component in submodel.component_list:
					# Param can represent any sims post-processing level
					if component.component_dict['hardware_component'] == None or component.component_dict['hardware_component'] != None:
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

		print('Constructing DAG:')

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
	# 	print('    Gathering unpooled parameters (and connecting parameters).')
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
	# 				# Create params for floated unpooled components
	# 				if component.floated:
	# 					name = self.GetRVName(component, 'unpooled')
	# 					print('        %s' % name)
	# 					testval = component.prior_loc # insert starting values / starting guesses here
	# 					d[component.name]['p_rv_name'] = name
	# 					d[component.name]['p_rv_dist'] = pm.TruncatedNormal.dist(mu = component.prior_loc, sd = component.prior_scale, lower = 0., upper = np.inf)
	# 					if st.toymc:
	# 						d[component.name]['p_toymc'] = d[component.name]['p_rv_dist'].random()
	# 						d[component.name]['prior_loc'] = d[component.name]['p_toymc']
	# 						component.prior_loc = d[component.name]['p_toymc']
	# 					d[component.name]['p_rv'] = pm.TruncatedNormal(name, mu = component.prior_loc, sd = component.prior_scale, lower = 0., testval = testval)
	# 				# For fixed components, set a fixed value and 'none' name as place holders
	# 				else:
	# 					# tmp = tt.dscalar()
	# 					# tmp.tag.test_value = 1.
	# 					# f = function([tmp], tmp)
	# 					# d[component.name]['w'] = f(1.)
	# 					d[component.name]['p_rv_name'] = 'none'
	# 					d[component.name]['p_rv'] = component.prior_loc
	# 			submodel.dag_df = pd.DataFrame.from_dict(d) # component.name will be col and subsequent vars will be rows
	#
	# 	if False:
	# 		# A test
	# 		# It seems like the dataframe series follow the same ordering/sorting as the component_name_list
	# 		print('A test of dataframe access order, pertaining to submodel.dag_df:')
	# 		for submodel in self.submodel_list:
	# 			print(submodel.component_name_list)
	# 			print(submodel.dag_df.loc['prior_loc'].axes)
	# 			i = 0
	# 			for component in submodel.component_list:
	# 				print(submodel.component_name_list[i], component.prior_loc, submodel.dag_df.loc['prior_loc'][i], submodel.dag_df.loc['prior_loc'][submodel.component_name_list[i]])
	# 				i += 1
	#
	#

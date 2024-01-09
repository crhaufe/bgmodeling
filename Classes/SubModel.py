"""
"""

import sys
import numpy as np
import pandas as pd

import Tools.DataTools as DataTools
import Tools.ToyMCTools as ToyMCTools
import Classes.ComponentL1 as ComponentL1
import Classes.ComponentL2 as ComponentL2
import Classes.ComponentL4 as ComponentL4

class SubModel:
	"""
	"""

	def __init__(self, submodel_name, submodel_dict, settings):
		self.settings = settings
		self.data_tools = DataTools.DataTools(settings)
		self.toymc_tools = ToyMCTools.ToyMCTools(settings)

		self.name = submodel_name
		self.submodel_dict = submodel_dict

		self.InitComponentList()
		# self.InitData()
		# self.InitDists()

	def InitComponentList(self):
		st = self.settings

		self.component_name_list = sorted(self.submodel_dict['components'].keys())
		self.component_list = []

		#print(self.name+'               '+str(len(sorted(self.submodel_dict['components'].keys()))))

		level_list = []
		detector_list = []

		# Loop components
		for component_name in self.component_name_list:
			# Create Component instance
			component_dict = self.submodel_dict['components'][component_name]
			level = component_dict['level']
			if level == 1: component = ComponentL1.ComponentL1(component_name, component_dict, self, st)
			elif level == 2: component = ComponentL2.ComponentL2(component_name, component_dict, self, st)
			elif level == 4: component = ComponentL4.ComponentL4(component_name, component_dict, self, st)
			else:
				sys.exit('Error: SubModel::InitComponentList(): No corresponding Component subclass for %s' % str(level))
			# Add Component instance into SubModel instance
			self.AddComponent(component)
			level_list.append(level)
			detector_list.append(component_dict['detector'])

		# Check if all components of same level
		level_list = np.array(level_list)
		if not np.all(level_list == level_list[0]):
			sys.exit('Error: SubModel::InitComponentList(): Submodel components not all of same level')
		self.level = level_list[0]
		self.detector = detector_list[0]

	def AddComponent(self, component):
		self.component_list.append(component)

	def InitData(self):
		"""
		Hits, dists, and exposures are their own data members,
		but more detailed info is left within the submodel_dict member
		which has submodel_dict['data'] and submodel_dict['components'].
		DataTools draws much from submodel_dict['data'].
		"""
		self.InitExposure()
		self.InitRuntime()
		self.InitHits()

	def InitExposure(self):
		st = self.settings

		dt = self.data_tools
		# Point DataTools instance to this submodel
		dt.SetSubModel(self)
		# Gather data exposure
		# If a level 1 submodel, spec_detector is needed
		if self.level == 1:
			cpd = 'C' + str(self.detector[2]) + 'P' + str(self.detector[4]) + 'D' + str(self.detector[6])
			self.exposure, self.exposure_uncert = dt.GetExposure(spec_detector = cpd) # (kg*yr)
			self.exposure_nat, self.exposure_enr_uncert = dt.GetExposure(spec_detector = cpd, spec_detector_type = 0) # (kg*yr)
			self.exposure_enr, self.exposure_nat_uncert = dt.GetExposure(spec_detector = cpd, spec_detector_type = 2) # (kg*yr)
		else:
			self.exposure, self.exposure_uncert = dt.GetExposure() # (kg*yr)
			#self.exposure_nat, self.exposure_enr_uncert = dt.GetExposure(spec_detector_type = 0) # (kg*yr)
			#self.exposure_enr, self.exposure_nat_uncert = dt.GetExposure(spec_detector_type = 2) # (kg*yr)

		self.exposure_units = 'kg*yr'

	def InitRuntime(self):
		st = self.settings
		dt = self.data_tools
		self.config = self.submodel_dict['data']['config']

		self.runtime = dt.GetRuntime(self.config)
		
		self.runtime_units = 'sec'

	def InitToyMCExposure(self):
		st = self.settings

		#Get data exposure value
		data_exposure = self.exposure

		if st.toymc:
			tm = self.toymc_tools
			tm.SetSubModel(self)
			self.toymc_exposure, self.toymc_exposure_uncert = tm.GetExposure()
			self.toymc_exposure_nat, self.toymc_exposure_enr_uncert = None, None
			self.toymc_exposure_enr, self.toymc_exposure_nat_uncert = None, None

		self.toymc_exposure_units = 'kg*yr'

		#See how many toymc draws leads to an increase in exposure
		multiplier = self.toymc_exposure/self.exposure
		print('%s has %f times more exposure than MJD' % (self.name,multiplier))
		print('Data exposure is %f kg*yr' % self.exposure)
		print('ToyMC exposure is %f kg*yr' % self.toymc_exposure)
		print(' ')

	def InitHits(self):
		st = self.settings

		if st.toymc:
			tm = self.toymc_tools
			dt = self.data_tools

			#Get number of counts from data for comparison
			dt.SetSubModel(self)
			self.real_data_hits = dt.GetDataHitsL2()
			self.real_count_dist = np.histogram(a = self.real_data_hits, bins = st.dft.bins_n, range = st.dft.range, density = False)[0] # (counts)
			self.real_count_dist_integral = np.sum(self.real_count_dist)

			tm.SetSubModel(self)
			self.hits = tm.DrawSamples()
		else:
			dt = self.data_tools
			# Point DataTools instance to this submodel
			dt.SetSubModel(self)
			# Gather data hits
			# If a level 1 submodel, spec_detector is needed
			if self.level == 1:
				cpd = 'C' + str(self.detector[2]) + 'P' + str(self.detector[4]) + 'D' + str(self.detector[6])
				self.hits = dt.GetDataHits(spec_detector = cpd)
			else:
				self.hits = dt.GetDataHitsL2()

	def InitDists(self):
		"""
		Create distributions
		"""
		st = self.settings

		#set distribution for variable binning scheme
		if st.variable_bin_size:
			bin_edges = st.var_bin_edges[st.var_bin_edges.index(st.dft.min):] #trim bin edges of lowE
			bin_edges.append(int(st.dft.max)) #need to add rightmost bin edge of last bin due to how np.histogram works
			self.count_dist = np.histogram(a = self.hits, bins = bin_edges, range = st.dft.range, density = False)[0] # (counts)
		else:
			self.count_dist = np.histogram(a = self.hits, bins = st.dft.bins_n, range = st.dft.range, density = False)[0] # (counts)
		self.rate_dist = self.count_dist / self.exposure # (counts/kg/yr)
		self.fit_dist = self.count_dist
		self.CreateFitEngineDist()

	# def GetExpectedRateDistIntegral(self):
	# 	st = self.settings
	#
	# 	tm = self.toymc_tools
	# 	tm.SetSubModel(self)
	# 	self.exp_rate_dist_integral = tm.exp_rate_dist_integral

	def GetExpectedCountDistIntegral(self):
		st = self.settings

		tm = self.toymc_tools
		tm.SetSubModel(self)
		tm.GetExpectedRateDist()
		self.exp_count_dist_integral = tm.exp_count_dist_integral

	def CreateFitEngineDist(self):
		"""
		Crop the raw sim_dist to the default range. Then rebin to the default
		binning.
		"""
		st = self.settings

		if st.fit_peaks == True:
			self.fit_engine_dist = self.fit_dist[st.fit.peaks_i]
		else:
			self.fit_engine_dist = self.fit_dist[st.fit.min_dft_i:st.fit.max_dft_i]
		#if self.name == "SubModel_1_0_6_DS0_openblind_ThM1_best_std":
		#	print(self.fit_engine_dist)
		#	sys.exit()

	def AppendFitEngineDistsToDAGDF(self):
		st = self.settings

		dag_d = {}
		for component in self.component_list:
			dag_d[component.name] = {}
			dag_d[component.name]['fit_engine_dist'] = component.fit_engine_dist
		dag_df = pd.DataFrame.from_dict(dag_d)

		#print(self.name+'           '+str(len(self.component_list)))

		self.dag_df = self.dag_df.append(dag_df)

	def AppendPointEstimatesToDAGDF(self):
		st = self.settings
		#print("Inside function AppendPointEstimatesToDAGDF()")
		dag_d = {}
		for component in self.component_list:
			if component is component.floated:
				dag_d[component.name] = {}
				dag_d[component.name]['p_std'] = component.p_std
				dag_d[component.name]['p_mean'] = component.p_mean
				dag_d[component.name]['p_mode'] = component.p_mode
				dag_d[component.name]['p_median'] = component.p_median
		dag_df = pd.DataFrame.from_dict(dag_d)

		self.dag_df = self.dag_df.append(dag_df)

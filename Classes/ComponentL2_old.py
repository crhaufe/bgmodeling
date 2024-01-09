"""
Base class for a fit component.
"""

import numpy as np

import Management.Private_ConfigData_v7 as ConfigData
cfgd = ConfigData.ConfigData()
import Classes.Component as Component

detector_type_dict = {'0':'Nat','2':'Enr','02':'All','20':'All',None:'All'}

class ComponentL2(Component.Component):
	"""
	Base class for a fit component.
	"""

	#####################
	# Methods to be overridden by subclasses for specific component types
	#####################

	def InitUnits(self):
		"""
		The units corresponding to the post-processing level. Energy differential
		has been summed out by Rebin() in Component::CreateDefaultDist(), but
		can restore with differential = True in other methods.
		"""
		self.prior_units = 'Bq'
		self.sim_units = 'c/decay/kg'
		self.dft_units = 'c/decay/kg'
		self.exp_units = 'counts'
		self.fit_units = 'c/Bq'

	def InitPriorParams(self, loc = False, scale = False):
		"""
		The prior loc, scale, distribution type, and any other parameters.
		Also set any custom fixed values.
		"""
		st = self.settings
		hwC = self.component_dict['hardware_component']
		dC = self.component_dict['decay_chain']
		tuple = (dC, hwC)
		dCActStr = self.component_dict['decay_chain'] + 'Activity'
		if dCActStr=='PbBremActivity': dCActStr = 'PbActivity'

		#List of Potassium and Cobalt groups that need to use a special assay value since their upper limits in assay are too high
		KCo_dict_loc = {('Co','M1LMFEs_bulk'): 1.07E-10,\
				('Co','M2LMFEs_bulk'): 6.61E-11,\
				('K','M1Connectors_bulk'): 4.42E-03,\
				('K','M1CrossarmAndCPCables_bulk'): 1.05E-02,\
				('K','RadShieldCuOuter_bulk'): 8.82E-07,\
				('K','M1CryostatCopperFar_bulk'): 2.24E-03,\
				('K','M1CryostatCopperNear_bulk'): 7.65E-09,\
				('K','M1DUStringCopper_bulk'): 5.54E-10,\
				('K','M1LMFEs_bulk'): 4.61E-10,\
				('K','M1StringCables_bulk'): 2.41E-09,\
				('K','M2Connectors_bulk'): 2.19E-03,\
				('K','M2CrossarmAndCPCables_bulk'): 5.14E-03,\
				('K','M2CryostatCopperFar_bulk'): 1.47E-03,\
				('K','M2CryostatCopperNear_bulk'): 1.14E-08,\
				('K','M2DUStringCopper_bulk'): 1.44E-09,\
				('K','M2LMFEs_bulk'): 7.11E-06,\
				('K','M2Seals_bulk'): 4.90E-06,\
				('K','M2StringCables_bulk'): 4.99E-10,\
				('K','RadShieldCuInner_bulk'): 3.84E-08}

		KCo_dict_scale = {('Co','M1LMFEs_bulk'): 1.01E-10, ('Co','M2LMFEs_bulk'): 2.03E-10, ('K','M1Connectors_bulk'): 1.10E-03,\
                                ('K','M1CrossarmAndCPCables_bulk'): 1.87E-03, ('K','RadShieldCuOuter_bulk'): 4.42E-03,\
                                ('K','M1CryostatCopperFar_bulk'): 3.55E-04, ('K','M1CryostatCopperNear_bulk'): 2.92E-09,\
                                ('K','M1DUStringCopper_bulk'): 3.70E-10, ('K','M1LMFEs_bulk'): 1.87E-06,\
                                ('K','M1StringCables_bulk'): 1.98E-09, ('K','M2Connectors_bulk'): 2.65E-04,\
                                ('K','M2CrossarmAndCPCables_bulk'): 8.69E-04, ('K','M2CryostatCopperFar_bulk'): 5.31E-05,\
                                ('K','M2CryostatCopperNear_bulk'): 1.45E-08, ('K','M2DUStringCopper_bulk'): 1.53E-09,\
                                ('K','M2LMFEs_bulk'): 1.05E-06, ('K','M2Seals_bulk'): 2.84E-07,\
                                ('K','M2StringCables_bulk'): 5.4E-05, ('K','RadShieldCuInner_bulk'): 1.66E-08}

		if loc is True and hwC in st.high_prior_comp and self.component_dict['decay_chain'] in st.high_prior_dc: 
			self.prior_loc = cfgd.hardwareComponentDict[hwC][dCActStr][0] * st.high_prior_mult # (Bq) = (uBq/kg) * (Bq/uBq) * (kg) * (arbitrary scaling factor)
			#print('ORIGINAL PRIOR FOR %s IS: %f' % (hwC,cfgd.hardwareComponentDict[hwC][dCActStr][0]))
			#print('NEW PRIOR FOR %s IS: %f' % (hwC,self.prior_loc))
			#print('RATIO OF NEW OVER ORIGINAL IS: %f' % (self.prior_loc/cfgd.hardwareComponentDict[hwC][dCActStr][0]))
		elif loc is True and tuple in KCo_dict_loc.keys():
			#print('PROESSSING TUPLE: ' + str(tuple))
			self.prior_loc = KCo_dict_loc[tuple]
		elif loc is True and hwC == 'M2CPInterfaceCavityBottomSurface_bulk' and dCActStr=='ThActivity':
			self.prior_loc = 0.0001149 #Fitted activity in Bq from Anna's frequentist fits, a better prior to use.
		elif loc is True and hwC == 'M1CPInterfaceCavityBottomSurface_bulk' and dCActStr=='ThActivity' and 'M1CPInterfaceCavityBottomSurface_bulk' in st.toymc_targeted_vals_comp:
			self.prior_loc = 0.00057*0.25 #UL Activity in Bq from 2023 component assay, use only for simdataset studies (0.25 multiplicative factor for small prior test)
			print("SETTING CAVITY ACTIVITY TO 0.1425 mBq!")
		elif loc is True:
			self.prior_loc = cfgd.hardwareComponentDict[hwC][dCActStr][0] # (Bq) = (uBq/kg) * (Bq/uBq) * (kg)
			if hwC == 'M2CalSource_linesource': print("M2CALSOURCE PRIOR IS: " + str(self.prior_loc))

		else: pass
		if scale is True and st.prior_unc_uniform is True: 
			self.prior_scale = cfgd.hardwareComponentDict['bulk_M1CryostatCopperNear']['Th232Activity'][1] * st.prior_unc_mult # (Bq) = (uBq/kg) * (Bq/uBq) * (kg) * (arbitary scaling factor)
			#if 'bulk_RadShieldAssembly_001_RadShieldCuInner_001' in hwC: print('RadShieldCuInner self.prior_scale | dCActStr = %f | %s' % (self.prior_scale,dCActStr))
		if scale is True and st.prior_unc_uniform is False and hwC in st.high_prior_unc_comp and 'Th232Activity' in dCActStr: self.prior_scale = cfgd.hardwareComponentDict[hwC][dCActStr][1] * 10
		elif tuple in KCo_dict_scale.keys():
			self.prior_scale = KCo_dict_scale[tuple]
		elif scale is True: self.prior_scale = cfgd.hardwareComponentDict[hwC][dCActStr][1] * st.prior_unc_mult # (Bq) = (uBq/kg) * (Bq/uBq) * (kg) * (arbitary scaling factor)
		else: pass


	def CreateExpectedRateDist(self):
		"""
		"""
		#avg_activefrac = self.GetAveragePhysActiveFraction() # DONT divide out the active fraction to make the mass norm match the data, it is now unnecessary with new pdfs
		self.exp_rate_dist = self.dft_dist * self.prior_loc  # (c/sec) = (c/decay)*(decays/sec)

	def CreateExpectedDist(self):
		"""
		The expected background model distribution
		To be overridden in subclass specific to post-
		processing level.
		"""
		st = self.settings
		# hwC = self.component_dict['hardware_component']
		# dCActStr = self.component_dict['decay_chain'] + 'Activity'
		# exposure = self.submodel.exposure #NO LONGER NEED EXPOSURE with new pdfs
		# avg_activefrac = self.GetAveragePhysActiveFraction() # DONT divide out the active fraction to make the mass norm match the data, it is now unnecessary with new pdfs
		if st.toymc: runtime = self.submodel.runtime * st.toymc_mult
		else: runtime = self.submodel.runtime
		self.exp_dist = self.dft_dist * self.prior_loc * runtime  # (counts) = (c/decay)*(decays/sec)*runtime in seconds

	def CreateFitDist(self):
		"""
		The distribution in units for the fit.
		To be overridden in subclass specific to post-
		processing level.
		"""
		# hwC = self.component_dict['hardware_component']
		# dCActStr = self.component_dict['decay_chain'] + 'Activity'
		#
		# expected_prior_loc = cfgd.hardwareComponentDict[hwC][dCActStr][0]
		# if expected_prior_loc == 0: # avoid dividing by zero for exp_dists that are zero
		# 	pass
		# else:
		# 	self.fit_dist = self.exp_dist / expected_prior_loc # (c/Bq) = (counts) / (Bq)

		if self.prior_loc == 0: # avoid dividing by zero for exp_dists that are zero
			pass
		else:
			self.fit_dist = self.exp_dist / self.prior_loc # (c/Bq) = (counts) / (Bq)

	def GetPhysMasses(self):
		configuration = self.component_dict['config']
		detector_type = detector_type_dict[self.component_dict['detector_type']]
		activeDetectorList = cfgd.activeDetectorDict[configuration]
		massList = cfgd.detectorPhysMassList
		enrichedDetectorList = cfgd.enrichedDetectorList
		result_list = []
		for i, mass in enumerate(massList):
			if activeDetectorList[i] == 1:
				if detector_type == 'Nat' and enrichedDetectorList[i] == 0:
					result_list.append(mass)
				elif detector_type == 'Enr' and enrichedDetectorList[i] == 1:
					result_list.append(mass)
				elif detector_type == 'All':
					result_list.append(mass)
		return result_list

	def GetPhysActiveMasses(self):
		configuration = self.component_dict['config']
		detector_type = detector_type_dict[self.component_dict['detector_type']]
		activeDetectorList = cfgd.activeDetectorDict[configuration]
		massList = cfgd.detectorPhysActiveMassList
		enrichedDetectorList = cfgd.enrichedDetectorList
		result_list = []
		for i, mass in enumerate(massList):
			if activeDetectorList[i] == 1:
				if detector_type == 'Nat' and enrichedDetectorList[i] == 0:
					result_list.append(mass)
				elif detector_type == 'Enr' and enrichedDetectorList[i] == 1:
					result_list.append(mass)
				elif detector_type == 'All':
					result_list.append(mass)
		return result_list

	def GetPhysActiveFractions(self):
		configuration = self.component_dict['config']
		detector_type = detector_type_dict[self.component_dict['detector_type']]
		physactivemasses = self.GetPhysActiveMasses()
		physmasses = self.GetPhysMasses()
		physactivefractions = []
		for i in range(len(physactivemasses)):
			am = physactivemasses[i]
			m = physmasses[i]
			physactivefractions.append(am/m)
		return physactivefractions

	def GetAveragePhysActiveFraction(self):
		configuration = self.component_dict['config']
		detector_type = detector_type_dict[self.component_dict['detector_type']]
		physactivefractions = self.GetPhysActiveFractions()
		physmasses = self.GetPhysMasses()
		totalphysmass = np.sum(physmasses)
		avg = 0.
		for i in range(len(physmasses)):
			avg += physactivefractions[i] * physmasses[i]
		avg /= totalphysmass
		return avg

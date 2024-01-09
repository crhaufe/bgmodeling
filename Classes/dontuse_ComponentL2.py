"""
Base class for a fit component.
"""

import numpy as np

import Management.Private_ConfigData as ConfigData
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
		hwC = self.component_dict['hardware_component']
		dCActStr = self.component_dict['decay_chain'] + 'Activity'

		if 'Co60' or 'Co57' or 'Ge68' in self.component_dict['decay_chain']:
			if 'DS1' in self.component_dict['config']:
			if 'DS5' in self.component_dict['config']:
			else:
		else:
			if loc: self.prior_loc = cfgd.hardwareComponentDict[hwC][dCActStr][0] # (Bq) = (uBq/kg) * (Bq/uBq) * (kg)
			if scale: self.prior_scale = cfgd.hardwareComponentDict[hwC][dCActStr][1] # (Bq) = (uBq/kg) * (Bq/uBq) * (kg)

	def CreateExpectedRateDist(self):
		"""
		"""
		avg_activefrac = self.GetAveragePhysActiveFraction() # divide out the active fraction to make the mass norm match the data
		self.exp_rate_dist = self.dft_dist * self.prior_loc * cfgd.secs_per_year / avg_activefrac # (c/kg/yr) = (c/decay/kg)*(decays/sec)*(sec/yr)

	def CreateExpectedDist(self):
		"""
		The expected background model distribution
		To be overridden in subclass specific to post-
		processing level.
		"""
		# hwC = self.component_dict['hardware_component']
		# dCActStr = self.component_dict['decay_chain'] + 'Activity'
		exposure = self.submodel.exposure
		avg_activefrac = self.GetAveragePhysActiveFraction() # divide out the active fraction to make the mass norm match the data
		self.exp_dist = self.dft_dist * self.prior_loc * cfgd.secs_per_year * exposure / avg_activefrac  # (counts) = (c/decay/kg)*(decays/sec)*(sec/yr)*(kg*yr)

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

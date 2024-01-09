"""
Base class for a fit component.
"""

import numpy as np

import Management.Private_ConfigData as ConfigData
cfgd = ConfigData.ConfigData()
import Classes.Component as Component

detector_type_dict = {'0':'Nat','2':'Enr','02':'All','20':'All',None:'All'}

class ComponentL1(Component.Component):
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
		self.sim_units = 'c/decay'
		self.dft_units = 'c/decay'
		self.exp_units = 'counts'
		self.fit_units = 'c/Bq'

	def InitPriorParams(self, loc = False, scale = False):
		"""
		The prior loc, scale, distribution type, and any other parameters.
		Also set any custom fixed values.
		"""
		hwC = self.component_dict['hardware_component']
		dCActStr = self.component_dict['decay_chain'] + 'Activity'

		if loc: self.prior_loc = cfgd.hardwareComponentDict[hwC][dCActStr][0] # (Bq) = (uBq/kg) * (Bq/uBq) * (kg)
		if scale: self.prior_scale = cfgd.hardwareComponentDict[hwC][dCActStr][1] # (Bq) = (uBq/kg) * (Bq/uBq) * (kg)

	def CreateExpectedRateDist(self):
		"""
		"""
		mass = self.GetDetectorMass() # (kg) simulation modeled mass for this component's detector
		activefrac = self.GetPhysActiveFraction() # divide out the active fraction to make the mass norm match the data
		self.exp_rate_dist = self.dft_dist * self.prior_loc * cfgd.secs_per_year / mass / activefrac # (c/kg/yr) = (c/decay)*(decays/sec)*(sec/yr)*(1/kg)

	def CreateExpectedDist(self):
		"""
		The expected background model distribution
		To be overridden in subclass specific to post-
		processing level.
		"""
		mass = self.GetDetectorMass() # (kg) simulation modeled mass for this component's detector
		activefrac = self.GetPhysActiveFraction() # divide out the active fraction to make the mass norm match the data
		exposure = self.submodel.exposure
		self.exp_dist = self.dft_dist * self.prior_loc * cfgd.secs_per_year * exposure / mass / activefrac  # (counts) = (c/decay)*(decays/sec)*(sec/yr)*(kg*yr)*(1/kg)

	def CreateFitDist(self):
		"""
		The distribution in units for the fit.
		To be overridden in subclass specific to post-
		processing level.
		"""
		if self.prior_loc == 0: # avoid dividing by zero for exp_dists that are zero
			pass
		else:
			self.fit_dist = self.exp_dist / self.prior_loc # (c/Bq) = (counts) / (Bq)

	def GetDetectorList(self):
		"""
		Get list of all detector simulation names (Ge_C_P_D), regardless of config
		"""
		return cfgd.detectorList

	def GetDetectorMassList(self):
		"""
		Get list of all modeled masses, regardless of config
		"""
		return cfgd.detectorMassList

	def GetDetectorMass(self):
		"""
		Given a detector simulation name (Ge_C_P_D), return the mass (simulated, modeled mass)
		"""
		dStr = self.component_dict['detector']
		dIndex = self.GetDetectorList().index(dStr) # will raise exception if dStr not in list # dIndex = self.bscd.GetDetectorList().index(dStr)
		return self.GetDetectorMassList()[dIndex] # <--Modeled Mass

	def GetPhysActiveFractionList(self):
		"""
        Get list of all active fractions based on phys masses
        """
		physactivemasses = cfgd.detectorPhysActiveMassList
		physmasses = cfgd.detectorPhysMassList
		physactivefractions = []
		for i in range(len(physactivemasses)):
			am = physactivemasses[i]
			m = physmasses[i]
			physactivefractions.append(am/m)
		return physactivefractions

	def GetPhysActiveFraction(self):
		"""
		Given a detector simulation name (Ge_C_P_D), return the active fraction based on phys mass
		"""
		dStr = self.component_dict['detector']
		dIndex = self.GetDetectorList().index(dStr) # will raise exception if dStr not in list # dIndex = self.bscd.GetDetectorList().index(dStr)
		return self.GetPhysActiveFractionList()[dIndex]

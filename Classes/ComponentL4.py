"""
Base class for a fit component.
"""

import Classes.Component as Component

class ComponentL4(Component.Component):
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
		self.prior_units = 'obs/exp' # a ratio; floating relative integral of counts
		self.sim_units = 'c/kg/yr'
		self.dft_units = 'c/kg/yr'
		self.exp_units = 'counts'
		self.fit_units = 'counts'
		# If floating exposure:
		# self.prior_units = 'kg*yr' # exposure
		# self.fit_units = 'c/kg/yr'

	def InitPriorParams(self, loc = False, scale = False):
		"""
		The prior loc, scale, distribution type, and any other parameters.
		Also set any custom fixed values.
		"""
		if loc: self.prior_loc = 1. # floating relative counts
		if scale: self.prior_scale = .2 # floating relative counts
		# If floating exposure:
		# if loc: self.prior_loc = self.submodel.exposure
		# if scale: self.prior_scale = self.submodel.exposure_uncert

	def CreateExpectedRateDist(self):
		"""
		"""
		self.exp_rate_dist = self.dft_dist * self.prior_loc # (c/kg/yr)

	def CreateExpectedDist(self):
		"""
		The expected background model distribution
		To be overridden in subclass specific to post-
		processing level.
		"""
		exposure = self.submodel.exposure
		self.exp_dist = self.dft_dist * self.prior_loc * exposure # (counts) = (c/kg/yr) * (obs/exp) * (kg*yr)
		print('WARNING: Active mass fraction correction not implemented for ComponentL4 class')

	def CreateFitDist(self):
		"""
		The distribution in units for the fit.
		To be overridden in subclass specific to post-
		processing level.
		"""
		self.fit_dist = self.exp_dist / self.prior_loc # (counts) # (observed counts) = (expected counts) * (obs/exp)
		# If floating exposure:
		# self.fit_dist = self.dft_dist # (c/kg/yr)

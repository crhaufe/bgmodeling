"""
Tools for getting data and data info
"""

import sys
import os
import json
import numpy as np
import h5py

# SOME GLOBAL VARIABLES
bcs_output_dirname = os.environ['BCSOUTPUTDIR']
bds_output_dirname = os.environ['BDSOUTPUTDIR']
#channel_data_dirname = os.environ['CHANNELDATADIR']
days_per_year = 365.25
secs_per_day = 60 * 60 * 24
sim_data_cut_dict = {1:'RD',2:'RMD',3:'RMAD',6:'RmD'} #added cut 6}
detector_type_dict = {'0':'Nat','2':'Enr','02':'All',None:'All'}
openness_dict = {'open': 'open', 'blind': 'blind', 'openblind': 'open+blind', 'blindopen': 'open+blind'}

class DataTools:
    """
    Holds the data info for easy access without having to pass arguments around
    """
    def __init__(self, settings):
        self.settings = settings

    def SetSubModel(self, submodel):
        self.submodel = submodel
        self.name = submodel.name
        self.dataset = self.submodel.submodel_dict['data']['dataset']
        self.openness = self.submodel.submodel_dict['data']['openness']
        self.cut = self.submodel.submodel_dict['data']['cut']
        self.detector_type = self.submodel.submodel_dict['data']['detector_type']
        self.data_cut_scheme = self.submodel.submodel_dict['data']['data_cut_scheme']
        self.datatype = self.submodel.submodel_dict['data']['datatype']

    def GetChannelData(self, ds, openness):
        """
        Return dictionary of the channel data for this ds
        For each channel, the dict holds
        'CPD': {'good' 'detectorName' 'channel' 'detectorType' 'activeMass' 'liveTime' 'exposure' 'exposureUncert'}.
        """
        if openness == 'open':
            file_path = channel_data_dirname + '/%s_channel_data.json' % ds
        elif openness == 'blind':
            file_path = channel_data_dirname + '/%s_%s_channel_data.json' % (ds, openness)
        else:
            sys.exit('Error: GetChannelData(): openness not recognized')

        if(os.path.isfile(file_path)):
            with open(file_path) as channel_data_file:
                channel_data_dict = json.load(channel_data_file)
        else:
            sys.exit('Error: GetChannelData(): os.path.isfile returned false regarding %s' % fullPathToFile)

        return channel_data_dict

    # def GetFileHits(self, cpd, ds, openness):
    #     return bds_output_dirname + '/%s_%s_%s_%s.npy' % (cpd, ds, openness, sim_data_cut_dict[self.cut])

    def OpenHDF5(self, ds, openness):
        """
        Open an .hdf5 file to access the dictionary structure holding data arrays
        """
        st = self.settings

        if st.data_cal:
            dirname = bcs_output_dirname
            datatype = self.datatype
            basename = '%s_%s_%s.hdf5' % (ds, openness, datatype) #not separating by source
            file_path = dirname + '/' + basename
        else:
            dirname = bds_output_dirname
            basename = '%s_%s.hdf5' % (ds, openness)
            file_path = dirname + '/' + basename
        if(os.path.isfile(file_path)):
            return h5py.File(file_path, 'r')
        else:
            sys.exit('Error: OpenHDF5(): file_path DNE %s' % file_path)

    def GetHitsFromFile(self, ds, openness): #no longer cutting on cpd
        st = self.settings
        f = self.OpenHDF5(ds, openness)
        cut_str = self.data_cut_scheme
        datatype = self.datatype

        #DS0 special case:
        if ds=='DS0':
          cut_strs = ['RMD_M1Enr','RmD_M1Enr','RMD_M1Nat','RmD_M1Nat']
          spectra = []
          for cut_str in cut_strs:
            ds_name = ds + '_' + openness + '_' + cut_str
            spectra.append(f[cut_str][ds_name][()])
          #for x in range(len(cut_strs)):
            #print(type(spectra[x]))
            #print(spectra[x].shape)
          full_DS0_spectrum = np.array([])
          for x in range(len(cut_strs)):
            full_DS0_spectrum = np.append(full_DS0_spectrum, spectra[x])
          #print(full_DS0_spectrum.shape)
          return full_DS0_spectrum

        if st.data_cal: ds_name = ds + '_' + openness + '_' + datatype + '_' + cut_str
        else: ds_name = ds + '_' + openness + '_' + cut_str
        return f[cut_str][ds_name][()] #no longer cutting on cpd

    def GetRunTimeFromFile(self, ds, openness):
        """
        Get runtime from file for calibration data
        """
        f = self.OpenHDF5(ds, openness)
        return f['run_time_s']['run_time_s'][()]

    def GetTruthLists(self, kwargs, spec_dataset, spec_openness, spec_detector, spec_module, spec_detector_type):
        """
        Check cuts on which data is accepted
        The GetTruthLists spec_* args actually represent the current vars. They are fed in
        with spec_* names for easy comparison with the kwargs that represent a desired cut on the data
        """
        data_dict = self.submodel.submodel_dict['data']

        # Check that the current variables obey any spec_* kwargs
        kwargs_truth_list = [False] # Prep this as false. If kwargs == {}, still want np.all(kwargs_truth_list) to be false
        if kwargs != {}:
            # the following loop is a workaround for [eval(key) == kwargs[key] for key in kwargs] which has an in-class scope issue
            # https://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
            kwargs_truth_list = []
            for key in kwargs:
                kwargs_truth_list.append(eval(key) == kwargs[key])
        # Check that the current variables obey any restrictions specified by the submodel's data dictionary
        data_truth_list = []
        for key in ['module', 'detector', 'detector_type', 'dataset', 'openness']:
            if data_dict[key] != None:
                doAppend = False
                if key == 'module':
                    if eval('spec_%s' % key) == data_dict[key]: doAppend = True
                if key == 'detector':
                    if eval('spec_%s' % key) == data_dict[key]: doAppend = True
                if key == 'detector_type':
                    if str(eval('spec_%s' % key)) in data_dict[key]: doAppend = True
                if key == 'dataset':
                    if eval('spec_%s' % key)[2:] in data_dict[key]: doAppend = True
                if key == 'openness':
                    if eval('spec_%s' % key) in data_dict[key]: doAppend = True
                if doAppend:
                    data_truth_list.append(True)
        return data_truth_list, kwargs_truth_list

    def GetDataHits(self, **kwargs):
        """
        Returns numpy array of hits. Records the exposures for each channel.
        Use kwargs if you wish to get total_hits under specific conditions.
        kwargs can include any of:
            GetDataHits(spec_dataset = x, spec_openness = x, spec_detector = x, spec_module = x, spec_detector_type = x)
        """
        st = self.settings
        d = self.submodel.submodel_dict['data']['dataset_openness_dict']

        total_hits = np.array([])

        # All cpd, ds, openness
        for ds in d:
            for openness in d[ds]:
                channel_data_dict = self.GetChannelData(ds, openness)
                for cpd in channel_data_dict:
                    if channel_data_dict[cpd]['good'] and (str(channel_data_dict[cpd]['detectorType']) in self.detector_type):
                        data_truth_list, kwargs_truth_list = self.GetTruthLists(kwargs, spec_dataset = ds, spec_openness = openness, \
                            spec_detector = cpd, spec_module = cpd[1], spec_detector_type = channel_data_dict[cpd]['detectorType'])
                        if np.all(data_truth_list) and ( kwargs == {} or np.all(kwargs_truth_list) ):
                            d[ds][openness][cpd] = {}
                            d[ds][openness][cpd]['detector_type'] = channel_data_dict[cpd]['detectorType']
                            if st.data_cal:
                                run_time_dy = self.GetRunTimeFromFile(ds, openness) / secs_per_day
                                d[ds][openness][cpd]['exposure'] = run_time_dy * channel_data_dict[cpd]['activeMass']
                                d[ds][openness][cpd]['exposureUncert'] = d[ds][openness][cpd]['exposure'] * (channel_data_dict[cpd]['exposureUncert']/channel_data_dict[cpd]['exposure'])
                            else:
                                d[ds][openness][cpd]['exposure'] = channel_data_dict[cpd]['exposure'] # (kg*dy)
                                d[ds][openness][cpd]['exposureUncert'] = channel_data_dict[cpd]['exposureUncert'] # (kg*dy)
                            d[ds][openness][cpd][self.cut] = self.GetHitsFromFile(self.cut, cpd, ds, openness) # d[ds][openness][cpd][self.cut] = np.load(self.GetFileHits(cpd, ds, openness))
                            total_hits = np.append(total_hits, d[ds][openness][cpd][self.cut])

                            # tmp_hits = np.load(self.GetFileHits(cpd, ds, openness))
                            # total_hits = np.append(total_hits, tmp_hits)

        return total_hits

    def GetDataHitsL2(self):
        st = self.settings
        d = self.submodel.submodel_dict['data']['dataset_openness_dict']

        total_hits = np.array([])

        # All cpd, ds, openness
        for ds in d:
            for openness in d[ds]:
                d[ds][openness][self.cut] = self.GetHitsFromFile(ds, openness)
                total_hits = np.append(total_hits, d[ds][openness][self.cut])

        return total_hits
        

    def GetExposure(self, **kwargs):
        """
        Only include cpd exposures for datasets in which the cpds were active.
        Use kwargs if you wish to get total_hits under specific conditions.
        kwargs can include any of:
            GetDataHits(spec_dataset = x, spec_openness = x, spec_detector = x, spec_module = x, spec_detector_type = x)
        """
        st = self.settings
        d = self.submodel.submodel_dict['data']['dataset_openness_dict']

        dettypes = {'0':'Nat', '2':'Enr'}
        modules = {1:'M1', 2:'M2'}
        if 'DS0' not in d:
          dettype = dettypes[self.submodel.submodel_dict['data']['detector_type']]
          module = modules[self.submodel.submodel_dict['data']['module']]


        # Table of exposures (kg-y):
        ref_exp = {
        'DS0':{'open':{'Enr':{'M1':[1.12,0.02],'M2':[0.00,0.00]},'Nat':{'M1':[0.41,0.01],'M2':[0.00,0.00]}}},
        'DS1':{'open':{'Enr':{'M1':[1.81,0.03],'M2':[0.00,0.00]},'Nat':{'M1':[0.18,0.00],'M2':[0.00,0.00]}},'blind':{'Enr':{'M1':[0.45,0.01],'M2':[0.00,0.00]},'Nat':{'M1':[0.04,0.00],'M2':[0.00,0.00]}}},
        'DS2':{'open':{'Enr':{'M1':[0.27,0.00],'M2':[0.00,0.00]},'Nat':{'M1':[0.03,0.00],'M2':[0.00,0.00]}},'blind':{'Enr':{'M1':[0.85,0.01],'M2':[0.00,0.00]},'Nat':{'M1':[0.09,0.00],'M2':[0.00,0.00]}}},
        'DS3':{'open':{'Enr':{'M1':[0.97,0.01],'M2':[0.00,0.00]},'Nat':{'M1':[0.22,0.01],'M2':[0.00,0.00]}}},
        'DS4':{'open':{'Enr':{'M1':[0.00,0.00],'M2':[0.26,0.00]},'Nat':{'M1':[0.00,0.00],'M2':[0.26,0.01]}}},
        'DS5b':{'open':{'Enr':{'M1':[1.32,0.02],'M2':[0.45,0.01]},'Nat':{'M1':[0.37,0.01],'M2':[0.55,0.01]}}},
        'DS5c':{'open':{'Enr':{'M1':[0.40,0.01],'M2':[0.14,0.00]},'Nat':{'M1':[0.11,0.00],'M2':[0.17,0.00]}},'blind':{'Enr':{'M1':[1.21,0.02],'M2':[0.42,0.01]},'Nat':{'M1':[0.34,0.01],'M2':[0.50,0.00]}}},
        'DS6':{'open':{'Enr':{'M1':[8.17,0.12],'M2':[3.50,0.05]},'Nat':{'M1':[2.21,0.05],'M2':[3.32,0.08]}},'blind':{'Enr':{'M1':[18.29,0.27],'M2':[7.84,0.11]},'Nat':{'M1':[4.86,0.11],'M2':[7.31,0.17]}}},
        'DS7':{'open':{'Enr':{'M1':[1.53,0.02],'M2':[0.00,0.00]},'Nat':{'M1':[0.49,0.01],'M2':[0.00,0.00]}},'blind':{'Enr':{'M1':[2.95,0.04],'M2':[0.00,0.00]},'Nat':{'M1':[0.95,0.02],'M2':[0.00,0.00]}}}
    }

        # All cpd, ds, openness
        exposure = 0. # (kg*dy)
        exposure_uncert = 0. # (kg*dy)
        for ds in d:
            if ds=="DS0":
              for type in dettypes.values():
                for mod in modules.values():
                  exposure += ref_exp[ds]['open'][type][mod][0]
                  exposure_uncert += ref_exp[ds]['open'][type][mod][1]
              break
            for openness in d[ds]:
                #channel_data_dict = self.GetChannelData(ds, openness)
                #for cpd in channel_data_dict: # for cpd in d[ds][openness]:
                #    if channel_data_dict[cpd]['good'] and (str(channel_data_dict[cpd]['detectorType']) in self.detector_type):
                #        data_truth_list, kwargs_truth_list = self.GetTruthLists(kwargs, spec_dataset = ds, spec_openness = openness, \
                #            spec_detector = cpd, spec_module = cpd[1], spec_detector_type = channel_data_dict[cpd]['detectorType'])
                #        if np.all(data_truth_list) and ( kwargs == {} or np.all(kwargs_truth_list) ):
                #            # exposure += d[ds][openness][cpd]['exposure'] # (kg*dy)
                #            # uncert = np.append(uncert, d[ds][openness][cpd]['exposureUncert']) # (kg*dy)
                #            if st.data_cal:
                #                run_time_dy = self.GetRunTimeFromFile(ds, openness) / secs_per_day
                #                exposure += run_time_dy * channel_data_dict[cpd]['activeMass']
                #                tmp_uncert = run_time_dy * channel_data_dict[cpd]['activeMass'] * (channel_data_dict[cpd]['exposureUncert']/channel_data_dict[cpd]['exposure'])
                #                uncert = np.append(uncert, tmp_uncert) # (kg*dy)
                #            else:
                #                exposure += channel_data_dict[cpd]['exposure'] # (kg*dy)
                #                tmp_uncert = channel_data_dict[cpd]['exposureUncert'] # (kg*dy)
                #                uncert = np.append(uncert, tmp_uncert) # (kg*dy)
                exposure += ref_exp[ds][openness][dettype][module][0]
                exposure_uncert += ref_exp[ds][openness][dettype][module][1]

        if exposure == 0.:
            print('Warning: GetExposure(): Received item with 0 exposure. Due to spec_detector_type?')

        #exposure_uncert = np.sqrt( np.sum( uncert**2 ) ) # (kg*dy)
        #exposure = exposure * 1/days_per_year # (kg*dy)*(yr/dy) = (kg*yr)
        #exposure_uncert = exposure_uncert * 1/days_per_year # (kg*dy)*(yr/dy) = (kg*yr)

        #print(exposure)
        #print(exposure_uncert)

        return exposure, exposure_uncert

    def GetRuntime(self, ds):
        st = self.settings
        runtime = 0.0

        #RnThCalibration data
        if ds=="DS6cal": runtime = 613674.7125721999 #sec

        #Background data
        if ds=="DS0": runtime = 3967362.6689589205 #sec
        if ds=="DS1-2": runtime = 10380247.05385147 #sec 
        if ds=="DS3-6": runtime = 83613604.04905578 #sec    
        if ds=="DS7": runtime = 15211023.12686105 #sec

        return runtime

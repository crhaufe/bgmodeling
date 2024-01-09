"""
"""

import sys
import os
import json

from helper_w_module import *

#############################
# Setup the sets of floated and fixed distributions
#############################

l2_full_set = GetFullL2DCHWTupleSet('DS3-6')
floating_comp = GetFloatingComp()
l2_floated_set = l2_full_set
l2_fixed_set = []
#for item in l2_full_set:
#  if item == floating_comp:
#    l2_floated_set.append(item)
#  else:
#    l2_fixed_set.append(item)
print('    l2_floated_set', len(l2_floated_set))
#for x in l2_floated_set:
  #print(x)
print('    l2_fixed_set', len(l2_fixed_set))
#for x in l2_fixed_set:
  #print(x)

#############################
# Setup the dict to later be turned into JSON
#############################

comment = 'Float l2 ' + floating_comp[0] + '_' + floating_comp[1]
model_description_dict = {
    'name': os.path.basename(sys.argv[0]).strip('Write_').strip('.py'), # argv[0] is the name of this .py file
    'comments': comment,
    'components': {}
}

#############################
# Floated Components
#############################

# FLOATED LEVEL 2 COMPONENTS
for (dC, hwC) in l2_floated_set:
    generator = hwC.split('_')[1]
    component_dict = {
     'level': 2,
     'module': 1, # invokes spec_m
     'detector': None, # invokes spec_cpd
     'config': 'DS3-6',
     'cut': 2, # implies data cut
     'data_cut_scheme': 'RMD_M1Nat', # needed for correct data file
     'detector_type': '0', # invokes spec_detector_type
     'decay_chain_segment': None,
     'decay_chain': dC,
     'hardware_component': hwC,
     'generator': generator,
     'dataset': 'DS345b5c6', # spec_ds is an option elsewhere
     'datatype': 'ThM1',
     'pdftype': 'best_std',
     'id': None,
     'openness': 'openblind', # spec_openness is an option elsewhere # options are 'open', 'blind', None='openblind'='blindopen'
     'floated': 1,
    }
    component_dict['submodel_name'] = GetSubModelName(component_dict)
    component_dict['sim_file_path'] = GetSimFilePath(component_dict)
    component_name = GetComponentName(component_dict)
    model_description_dict['components'][component_name] = component_dict

#############################
# Fixed Components
#############################

# FIXED LEVEL 2 COMPONENTS
for (dC, hwC) in l2_fixed_set:
    generator = hwC.split('_')[1]
    component_dict = {
     'level': 2,
     'module': 1, # invokes spec_m
     'detector': None, # invokes spec_cpd
     'config': 'DS3-6',
     'cut': 2, # implies data cut
     'data_cut_scheme': 'RMD_M1Nat', # needed for correct data file
     'detector_type': '0', # invokes spec_detector_type
     'decay_chain_segment': None,
     'decay_chain': dC,
     'hardware_component': hwC,
     'generator': generator,
     'dataset': 'DS345b5c6', # spec_ds is an option elsewhere
     'datatype': 'ThM1',
     'pdftype': 'best_std',
     'id': None,
     'openness': 'openblind', # spec_openness is an option elsewhere # options are 'open', 'blind', None='openblind'='blindopen'
     'floated': 0,
    }
    component_dict['submodel_name'] = GetSubModelName(component_dict)
    component_dict['sim_file_path'] = GetSimFilePath(component_dict)
    component_name = GetComponentName(component_dict)
    model_description_dict['components'][component_name] = component_dict

#############################
# Load model_description_dict into JSON and save to file
#############################
outfile_dirname = os.path.dirname(sys.argv[0]) if os.path.dirname(sys.argv[0]) else '.'
outfile_basename = model_description_dict['name'] + '.json'
outfile_path = outfile_dirname + '/' + outfile_basename
with open(outfile_path, 'w') as file:
    json.dump(model_description_dict, file)

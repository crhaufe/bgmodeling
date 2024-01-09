"""
Preprocessing script that links all the component dictionaries from model description JSON files.
Then compiles a set of unique submodel names as the set of submodels/likelihood terms.
Then creates the Model.json file representing the total model, organized by submodel.
"""

import sys
import os
import glob
import json
import subprocess

def GetDatasetOpennessDict(st, dataset, openness):
    ref_d = {
        'DS0':{'open':{}},
        'DS1':{'open':{},'blind':{}},
        'DS2':{'open':{},'blind':{}},
        'DS3':{'open':{}},
        'DS4':{'open':{}},
        #'DS5a':{'open':{}}, (no fitting to 5a, noisy) 
        'DS5b':{'open':{}},
        'DS5c':{'open':{},'blind':{}},
        'DS6':{'open':{},'blind':{}},
        'DS7':{'open':{},'blind':{}}
    }
    if st.data_cal:
        ref_d = {
            'DS0':{'open':{}},
            'DS1':{'open':{}},
            'DS2':{'open':{}},
            'DS3':{'open':{}},
            'DS4':{'open':{}},
            #'DS5a':{'open':{}},
            'DS5b':{'open':{}},
            'DS5c':{'open':{}},
            'DS6':{'open':{}},
            'DS7':{'open':{}}
        }
    d = {}
    for ds in ref_d:
        if ds[2:] in dataset:
            if openness in ['open', 'blind'] and openness in ref_d[ds]:
                d.update({ds: {openness: {}}})
            if openness == None or ('open' in openness and 'blind' in openness):
                d.update({ds: ref_d[ds]})
    return d

def main(st):
    """
    """
    model_dirname = st.model_dirname

    ##########################################
    # Create and get list of Model_*.json files
    ##########################################

    # Create Model_*.json files
    glob_str = model_dirname + '/' + 'Write_Model_*.py'
    glob_list = glob.glob(glob_str)
    print('Found user-created model component description scripts:')
    [print('    %s' % os.path.basename(file)) for file in glob_list]
    [subprocess.run(['python', script_str]) for script_str in glob_list]

    # Get list of created Model_*.json files
    glob_str = model_dirname + '/Model_*.json'
    glob_list = glob.glob(glob_str)
    #for x in glob_list:
    #  print(x)
    

    ##########################################
    # Gather Model_*.json files and create Model.json
    ##########################################

    # Gather components together, organized by submodel
    print('Gathering components:')
    model_dict = {}
    # Loop Model_*.json files
    print(glob_list)
    for file_path in glob_list:
        with open(file_path) as file:
            d_json = json.load(file)
            # Loop components
            for component_name in d_json['components']:
                submodel_name = d_json['components'][component_name]['submodel_name']
                print('    %s %s' % (component_name, submodel_name))
                # If first pass on a submodel, add to set of submodel names and fill out the submodel's data
                if submodel_name not in model_dict:
                    model_dict[submodel_name] = {'components': {}}
                    if 'data' not in model_dict[submodel_name]:
                        model_dict[submodel_name]['data'] = {}
                        for key in ['module', 'config', 'detector', 'detector_type', 'cut', 'data_cut_scheme', 'dataset', 'openness', 'datatype', 'pdftype', 'id']:
                            if key not in model_dict[submodel_name]['data']:
                                model_dict[submodel_name]['data'][key] = d_json['components'][component_name][key]
                        if 'dataset_openness_dict' not in model_dict[submodel_name]['data']:
                            dataset = model_dict[submodel_name]['data']['dataset']
                            openness = model_dict[submodel_name]['data']['openness']
                            tmp_dict = { 'dataset_openness_dict': GetDatasetOpennessDict(st, dataset, openness) }
                            model_dict[submodel_name]['data'].update(tmp_dict)
                # Collect the components underneath of their respective submodel
                if submodel_name in model_dict:
                    model_dict[submodel_name]['components'][component_name] = d_json['components'][component_name]

    # Create Model.json
    outfile_path = model_dirname + '/' + 'Model.json'
    with open(outfile_path, 'w') as file:
        json.dump(model_dict, file)
    print('Created %s' % outfile_path)

    #sys.exit()

    return model_dict

##########################################
# main function
##########################################

if __name__ == "__main__":
    """
    Takes the Write_Model*.py scripts in a user-created model directory
    and prepares a Model.json file for FitSpectra.py

    usage:
    $ python Preprocessor.py <model dirname>
    """

    if os.path.isdir(sys.argv[1]):
        if sys.argv[1][-1] == '/': sys.argv[1] = sys.argv[1][:-1]
        model_dirname = sys.argv[1]
    else:
        sys.exit('Error: os.path.isdir(sys.argv[1]) == False')

    main(model_dirname)

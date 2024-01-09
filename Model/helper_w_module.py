"""
"""

import sys
import os
import json

import Private_ConfigData_v7 as ConfigData
cfgd = ConfigData.ConfigData()

# SOME GLOBAL VARIABLES
bss_output_dirname = os.environ['BSSOUTPUTDIR']
sim_data_cut_dict = {1:'RD',2:'RMD',3:'RMAD',4:'RAD',6:'RmD'}
grab_pdf_cut_dict = {2:'Gran',6:'Antigran',None:'None'}
detector_type_dict = {'0':'Nat','2':'Enr','02':'All','20':'All',None:'All'}
openness_dict = {'open':'open','blind':'blind','openblind':'open+blind','blindopen':'open+blind',None:'open+blind'}
module_dict = {1:'M1',2:'M2'}

def GetComponentName(d):
    """
    Component_<decay_chain>_<hardware_component>_<module>_<detector_type>_<cut>_<config>_<pdftype>_<id>
    """
    component_name = 'Component'
    for key in ['decay_chain', 'hardware_component', 'module', 'detector_type', 'cut', 'config', 'pdftype','id']:
        if d[key] != None:
            tmp = d[key]
            component_name += '_%s' % str(tmp)
    return component_name

def GetSubModelName(d):
    """
    SubModel_<module>_<detector_type>_<cut>_<config>_<openness>_<datatype>_<pdftype>_<id>
    """
    submodel_name = 'SubModel'
    for key in ['module', 'detector_type', 'cut', 'config', 'openness', 'datatype', 'pdftype', 'id']:
        if d[key] != None:
            submodel_name += '_%s' % str(d[key])
    return submodel_name

def GetSimFilePath(d):
    level = d['level']
    config = d['config']
    cut = grab_pdf_cut_dict[d['cut']]
    dC = d['decay_chain']
    hwC = d['hardware_component']
    module = module_dict[d['module']]
    id = d['id']
    pdftype = d['pdftype']
    detector_type = detector_type_dict[d['detector_type']]

    dirname = bss_output_dirname
    ThRn_groups = ['peakshape','dl_shape','dl_fccd','dl_all','energylin']
    if pdftype in ThRn_groups: dirname += '/pdfs_ThRn/' + pdftype + '/'
    elif config == 'DS0': dirname += '/pdfs_DS0/combined_pdfs/'
    else: dirname += '/pdfs/'

    #Deal with N2 groups:
    if hwC in ['N2DS0_bulk', 'N2DS127_bulk']:
        hwC = 'N2_bulk'
    if hwC in ['N2DS0_surf', 'N2DS127_surf']:
        hwC = 'N2_surf'
    if config == 'DS0':
        basename = '%s_All_%s_%s_%s' % (config, dC, hwC, pdftype)
    elif d['level'] == 2:
        basename = '%s_All_%s_%s_%s_%s_%s_%s' % (config, dC, hwC, cut, pdftype, module, detector_type)
    else:
        sys.exit('Write_Model_*.py::GetSimulationFile(): no known sim file path')
    if 'None' in basename:
        sys.exit('Write_Model_*.py::GetSimulationFile(): \'None\' in basename')
    basename += '.npy'

    simfilepath = dirname + basename
   
    #Check if path exists
    if os.path.exists(simfilepath) is False:
        print('THIS PATH DOES NOT EXIST: ' + simfilepath)
        sys.exit('Write_Model_*.py::GetSimulationFile(): sim file path does not exist!')

    return simfilepath

def GetDecayChainList():
    return [
        'Th',\
        'U',\
        '228Th',\
        'Rn',\
        'Pb',\
        'PbBrem',\
        'Co',\
        '57Co',\
        '68Ge',\
        'K',\
        '0v',\
        '2v',\
        '54Mn',\
        'DCR'
        ] #originally 232Th, 238U, 222Rn, 210Pb, 60Co, 40K

def GetHardwareComponentList(config):
    hardware_component_list = [\
        'M1NatGe_bulk',\
        'M2NatGe_bulk',\
        'M1EnrGe_bulk',\
        'M2EnrGe_bulk',\
        'M1Bellows_bulk',\
        'M2Bellows_bulk',\
        'M1DUStringCopper_bulk',\
        'M2DUStringCopper_bulk',\
        'M1CryostatCopperFar_bulk',\
        'M2CryostatCopperFar_bulk',\
        'M1CryostatCopperNear_bulk',\
        'M2CryostatCopperNear_bulk',\
        'M1CryostatCopperNearWeldedParts_bulk',\
        'M2CryostatCopperNearWeldedParts_bulk',\
        'RadShieldCuInner_bulk',\
        'RadShieldCuOuter_bulk',\
        'M1LMFEs_bulk',\
        'M2LMFEs_bulk',\
        'M1Connectors_bulk',\
        'M2Connectors_bulk',\
        'M1StringCables_bulk',\
        'M1CrossarmAndCPCables_bulk',\
        'M2StringCables_bulk',\
        'M2CrossarmAndCPCables_bulk',\
        'M1ThermosyphonAndShieldVespel_bulk',\
        'M2ThermosyphonAndShieldVespel_bulk',\
        'M1DUPTFE_bulk',\
        'M2DUPTFE_bulk',\
        'M1Seals_bulk',\
        'M2Seals_bulk',\
        'N2_bulk',\
        'N2_surf',\
        'RadShieldAssembly_001_RadShieldPb_bulk',\
        'RadShieldAssembly_001_RadShieldPb_001_bulk',\
        'M1DUPTFE_surf',\
        'M2DUPTFE_surf',\
        'M1CPInterfaceCavityBottomSurface_bulk',\
        'M2CPInterfaceCavityBottomSurface_bulk',\
        #'M1CalSource_linesource',\
        #'M2CalSource_linesource',\
        ]
    if config == 'DS0':
        hardware_component_list.remove('RadShieldCuInner_bulk')
    if config in ['DS0','DS1-2','DS7']:
        m2_list = ['M2CrossarmAndCPCables_bulk',\
        'M2StringCables_bulk',\
        'M2NatGe_bulk',\
        'M2EnrGe_bulk',\
        'M2Bellows_bulk',\
        'M2CryostatCopperFar_bulk',\
        'M2CryostatCopperNear_bulk',\
        'M2CryostatCopperNearWeldedParts_bulk',\
        'M2LMFEs_bulk',\
        'M2Connectors_bulk',\
        'M2ThermosyphonAndShieldVespel_bulk',\
        'M2DUPTFE_bulk',\
        'M2DUPTFE_surf',\
        'M2Seals_bulk',\
        'M2DUStringCopper_bulk',\
        'M2CPInterfaceCavityBottomSurface_bulk'
        ]
        #n2_list = ['N2_bulk','N2_surf']
        for hwC in m2_list: hardware_component_list.remove(hwC)
        #for hwC in n2_list: hardware_component_list.remove(hwC)

    if config == 'DS0':
        hardware_component_list.remove('N2_bulk')
        hardware_component_list.remove('N2_surf')
        hardware_component_list.append('N2DS0_bulk')
        hardware_component_list.append('N2DS0_surf')
        
    if config in ['DS1-2','DS7']:
        hardware_component_list.remove('N2_bulk')
        hardware_component_list.remove('N2_surf')
        hardware_component_list.append('N2DS127_bulk')
        hardware_component_list.append('N2DS127_surf')          
         
    # leave the M2 components in DS3 and M1 components in DS4
    return hardware_component_list

def GetFullL2DCHWTupleSet(config):
    l2_full_set = set()
    l2_set_to_remove = set()
    hardware_component_list = GetHardwareComponentList(config)
    decay_chain_list = GetDecayChainList().copy()
    #always remove
    decay_chain_list.remove('0v')
    decay_chain_list.remove('DCR')
    #remove for cal fits
    #decay_chain_list.remove('U')
    #decay_chain_list.remove('K')
    #decay_chain_list.remove('Co')
    #decay_chain_list.remove('Pb')
    #decay_chain_list.remove('57Co')
    #decay_chain_list.remove('68Ge')
    #decay_chain_list.remove('2v')
    #decay_chain_list.remove('54Mn')

    #PDFs we'll never want to include
    l2_set_to_remove.add(('Co','M1CryostatCopperNear_bulk'))
    l2_set_to_remove.add(('Co','M2CryostatCopperNear_bulk'))
    l2_set_to_remove.add(('Th','M1CryostatCopperNearWeldedParts_bulk'))
    l2_set_to_remove.add(('Th','M2CryostatCopperNearWeldedParts_bulk'))
    l2_set_to_remove.add(('U','M1CryostatCopperNearWeldedParts_bulk'))
    l2_set_to_remove.add(('U','M2CryostatCopperNearWeldedParts_bulk'))
    l2_set_to_remove.add(('K','M1CryostatCopperNearWeldedParts_bulk'))
    l2_set_to_remove.add(('K','M2CryostatCopperNearWeldedParts_bulk'))

    ##There are some PDFs we don't want to include at the moment that would otherwise be included (maybe?)
    l2_set_to_remove.add(('K','M1Bellows_bulk'))
    l2_set_to_remove.add(('K','M2Bellows_bulk'))
    l2_set_to_remove.add(('57Co','M1EnrGe_bulk'))
    l2_set_to_remove.add(('57Co','M2EnrGe_bulk'))
    l2_set_to_remove.add(('U','M1EnrGe_bulk'))
    l2_set_to_remove.add(('U','M2EnrGe_bulk'))
    l2_set_to_remove.add(('Th','M1EnrGe_bulk'))
    l2_set_to_remove.add(('Th','M2EnrGe_bulk'))
    l2_set_to_remove.add(('Pb','RadShieldAssembly_001_RadShieldPb_001_bulk'))

    for hwC in hardware_component_list:
        for dC in decay_chain_list:
            tmp_tuple = (dC, hwC)
            if dC=='PbBrem' and hwC=='RadShieldAssembly_001_RadShieldPb_001_bulk':
              dCActStr = 'PbActivity'
            elif dC=='PbBrem': continue #PbBrem only needed for hwc above
            else:
              dCActStr = dC + 'Activity'
            if cfgd.hardwareComponentDict[hwC][dCActStr][0] > 0 and tmp_tuple not in l2_set_to_remove:
                l2_full_set.add(tmp_tuple)
                #print(tmp_tuple)
    return l2_full_set

def GetFloatingComp():
    floating_comp = ('Th', 'M1CPInterfaceCavityBottomSurface_bulk')
    return floating_comp

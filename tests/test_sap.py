import pytest
from janus import sap, psi4_wrapper, openmm_wrapper, initializer
from copy import deepcopy
import numpy as np
import os

water = os.path.join(str('tests/files/test_openmm/water.pdb'))


param = {"system" : {"mm_pdb_file": water},
         "qmmm" : {"embedding_scheme" : "Electrostatic"}}

config = initializer.Initializer(param, as_file=False)
psi4 = psi4_wrapper.Psi4_wrapper(config.qm_param)
openmm = openmm_wrapper.OpenMM_wrapper(config.mm_param)

sap_1 = sap.SAP(config.aqmmm_param, psi4, openmm)
sap_2 = sap.SAP(config.aqmmm_param, psi4, openmm)

sap_1.set_Rmin(0.26)
sap_1.set_Rmax(0.32)
sap_2.set_Rmin(0.26)
sap_2.set_Rmax(0.34)

def test_get_combos():

    buffers = [0,1,2,3,4]
    buffers2 = [0,1]
    buffer_distance = {0:1.2, 1:0.4, 2:0.8, 3:1.5, 4:0.2}
    buffer_distance2 = {0:3, 1:1}

    combo1 = sap_1.get_combos(buffers, buffer_distance)
    order1 = np.array(deepcopy(sap_1.sap_order))
    combo2 = sap_1.get_combos(buffers2, buffer_distance2)
    order2 = np.array(deepcopy(sap_1.sap_order))

    assert(len(combo1)) == len(buffers)
    assert(len(combo2)) == len(buffers2)
    assert np.allclose(order1, np.array([4,1,2,0,3]))
    assert np.allclose(order2, np.array([1,0]))


def test_partition():

    sap_1.partition([0])
    sap_2.partition([0])

    assert len(sap_1.systems[0]) == 2
    assert len(sap_2.systems[0]) == 3

def test_get_switching_functions():
    # need more here

    sap_1.get_switching_functions()
    sap_2.get_switching_functions()
    
    assert np.allclose(sap_1.buffer_groups[1].phi_i, 3.5669066455610295e-05)
    assert np.allclose(sap_2.buffer_groups[1].phi_i, 0.019398444948607135)
    assert np.allclose(sap_2.buffer_groups[2].phi_i, 9.163106551223009e-08)

def test_compute_sf_gradients():

    f1 =  sap_1.compute_sf_gradient()
    f2 = sap_2.compute_sf_gradient()

    force1 =  {0: np.array([ 0.0064088 ,  1.80584451,  2.0500046 ]), 
                3: np.array([-0.00569161, -1.60375833, -1.82059526]), 
                4: np.array([-0.00035859, -0.10104309, -0.11470467]), 
                5: np.array([-0.00035859, -0.10104309, -0.11470467])}
    force2 = {0: np.array([  0.14451921,  42.96266838,  48.45262028]), 
                3: np.array([ -0.13545501, -38.16793622, -43.32845066]), 
                4: np.array([-0.0085342 , -2.40473028, -2.72986301]), 
                5: np.array([-0.0085342 , -2.40473028, -2.72986301]), 
                6: np.array([ 0.00710847,  0.01308019,  0.29800537]), 
                7: np.array([ 0.00044786,  0.0008241 ,  0.01877551]), 
                8: np.array([ 0.00044786,  0.0008241 ,  0.01877551])}

    for i, f in f1.items():
        assert np.allclose(f, force1[i])
    for i, f in f2.items():
        assert np.allclose(f, force2[i])

def test_run_aqmmm():
    pass

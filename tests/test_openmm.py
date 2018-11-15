"""
Testing for the openmm_wrapper module
"""
import pytest
from janus import mm_wrapper 
from janus import initializer
import simtk.unit as OM_unit
import numpy as np
import os

#ala_water_pdb_file = os.path.join(str('tests/files/test_openmm/ala_water.pdb'))
water_pdb_file = os.path.join(str('tests/files/test_openmm/water.pdb'))
ala_pdb_file = os.path.join(str('tests/files/test_openmm/ala_ala_ala.pdb'))

config_water = {"system" : {"mm_pdb_file" : water_pdb_file}}
config_ala = {"system" : {"mm_pdb_file" : ala_pdb_file}}
          #"embedding_method" : "Electrostatic"}

config1 = initializer.Initializer(config_water, as_file=False)
config2 = initializer.Initializer(config_ala, as_file=False)

wrapper = mm_wrapper.OpenMMWrapper(config1.ll_param)
wrapper_ala = mm_wrapper.OpenMMWrapper(config2.ll_param)
#openmm_mech = openmm_wrapper.OpenMM_wrapper(sys_mech)
#openmm_elec = openmm_wrapper.OpenMM_wrapper(sys_elec)
#openmm_ala_link = openmm_wrapper.OpenMM_wrapper(sys_ala_link)
#openmm_ala_link_2 = openmm_wrapper.OpenMM_wrapper(sys_ala_link)


def test_create_new_residue_template():

    mod = wrapper_ala.create_modeller(keep_qm=False, qm_atoms=[0,1,2,3])
    wrapper_ala.create_new_residue_template(mod.topology)

    assert wrapper_ala.forcefield._templates['Modified_ALA'].name == 'Modified_ALA' 

def test_set_charge_zero():

    sys1 = wrapper.create_openmm_system(wrapper.pdb.topology)
    sys2 = wrapper.create_openmm_system(wrapper.pdb.topology)

    wrapper.set_charge_zero(sys1)
    wrapper.set_charge_zero(sys2, link_atoms = [0])

    assert sys1.getForce(3).getParticleParameters(0)[0]/OM_unit.elementary_charge == 0.0
    assert sys1.getForce(3).getParticleParameters(1)[0]/OM_unit.elementary_charge == 0.0
    assert sys2.getForce(3).getParticleParameters(0)[0]/OM_unit.elementary_charge == 0.0
    assert sys2.getForce(3).getParticleParameters(1)[0]/OM_unit.elementary_charge == 0.417

def test_set_LJ_zero():

    sys = wrapper.create_openmm_system(wrapper.pdb.topology)

    wrapper.set_LJ_zero(sys)

    assert sys.getForce(3).getParticleParameters(0)[0]/OM_unit.elementary_charge == -0.834
    assert sys.getForce(3).getParticleParameters(0)[1]/OM_unit.nanometer == 0.0
    assert sys.getForce(3).getParticleParameters(0)[2]/OM_unit.kilojoule_per_mole == 0.0

def test_create_openmm_system():
    sys_1 = wrapper.create_openmm_system(wrapper.pdb.topology)
    sys_2 = wrapper.create_openmm_system(wrapper.pdb.topology, include_coulomb='all', initialize=True)
    sys_3 = wrapper.create_openmm_system(wrapper.pdb.topology, include_coulomb='only')

    assert sys_1.getNumForces() == 5
    assert sys_2.getNumForces() == 6
    assert sys_3.getNumForces() == 2

def test_compute_info():
    state1 = wrapper.compute_info(wrapper.pdb.topology, wrapper.pdb.positions, minimize=True)
    state2 = wrapper.compute_info(wrapper.pdb.topology, wrapper.pdb.positions)

    assert state1['kinetic'] + state1['potential'] == -0.027789330729325913
    assert state2['kinetic'] + state2['potential'] == -0.010562891563767518

def test_initialize():
    wrapper.initialize('Mechanical')
    wrapper_ala.initialize('Electrostatic')
    print(wrapper.main_info['kinetic'] + wrapper.main_info['potential'])
    print(wrapper_ala.main_info['kinetic'] + wrapper_ala.main_info['potential'])
    assert wrapper.main_info['kinetic'] + wrapper.main_info['potential'] ==  -0.027789330729325913
    assert wrapper_ala.main_info['kinetic'] + wrapper_ala.main_info['potential'] == -0.035126792644987366

def test_get_main_info():
    state1 = wrapper.get_main_info()
    state2 = wrapper_ala.get_main_info()
    
    print(state1['kinetic'] + state1['potential'])
    print(state2['kinetic'] + state2['potential'])
    assert state1['kinetic'] + state1['potential'] == -0.027789330729325913
    assert state2['kinetic'] + state2['potential'] == -0.035126792644987366
    assert 'topology' in state1
    assert 'topology' in state2

def test_take_step():
    force1 = {0 : np.array([0.0,0.0,0.0]), 1 : np.array([0.0, 0.0, 0.0])}
    force2 = {0 : np.array([0.0,0.0,0.0]), 1 : np.array([-0.0001, -0.0001, -0.0001])}
    wrapper.take_step(force1)
    energy1 = wrapper.main_info['kinetic'] + wrapper.main_info['potential']
    forces1 = wrapper.main_info['forces'][1]
    print(forces1)
    wrapper.take_step(force2)
    energy2 = wrapper.main_info['kinetic'] + wrapper.main_info['potential']
    forces2 = wrapper.main_info['forces'][1]
    print(forces2)

    assert energy1 == -0.027756743159817597
    assert energy2 == -0.02581537517928049
    assert np.allclose(np.array([ 31.84484291,-745.71618652,-415.50253296]), forces1)
    assert np.allclose(np.array([ 28.39440727,-746.68914795,-423.17053223]), forces2)

def test_create_modeller():
    mod1 = wrapper_ala.create_modeller(qm_atoms=[0,1,2,3], keep_qm=True)
    mod2 = wrapper_ala.create_modeller(qm_atoms=[0,1,2,3], keep_qm=False)
    atom1 = mod1.topology.getNumAtoms()
    atom2 = mod2.topology.getNumAtoms()

    assert atom1 == 4
    assert atom2 == 29


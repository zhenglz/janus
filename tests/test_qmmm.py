from janus import qm_wrapper, mm_wrapper, qmmm, system
import numpy as np
import pytest
import os

water = os.path.join(str('tests/files/test_openmm/water.pdb'))
ala = os.path.join(str('tests/files/test_openmm/ala_ala_ala.pdb'))

psi4 = qm_wrapper.Psi4Wrapper()
psi4_ala = qm_wrapper.Psi4Wrapper(charge=1)

om_m = mm_wrapper.OpenMMWrapper(sys_info=water)
om_m.initialize('Mechanical')
main_info_m = om_m.get_main_info()

om_ala = mm_wrapper.OpenMMWrapper(sys_info=ala)
om_ala.initialize('Electrostatic')
main_info_ala = om_ala.get_main_info()

mech     = qmmm.QMMM(psi4,     om_m,sys_info=water, qm_atoms=[0,1,2], embedding_method='Mechanical' )
ala_link = qmmm.QMMM(psi4_ala, om_ala,sys_info=ala, qm_atoms=[0,1,2], embedding_method='Electrostatic' )
ala_RC   = qmmm.QMMM(psi4_ala, om_ala,sys_info=ala, qm_atoms=[0,1,2], embedding_method='Electrostatic', boundary_treatment='RC' )
ala_RCD  = qmmm.QMMM(psi4_ala, om_ala,sys_info=ala, qm_atoms=[0,1,2], embedding_method='Electrostatic', boundary_treatment='RCD')

sys_mech = system.System([0,1,2], [0],  0)
sys_ala_link = system.System([0,1,2,3],[0],  0)
sys_ala_RC = system.System([0,1,2,3,4,5], [0,1], 0)
sys_ala_RCD = system.System([0], [0],  0)

sys_mech.entire_sys = main_info_m
sys_ala_link.entire_sys = main_info_ala
sys_ala_RC.entire_sys = main_info_ala
sys_ala_RCD.entire_sys = main_info_ala

def test_edit_qm_atoms():

    a = np.array([0,1,2])
    b = np.array([3,4,5])
    c = np.array([0,1,2,3,4,5])

    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[0,1,2])), a)
    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[2,3])), b)
    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[0,1,2,3])), c)
    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[0,1,2,3,4])), c)
    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[0,1,2,4,5])), a)
    assert np.allclose(np.array(mech.edit_qm_atoms(qm_atoms=[0,1,2,5])), a)

def test_find_boundary_bonds():

    mech.find_boundary_bonds(qm_atoms=[1,2,3,4])
    ala_link.find_boundary_bonds(qm_atoms=[0,1,2,3])
    ala_RC.find_boundary_bonds(qm_atoms=[0,1,2,3,4,5])
    ala_RCD.find_boundary_bonds(qm_atoms=[0])

    assert len(mech.qmmm_boundary_bonds) == 0
    assert len(ala_link.qmmm_boundary_bonds) == 1 
    assert len(ala_RC.qmmm_boundary_bonds) == 2
    assert len(ala_RCD.qmmm_boundary_bonds) == 4

def test_prepare_link_atom():

    ala_link.prepare_link_atom()
    ala_RC.prepare_link_atom()
    ala_RCD.prepare_link_atom()

    assert len(ala_link.link_atoms['all_outer_bonds']) == 0
    assert ala_link.link_atoms[0]['link_atom'] == 'H'
    assert np.allclose(np.array(ala_RC.link_atoms['all_outer_bonds'][1]), np.array([7, 8, 9]))
    assert np.allclose(np.array(ala_RCD.link_atoms['all_outer_bonds'][0]), np.array([10, 6, 5]))
    assert len(np.array(ala_RCD.link_atoms['all_outer_bonds'][1])) == 0

def test_get_redistributed_positions():

    positions = sys_ala_RC.entire_sys['positions']
    pos1 = ala_RC.get_redistributed_positions(positions, ala_RC.link_atoms['all_outer_bonds'][0], ala_RC.link_atoms['all_mm'][0])
    pos2 = ala_RC.get_redistributed_positions(positions, [], ala_RC.link_atoms['all_mm'][0])
    
    pos = np.array([[ 0.17042224,  0.1955063 ,  0.0170204 ],
                    [ 0.27181732,  0.15053827, -0.00442697]])

    assert len(pos2) == 0
    assert np.allclose(np.array(pos1), pos)

def test_get_external_charges():

    charges_mech = mech.get_external_charges(sys_mech)
    charges_ala_link = ala_link.get_external_charges(sys_ala_link)
    charges_ala_RC = ala_RC.get_external_charges(sys_ala_RC)
    charges_ala_RCD = ala_RCD.get_external_charges(sys_ala_RCD)
    
    assert charges_mech is None
    assert len(charges_ala_link) == 29
    assert len(charges_ala_RC) == 30
    assert len(charges_ala_RCD) == 31

def test_make_primary_subsys_trajectory():

    traj_mech, link_mech = mech.make_primary_subsys_trajectory()
    traj_ala, link_ala = ala_RC.make_primary_subsys_trajectory(qm_atoms=sys_ala_RC.qm_atoms)

    mech.traj_ps = traj_mech
    ala_RC.traj_ps = traj_ala

    assert len(link_mech) == 0
    assert len(link_ala) == 2
    assert len(traj_mech.xyz[0]) == 3
    assert len(traj_ala.xyz[0]) == 8
    
def test_make_second_subsys_trajectory():

    traj_mech = mech.make_second_subsys_trajectory()
    traj_ala = ala_RC.make_second_subsys_trajectory(qm_atoms=sys_ala_RC.qm_atoms)
    
    assert len(traj_mech.xyz[0]) ==6
    assert len(traj_ala.xyz[0]) == 27


def test_mechanical():
    mech.mechanical(sys_mech, main_info_m)
    ala_link.mechanical(sys_ala_link, main_info_ala)
    
    assert len(sys_mech.qmmm_forces) == 3
    assert len(sys_ala_link.qmmm_forces) == 5
    assert sys_mech.entire_sys['energy'] == -0.027789337360217735
    assert sys_mech.primary_subsys['ll']['energy'] == 0.0
    assert sys_mech.primary_subsys['hl']['energy'] == -74.96297372571573
    assert sys_ala_link.entire_sys['energy'] == -0.03512682903232768
    assert sys_ala_link.primary_subsys['ll']['energy'] == 0.02107866334070054
    assert sys_ala_link.primary_subsys['hl']['energy'] == -55.684475328036896

def test_electrostatic():
    ala_link.electrostatic(sys_ala_link, main_info_ala)
    ala_RCD.electrostatic(sys_ala_RCD, main_info_ala)

    print(sys_ala_link.second_subsys['ll']['energy'])
    print(sys_ala_link.primary_subsys['hl']['energy'])
    print(sys_ala_RCD.entire_sys['energy'])
    print(sys_ala_RCD.primary_subsys['ll']['energy'])
    print(sys_ala_RCD.second_subsys['ll']['energy'] )
    print(sys_ala_RCD.primary_subsys['hl']['energy'])

    assert len(sys_ala_link.qmmm_forces) == 33
    assert len(sys_ala_RCD.qmmm_forces) == 33
    assert sys_ala_link.entire_sys['energy'] == -0.03512682903232768
    assert sys_ala_link.primary_subsys['ll']['energy'] == 0.02107866334070054
    assert sys_ala_link.second_subsys['ll']['energy'] == -0.04884654076021316
    assert sys_ala_link.primary_subsys['hl']['energy'] == -55.70399957201144
    assert sys_ala_RCD.entire_sys['energy'] == -0.03512682903232768
    assert sys_ala_RCD.primary_subsys['ll']['energy'] == 0.021188479175053232
    assert sys_ala_RCD.second_subsys['ll']['energy'] == -0.04884654076021316
    assert sys_ala_RCD.primary_subsys['hl']['energy'] == -55.707295905495776


def test_update_traj():

    mech.traj.xyz[0] = np.zeros((9,3))
    pos1 = mech.traj.xyz[0]
    mech.update_traj(main_info_m['positions'], main_info_m['topology'], 'OpenMM')
    
    assert np.allclose(pos1, np.zeros((9,3)))
    assert np.allclose(mech.traj.xyz[0], main_info_m['positions'])
    
def test_run_qmmm():
    mech.qm_atoms = [0,1,2]
    ala_link.qm_atoms = [0,1,2,3]

    mech.run_qmmm(main_info_m, 'OpenMM')
    ala_link.run_qmmm(main_info_ala, 'OpenMM')

    assert 'qm' in mech.systems[0]
    assert 'qm' in ala_link.systems[0]
    assert len(mech.systems[0]['qmmm_forces']) == 3
    assert len(ala_link.systems[0]['qmmm_forces']) == 33
    assert mech.systems[0]['qmmm_energy'] == -74.99077533004528
    assert ala_link.systems[0]['qmmm_energy'] ==  -55.72526692759818 
    assert mech.run_ID == 1
    assert ala_link.run_ID == 1
    

def test_get_forces():
    f_mech = mech.get_forces()
    f_link = ala_link.get_forces()

    assert len(f_mech) == 3
    assert len(f_link) == 33


#def test_compute_gradients():
# pass in a system with gradients 
    # tested in mechanical and electrostatic, but need for RCD testing

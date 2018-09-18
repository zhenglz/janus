"""
Testing for psi4_wrapper.py module
"""
from janus import psi4_wrapper
import numpy as np
from copy import deepcopy

config2 = {
        "basis_set" : "3-21G",
        "scf_type" : "pk",
        "guess_orbitals" : "sad",
        "reference" : "uhf",
        "e_convergence" : 1e-8,
        "d_convergence" : 1e-8,
        "method" : "scf",
        "charge_method" : "MULLIKEN_CHARGES",
        "charge" : 0,
        "multiplicity" : 1
        }
config1 = {
        "basis_set" : "STO-3G",
        "scf_type" : "df",
        "guess_orbitals" : "sad",
        "reference" : "rhf",
        "e_convergence" : 1e-8,
        "d_convergence" : 1e-8,
        "method" : "scf",
        "charge_method" : "MULLIKEN_CHARGES",
        "charge" : 0,
        "multiplicity" : 1
        }

qm_sys1 = psi4_wrapper.Psi4_wrapper(config1)
qm_sys2 = psi4_wrapper.Psi4_wrapper(config2)
qm_sys3 = psi4_wrapper.Psi4_wrapper(config2)

qm_mol = """O     0.123   3.593   5.841 
H    -0.022   2.679   5.599 
H     0.059   3.601   6.796 
O     0.017   6.369   7.293 
H    -0.561   5.928   6.669 
H     0.695   6.771   6.749 
"""
gradient1 = np.array([[-0.00995519, -0.04924799,  0.03606667],  
                        [ 0.00685005,  0.0390004 ,  0.00096903],
                        [ 0.00308006,  0.00941025, -0.03776953],
                        [ 0.00633522, -0.00137517, -0.0604841 ],
                        [ 0.01545583,  0.01344479,  0.03199705],
                        [-0.02176597, -0.01123228,  0.02922087]])

gradient2 = np.array([[ 0.00144853, -0.00776505,  0.0015876 ],
                        [ 0.00158141,  0.01248499,  0.00729603],
                        [-0.0027212 , -0.00692001, -0.01255027],
                        [ 0.00238897,  0.00104995, -0.00428942],
                        [ 0.0084365 ,  0.00927855,  0.00464643],
                        [-0.01114469, -0.00549142,  0.00150409]])

gradient3 = np.array([[  1.70948114e-03,  -5.78855078e-03,  -7.33574116e-06],
                        [  1.41369972e-03,   1.00855666e-02,   1.12539617e-02],
                        [ -2.87535666e-03,  -9.09313637e-03,  -1.32275167e-02],
                        [  2.22089216e-03,   1.89013451e-03,  -4.26816857e-03],
                        [  8.65798756e-03,   8.65893257e-03,   4.80828938e-03],
                        [ -1.11267039e-02,  -5.75294651e-03,   1.44077001e-03]])

charges = [[-0.834, 0.115 ,  0.313, 6.148],
            [ 0.417, 0.12  ,  0.241, 5.193],
            [ 0.417, 0.66  , -0.415, 6.446]]

def test_build_qm_param():
    
    qm_sys1.build_qm_param()
    qm_sys2.build_qm_param()
    qm_sys3.build_qm_param()

    assert qm_sys1.qm_param['basis'] == 'STO-3G'
    assert qm_sys1.qm_param['scf_type'] == 'df' 
    assert qm_sys1.qm_param['guess'] == 'sad' 
    assert qm_sys1.qm_param['reference'] == 'rhf'
    assert qm_sys1.qm_param['e_convergence'] == 1e-8
    assert qm_sys1.qm_param['d_convergence'] == 1e-8 

    assert qm_sys2.qm_param['basis'] == '3-21G'
    assert qm_sys2.qm_param['scf_type'] == 'pk' 
    assert qm_sys2.qm_param['guess'] == 'sad' 
    assert qm_sys2.qm_param['reference'] == 'uhf'
    assert qm_sys2.qm_param['e_convergence'] == 1e-8
    assert qm_sys2.qm_param['d_convergence'] == 1e-8 

def test_set_external_charges():

    qm_sys2.set_external_charges(charges)
    
    assert qm_sys2.external_charges == charges

def test_set_qm_geometry():
    
    qm_sys1.set_qm_geometry(qm_mol,10)
    qm_sys2.set_qm_geometry(qm_mol,10)
    qm_sys3.set_qm_geometry(qm_mol,10)

    assert qm_sys1.qm_geometry == qm_mol
    assert qm_sys2.qm_geometry == qm_mol
    assert qm_sys3.qm_geometry == qm_mol

def test_compute_energy():
    """
    Function to test get_psi4_energy is getting energy correctly
    """

    qm_sys1.compute_energy()
    qm_sys2.compute_energy()
    qm_sys3.compute_energy()

    assert np.allclose(qm_sys1.energy, -149.92882700815)
    assert np.allclose(qm_sys2.energy,-151.18483039002274)
    assert np.allclose(qm_sys3.energy,-151.17927491846075)

def test_compute_gradient():
    
    qm_sys1.compute_gradient()
    qm_sys2.compute_gradient()
    qm_sys3.compute_gradient()
    print(qm_sys1.gradient)
    print(gradient1)

    assert np.allclose(qm_sys1.gradient, gradient1)
    assert np.allclose(qm_sys2.gradient, gradient2)
    assert np.allclose(qm_sys3.gradient, gradient3)

def test_compute_energy_and_gradient():
    
    qm_sys1.compute_energy_and_gradient()
    print(qm_sys1.gradient)
    print(gradient1)
    qm_sys2.compute_energy_and_gradient()
    print(qm_sys2.gradient)
    print(gradient2)

    assert np.allclose(qm_sys1.energy, -149.92882700815)
    assert np.allclose(qm_sys1.gradient, gradient1)

def test_compute_scf_charges():

    qm_sys1.compute_scf_charges()

    charge1 = np.array([-0.3742676, 0.18533499, 0.18958095, -0.37355466, 0.18900526, 0.18390106])

    assert np.allclose(qm_sys1.charges, charge1)

def test_compute_energy_and_charges():

    qm_sys2.compute_energy_and_charges()

    charge2 = np.array([-0.75706309, 0.38308182, 0.37724382, -0.74477242, 0.37486706, 0.36664282])

    assert np.allclose(qm_sys2.energy,-151.18483039002274)
    assert np.allclose(qm_sys2.charges, charge2)

def test_run_qm():

    info2 = qm_sys2.run_qm(qm_mol,20)
    info3 = qm_sys3.run_qm(qm_mol,20)
    print(qm_sys2.gradient)
    print(gradient2)
    print(qm_sys3.gradient)
    print(gradient3)


    assert np.allclose(info2['energy'],-151.18483039002274)
    assert np.allclose(info3['energy'],-151.17927491846075)
    assert np.allclose(info2['gradients'], gradient2)
    assert np.allclose(info3['gradients'], gradient3)


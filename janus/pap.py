from .aqmmm import AQMMM
from .system import System
import itertools as it
from copy import deepcopy
import numpy as np

class PAP(AQMMM):

    def __init__(self, param, qm_wrapper, mm_wrapper):
        """
        Initializes the PAP class object
    
        Parameters
        ----------
        See parameters for AQMMM class 

        Returns
        -------
        A PAP class object

        Examples
        --------
        pap = PAP(param, psi4_wrapper, openmm_wrapper)
        """
        
        super().__init__(param, qm_wrapper, mm_wrapper, 'PAP')
        self.modified_variant = param['modified_variant']


    def partition(self, qm_center=None, info=None): 
        """
        Finds the partitions as required by the PAP method 
        and saves each partition as a system object.
        Saves all systems in the dictionary self.systems

        Parameters
        ----------
        qm_center: list of atoms that define the qm center, 
                   default is None

        Returns
        -------
        None

        Examples
        --------
        partition([0])
        """
    
        if qm_center is None:
            qm_center = self.qm_center

        self.define_buffer_zone(qm_center)

        qm = System(qm_indices=self.qm_atoms, qm_residues=self.qm_residues, run_ID=self.run_ID, partition_ID='qm')

        self.systems[self.run_ID] = {}
        self.systems[self.run_ID][qm.partition_ID] = qm

        # the following only runs if there are groups in the buffer zone
        if self.buffer_groups:

            self.partitions = self.get_combos(list(self.buffer_groups))

            for i, part in enumerate(self.partitions):
                sys = System(qm_indices=self.qm_atoms, qm_residues=self.qm_residues, run_ID=self.run_ID, partition_ID=i)
                for group in part:
                    sys.qm_residues.append(group)
                    for idx in self.buffer_groups[group].atoms:
                        sys.qm_atoms.append(idx)
                
                # each partition has a copy of its buffer groups - 
                # don't know if this is actually needed
                sys.buffer_groups = {k: self.buffer_groups[k] for k in part}
                self.systems[self.run_ID][sys.partition_ID] = sys

    def run_aqmmm(self):
        """
        Interpolates the energy and gradients from each partition
        according to the PAP method
        """
        
        qm = self.systems[self.run_ID]['qm']

        if not self.buffer_groups:
            self.systems[self.run_ID]['qmmm_energy'] = qm.qmmm_energy
            self.systems[self.run_ID]['qmmm_forces'] = qm.qmmm_forces

        else:

            # getting first term of ap energy and forces (w/o gradient of switching function)
            energy = deepcopy(self.systems[self.run_ID]['qm'].qmmm_energy)
            self.systems[self.run_ID]['qm'].aqmmm_forces = deepcopy(self.systems[self.run_ID]['qm'].qmmm_forces)
            forces = self.systems[self.run_ID]['qm'].aqmmm_forces
            for i, buf in self.buffer_groups.items():
                energy *= (1 - buf.s_i)
                forces.update((x, y*(1 - buf.s_i)) for x,y in forces.items())
            self.systems[self.run_ID]['qm'].aqmmm_energy = deepcopy(energy)

            qmmm_forces = deepcopy(forces)

            # getting rest of the terms of ap energy and forces (w/o gradient of switching function)
            for i, part in enumerate(self.partitions):
                part_energy = deepcopy(self.systems[self.run_ID][i].qmmm_energy)
                self.systems[self.run_ID][i].aqmmm_forces = deepcopy(self.systems[self.run_ID][i].qmmm_forces)
                forces = self.systems[self.run_ID][i].aqmmm_forces
                for j, buf in self.buffer_groups.items():
                    if j in part:
                        part_energy *= buf.s_i
                        forces.update((x, y*buf.s_i) for x,y in forces.items())
                    else:
                        part_energy *= (1 - buf.s_i)
                        forces.update((x, y*(1 - buf.s_i)) for x,y in forces.items())

                self.systems[self.run_ID][i].aqmmm_energy = deepcopy(part_energy)
                energy += part_energy

            self.systems[self.run_ID]['qmmm_energy'] = energy

            if self.modified_variant is False:
                # computing forces due to gradient of switching function for PAP
                forces_sf = self.compute_sf_gradient()

                # adding forces to total forces
                for i, force in forces_sf.items():
                    if i in qmmm_forces:
                        qmmm_forces[i] += force
                    else:
                        qmmm_forces[i] = force

            # combining all forces
            for i, part in enumerate(self.partitions):
                forces = self.systems[self.run_ID][i].aqmmm_forces
                for i, force in forces.items():
                    if i in qmmm_forces:
                        qmmm_forces[i] += force
                    else:
                        qmmm_forces[i] = force

            self.systems[self.run_ID]['qmmm_forces'] = forces
            

    def compute_sf_gradient(self):
        """
        Computes forces due to the gradient of the switching function
        
        Parameters
        ----------
        None
        
        Returns
        -------
        Forces due to gradient of switching function as a dictionary

        Examples
        --------
        forces = compute_sf_gradient
        """

        forces_sf = {self.qm_center[0]: np.zeros((3))}

        for i, buf in self.buffer_groups.items():

            # energy scaler due to partition with qm only
            buf.energy_scaler = -1 * self.systems[self.run_ID]['qm'].aqmmm_energy / (1 - buf.s_i)
            
            for p, part in enumerate(self.partitions):
                aqmmm_energy = self.systems[self.run_ID][p].aqmmm_energy
                if i in part:
                    buf.energy_scaler += aqmmm_energy / buf.s_i
                else:
                    buf.energy_scaler -= aqmmm_energy / (1 - buf.s_i)
            
            forces_sf[self.qm_center[0]] -= buf.energy_scaler * buf.d_s_i * buf.COM_coord 

            for idx, ratio in buf.weight_ratio.items():

                if idx not in forces_sf:
                    forces_sf[idx] = ratio * buf.energy_scaler * buf.d_s_i * buf.COM_coord
                else:
                    raise Exception('Overlapping buffer atom definitions')

        return forces_sf


    def get_combos(self, items=None):
        """
        Gets all combinations of a given list of indices 

        Parameters
        ----------
        items: list of indices to get combinations for
    
        Returns
        -------
        List of all possible combinations 

        Examples    
        --------
        combos = get_combos([1,2])

        In this case, combos will return 
        [(1), (2), (1,2)]
        """
        
        all_combo = []

        for i in range(1, len(items) +1):
            all_combo += list(it.combinations(items, i))

        return all_combo




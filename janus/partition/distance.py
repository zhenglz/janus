import numpy as np
from copy import deepcopy
import mdtraj as md
from janus.partition import Partition

class DistancePartition(Partition):

    def __init__(self, trajectory, topology, Rmin, Rmax):

        self.Rmin = Rmin
        self.Rmax = Rmax

        super().__init__(trajectory, topology, 'distance')

    def define_buffer_zone(self, qm_center):
        """
        Determines buffer group atoms.
        Gets the buffer groups in the buffer zone based on a distance 
        partitioning scheme, saves each buffer group as a 
        :class:`~janus.system.Buffer` object,
        and saves all buffer groups in the dictionary self.buffer_groups.
        For water as a solvent, considers the whole water molecule as a buffer group.

        Note
        ----
        Currently only worked with explicit solvent based systems. 
        Cannot treat buffer atoms that are part of large molecular structures (e.g., proteins).

        Parameters
        ----------
        qm_center : list 
            the indicies that make up the qm center

        """

        self.qm_residues = []
        self.buffer_groups = {}
        residue_tracker = [] 
        top = self.topology

        self.find_buffer_atoms(qm_center)

        for i in self.buffer_atoms:
            idx = top.atom(i).residue.index

            if idx not in residue_tracker:
                residue_tracker.append(idx)
                buf = self.get_residue_info(idx)
            
                if buf.r_i <= self.Rmin:
                    self.edit_atoms(atoms=self.qm_atoms, res_idx=idx, add=True)
                    
                elif buf.r_i >= self.Rmax:
                    self.edit_atoms(atoms=self.qm_atoms, res_idx=idx, remove=True)

                elif (buf.r_i > self.Rmin and buf.r_i < self.Rmax):
                    self.buffer_groups[idx] = buf
                    self.edit_atoms(atoms=self.qm_atoms, res_idx=idx, remove=True)


        qm_atoms = deepcopy(self.qm_atoms)
        # tracking qm_residues and cleaning up qm
        for i in qm_atoms:
            idx = top.atom(i).residue.index
            if idx not in self.qm_residues:
                res = self.get_residue_info(idx)

                if res.r_i >= self.Rmax:
                    self.edit_atoms(atoms=self.qm_atoms, res_idx=idx, remove=True)
                elif res.r_i <= self.Rmin:
                    self.edit_atoms(atoms=self.qm_atoms, res_idx=idx, add=True)
                    self.qm_residues.append(idx)

    def find_buffer_atoms(self, qm_center):
        """
        Find the buffer groups whose COM falls in between Rmin and Rmax

        Parameters
        ----------
        qm_center : list 
            the indicies that make up the qm center

        """

        if len(qm_center) == 1:
            self.COM_as_qm_center = False
            self.qm_center_xyz = self.traj.xyz[0][qm_center[0]]
            qm_center_idx = qm_center
            temp_traj = self.traj
            self.qm_center_weight_ratio = {qm_center[0] : 1}
        else:
            self.COM_as_qm_center = True
            self.qm_center_xyz, self.qm_center_atom_weights, self.qm_center_weight_ratio = self.compute_COM(qm_center)

            t = deepcopy(self.traj)
            t.topology.add_atom('DUM', md.element.Element.getBySymbol('H'), t.topology.atom(0).residue, 1)
            for atom in t.topology.atoms:
                if atom.name == 'DUM':
                    qm_center_idx = [atom.index]
            t.xyz = np.append(t.xyz[0], [self.qm_center_xyz], axis=0)
            temp_traj = t

        rmin_atoms = md.compute_neighbors(temp_traj, self.Rmin/10, qm_center_idx)
        rmax_atoms = md.compute_neighbors(temp_traj, self.Rmax/10, qm_center_idx)
        self.buffer_atoms = np.setdiff1d(rmax_atoms, rmin_atoms)
        print('buffer atoms identified by find_buffer_atom function:')
        print(self.buffer_atoms)
        self.qm_atoms = rmin_atoms[0].tolist()

        if self.COM_as_qm_center is False:
            self.qm_atoms.append(qm_center[0])

        print('qm_atoms identified by the find_buffer_atom function: ' )
        print(self.qm_atoms)


    def get_Rmin(self):
        """
        Function to return self.Rmin

        Returns
        -------
        float
            the distance from qm center to inner limit of buffer zone in angstroms

        """
        return self.Rmin

    def get_Rmax(self):
        """
        Function to return self.Rmin

        Returns
        -------
        float
            the distance from qm center to outer limit of buffer zone in angstroms

        """

        return self.Rmax

    def set_Rmin(self, Rmin):
        """
        Function to set self.Rmin
        
        Parameters
        ----------
        Rmin : float 
            the distance from qm center to inner limit of buffer zone in angstroms
        
        """

        self.Rmin = Rmin

    def set_Rmax(self, Rmax):
        """
        Function to set self.Rmax
        
        Parameters
        ----------
        Rmax : float 
            the distance from qm center to outer limit of buffer zone in angstroms
        
        """
        self.Rmax = Rmax


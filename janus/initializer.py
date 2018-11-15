import json
import os
from janus.qm_wrapper import Psi4Wrapper 
from janus.mm_wrapper import OpenMMWrapper 
from janus.qmmm import QMMM
from janus.qmmm import OniomXS
from janus.qmmm import HotSpot
from janus.qmmm import PAP
from janus.qmmm import SAP

class Initializer(object):
    """
    Class that initializes the initial parameters 
    and necessary wrapppers
    """

    def __init__(self, param, as_file=True):
        """
        Initializes the Initializer class with parameters and updates 
        defaults with user defined parameters

        Parameters
        ----------
        param : str 
            filename containing a json input file, if as_file is False, param is a dict
        as_file : bool
             param is a file if True, dict if False

        """

        if as_file is True:
            self.param = self.load_param(param)
        else:
            self.param = param

        try:
            print('System information read from {}'.format(self.param['system']['system_info']))
        except KeyError:
            print('No system info was specified')
        
        if 'system_info_format' not in self.param['system']:
            self.param['system']['system_info_format'] = 'pdb'
        
        if 'md' in self.param:
            self.run_md = True

            try:
                self.md_sim_prog = self.param['md']['md_simulation_program']
            except KeyError:
                print('MD simulation program needs to be specified')
            try:
                self.start_qmmm = self.param['md']['start_qmmm']
            except KeyError:
                print('step at which to start qmmm needs to be specified')
            try:
                self.end_qmmm = self.param['md']['end_qmmm']
            except KeyError:
                print('step at which to end qmmm needs to be specified')
            try:
                self.step_size = self.param['md']['step_size']
            except:
                self.step_size=1
                print('Step size not specified, default of 1 femtosecond will be used')
            try:
                self.md_steps = self.param['md']['md_steps']
            except:
                self.md_steps = self.end_qmmm 
                print('Number of steps not specified, taking {} total steps by default'.format(self.end_qmmm))
            try:
                self.md_ensemble = self.param['md']['md_ensemble']
            except:
                self.md_ensemble = 'NVE'
                print('NVE ensemble used by default')

            self.qmmm_steps = self.end_qmmm - self.start_qmmm

            if type(self.md_steps) is int:
                self.end_steps = self.md_steps - self.end_qmmm
            elif type(self.md_steps) is list:
                self.end_steps = self.md_steps[-1] - self.end_qmmm

            if 'restart' in self.param['md']:
                self.md_restart = self.param['md']['restart']
                try:
                    self.restart_chkpt_filename = self.param['md']['restart_checkpoint_filename']
                except KeyError:
                    print('restart checkpoint filename needs to be specified')
                try:
                    self.restart_forces_filename = self.param['md']['restart_forces_filename']
                except KeyError:
                    print('restart forces filename needs to be specified')

                try:
                    self.return_forces_interval = self.param['md']['return_checkpoint_interval']
                except KeyError:
                    print('return checkpoint interval needs to be specified')
                     
            else:   
                self.md_restart = False

            try:
                self.return_forces_filename = self.param['md']['return_forces_filename']
            except:
                self.return_forces_filename = 'forces.pkl'
                print('forces printed to forces.json')

                
                
        else:
            self.run_md = False
            self.md_sim_prog = None
            print("MD simulation not specified. Not performing a simulation")
            

        self.qmmm_paramfile = os.path.abspath(os.path.dirname(__file__)) + '/default_input/qmmm.json'
        self.aqmmm_paramfile = os.path.abspath(os.path.dirname(__file__)) + '/default_input/aqmmm.json'
        self.psi4_paramfile = os.path.abspath(os.path.dirname(__file__)) + '/default_input/psi4.json'
        self.openmm_paramfile = os.path.abspath(os.path.dirname(__file__)) + '/default_input/openmm.json'

        self.qmmm_param = self.load_param(self.qmmm_paramfile)
        self.aqmmm_param = self.load_param(self.aqmmm_paramfile)

            
        try:
            self.hl_program = self.param['qmmm']['hl_program']
        except:
            print("No QM program was specified. Psi4 will be used")
            self.hl_program = 'Psi4'

        try:
            self.ll_program = self.param['qmmm']['ll_program']
        except:
            print("No MM program was specified. OpenMM will be used")
            self.ll_program = 'OpenMM'


        self.update_param()

    def update_param(self):
        """
        updates default parameters with user defined parameters

        """
        try:
            self.qmmm_param.update(self.param['qmmm'])
            self.qmmm_param.update(self.param['system'])
        except KeyError: 
            print("No QMMM parameters given.")

        if self.hl_program == "Psi4":
            self.hl_param = self.load_param(self.psi4_paramfile)
        elif self.hl_program == "OpenMM":
            self.hl_param = self.load_param(self.openmm_paramfile)
        else:
            print("Only Psi4 and OpenMM currently available to be used in high level computations")

        if self.ll_program == "OpenMM":
            self.ll_param = self.load_param(self.openmm_paramfile)
        else:
            print("Only OpenMM currently available to be used in low level computations")

        self.ll_param.update(self.param['system'])

        if self.run_md is True:

            if self.md_sim_prog == "OpenMM":
                self.md_sim_param = self.load_param(self.openmm_paramfile)
            else:
                print("Only OpenMM currently available")

            self.md_sim_param.update(self.param['system'])
            self.md_sim_param.update(self.param['md'])
            self.ll_param.update(self.param['md'])

        try:
            self.hl_param.update(self.param['hl'])
        except:
            print("No high level parameters given. Using Psi4 defaults")
        try:
            self.ll_param.update(self.param['ll'])
            self.md_sim_param.update(self.param['ll'])
        except:
            print("No low level parameters given. Using OpenMM defaults")

        try:
            self.md_sim_param.update(self.param['ll_md'])
        except:
            print("No low level parameters given for md simulation. Using OpenMM defaults")
        try:
            self.aqmmm_param.update(self.param['aqmmm'])
            self.aqmmm_param.update(self.qmmm_param)
        except: 
            print("No AQMMM parameters given, running traditional QM/MM")

        

    def initialize_wrappers(self, simulation=False, restart=False):
        """
        Instantiates qm, mm, qmmm, and/or aqmmm wrapper objects 
        used for computation based on input parameters


        Returns
        -------
        MMWrapper object
        QMMM wrapper object

        """

        # create hl_wrapper object
        if self.hl_program == "Psi4":
            print('using Psi4 for high level computation')
            hl_wrapper = Psi4Wrapper(self.hl_param)
        elif self.hl_program == "OpenMM":
            hl_wrapper = OpenMMWrapper(self.hl_param)
            print('using OpenMM for high level computation')
        else:
        # add other options for qm program here
            print("Only Psi4 and OpenMM currently available")

        # create ll_wrapper object
        if self.ll_program == "OpenMM":
            print('initializing low level wrapper')
            ll_wrapper = OpenMMWrapper(self.ll_param)
        else:
        # add other options for mm program here
            print("Only OpenMM currently available")

        if self.md_sim_prog == "OpenMM":
            print('initializing MD simulation wrapper')
            md_sim_wrapper = OpenMMWrapper(self.md_sim_param)
        else:
            print("Only OpenMM currently available")


        if self.param['qmmm']['run_aqmmm'] is False:
            qmmm = QMMM(self.qmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        elif self.aqmmm_param['aqmmm_scheme'] == 'ONIOM-XS':
            qmmm = OniomXS(self.aqmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        elif self.aqmmm_param['aqmmm_scheme'] == 'Hot-Spot':
            qmmm = HotSpot(self.aqmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        elif self.aqmmm_param['aqmmm_scheme'] == 'PAP':
            qmmm = PAP(self.aqmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        elif self.aqmmm_param['aqmmm_scheme'] == 'SAP':
            qmmm = SAP(self.aqmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        elif self.aqmmm_param['aqmmm_scheme'] == 'DAS':
            qmmm = SAP(self.aqmmm_param, hl_wrapper, ll_wrapper, self.md_sim_prog)
        else:
            print("Only ONIOM-XS, Hot Spot, PAP, SAP, and DAS currently implemented")

        if (simulation is True and restart is False):
            # initialize mm_wrapper with information about initial system
            md_sim_wrapper.initialize(self.qmmm_param['embedding_method'])
            return md_sim_wrapper, qmmm
 
        elif (simulation is True and restart is True):
            # initialize mm_wrapper with information about initial system
            md_sim_wrapper.restart(self.qmmm_param['embedding_method'], self.restart_chkpt_filename, self.restart_forces_filename)
            return md_sim_wrapper, qmmm

        else:
            return ll_wrapper, qmmm
        

    def load_param(self, filename):
        """
        Converts a json file into a dictionary
    
        Parameters
        ----------
        filename : str
            name of json file

        Returns
        -------
        dict
            parameters contained in filename

        """

        with open(filename) as parameter_file:
            param = json.load(parameter_file)
        
        return param


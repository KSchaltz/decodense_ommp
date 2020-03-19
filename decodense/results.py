#!/usr/bin/env python
# -*- coding: utf-8 -*

"""
results module
"""

__author__ = 'Dr. Janus Juul Eriksen, University of Bristol, UK'
__maintainer__ = 'Dr. Janus Juul Eriksen'
__email__ = 'janus.eriksen@bristol.ac.uk'
__status__ = 'Development'

import os
import numpy as np
import math
from pyscf import gto, lib
from typing import Dict, Tuple, List, Union, Any

from .decomp import DecompCls
from .tools import git_version, time_str


def collect_res(mol: gto.Mole, decomp: DecompCls) -> Dict[str, Any]:
        res: Dict[str, Any] = {'prop_el': decomp.prop_el, 'prop_nuc': decomp.prop_nuc, \
                               'ref': _ref(mol, decomp), 'thres': decomp.thres, \
                               'part': decomp.part, 'time': decomp.time, 'sym': mol.groupname}
        if decomp.orbs == 'localized':
            res['loc'] = decomp.loc
            res['pop'] = decomp.pop
        if decomp.xc != '':
            res['xc'] = decomp.xc
        return res


def table_info(mol: gto.Mole, decomp: DecompCls) -> str:
        """
        this function prints basic info
        """
        # init string & form
        string: str = ''
        form: Tuple[Any, ...] = ()

        # print geometry
        string += '\n\n   ------------------------------------\n'
        string += '{:^43}\n'
        string += '   ------------------------------------\n'
        form += ('geometry',)

        molecule = gto.tostring(mol).split('\n')
        for i in range(len(molecule)):
            atom = molecule[i].split()
            for j in range(1, 4):
                atom[j] = float(atom[j])
            string += '   {:<3s} {:>10.5f} {:>10.5f} {:>10.5f}\n'
            form += (*atom,)
        string += '   ------------------------------------\n'

        # system info
        string += '\n\n system info:\n'
        string += ' ------------\n'
        string += ' point group        =  {:}\n'
        string += ' basis set          =  {:}\n'
        string += '\n partitioning       =  {:}\n'
        string += ' threshold          =  {:}\n'
        form += (mol.groupname, mol.basis, decomp.part, decomp.thres,)
        if decomp.orbs == 'localized':
            string += ' localization       =  {:}\n'
            string += ' assignment         =  {:}\n'
            form += (decomp.loc, decomp.pop,)
        if decomp.xc != '':
            string += ' xc functional      =  {:}\n'
            form += (decomp.xc,)
        string += '\n reference funct.   =  {:}\n'
        string += ' electrons          =  {:d}\n'
        string += ' alpha electrons    =  {:d}\n'
        string += ' beta electrons     =  {:d}\n'
        string += ' spin: <S^2>        =  {:.3f}\n'
        string += ' spin: 2*S + 1      =  {:.3f}\n'
        string += ' basis functions    =  {:d}\n'
        form += (_ref(mol, decomp), mol.nelectron, mol.nalpha, mol.nbeta, \
                 decomp.ss + 1.e-6, decomp.s + 1.e-6, mol.nao_nr(),)

        # calculation info
        string += '\n total time         =  {:}\n'
        if decomp.prop == 'energy':
            string += ' reference result   = {:.5f}\n'
            form += (time_str(decomp.time), decomp.prop_ref)
        elif decomp.prop == 'dipole':
            string += ' reference result   = {:.3f}  / {:.3f}  / {:.3f}\n'
            form += (time_str(decomp.time), *decomp.prop_ref)

        # git version
        string += '\n git version: {:}\n\n'
        form += (git_version(),)

        return string.format(*form)


def table_atoms(mol: gto.Mole, decomp: DecompCls) -> str:
        """
        this function prints the results based on an atom-based partitioning
        """
        # init string & form
        string: str = ''
        form: Tuple[Any, ...] = ()

        if decomp.prop == 'energy':

            string += '----------------------------------------------------\n'
            string += '{:^52}\n'
            string += '{:^52}\n'
            string += '----------------------------------------------------\n'
            string += '----------------------------------------------------\n'
            string += ' atom |  electronic  |    nuclear   |     total\n'
            string += '----------------------------------------------------\n'
            string += '----------------------------------------------------\n'
            form += ('ground-state energy', decomp.orbs + ' MOs',)

            for i in range(mol.natm):
                string += ' {:<5s}|{:>12.5f}  |{:>+12.5f}  |{:>+12.5f}\n'
                form += ('{:s}{:d}'.format(mol.atom_symbol(i), i), \
                                           decomp.prop_el[i], decomp.prop_nuc[i], \
                                           decomp.prop_el[i] + decomp.prop_nuc[i],)

            string += '----------------------------------------------------\n'
            string += '----------------------------------------------------\n'
            string += ' sum  |{:>12.5f}  |{:>+12.5f}  |{:>+12.5f}\n'
            string += '----------------------------------------------------\n\n'
            form += (np.sum(decomp.prop_el), np.sum(decomp.prop_nuc), \
                     np.sum(decomp.prop_el + decomp.prop_nuc),)

        elif decomp.prop == 'dipole':

            string += '-------------------------------------------------------------------------------------------------------------------\n'
            string += '{:^113}\n'
            string += '{:^113}\n'
            string += '-------------------------------------------------------------------------------------------------------------------\n'
            string += '      |             electronic            |               nuclear             |               total\n'
            string += ' atom -------------------------------------------------------------------------------------------------------------\n'
            string += '      |     x     /     y     /     z     |     x     /     y     /     z     |     x     /     y     /     z\n'
            string += '-------------------------------------------------------------------------------------------------------------------\n'
            string += '-------------------------------------------------------------------------------------------------------------------\n'
            form += ('ground-state dipole moment', decomp.orbs + ' MOs',)

            for i in range(mol.natm):
                string += ' {:<5s}| {:>8.3f}  / {:>8.3f}  / {:>8.3f}  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}\n'
                form += ('{:s}{:d}'.format(mol.atom_symbol(i), i), \
                                           *decomp.prop_el[i] + 1.e-10, *decomp.prop_nuc[i] + 1.e-10, \
                                           *(decomp.prop_el[i] + decomp.prop_nuc[i]) + 1.e-10)

            string += '-------------------------------------------------------------------------------------------------------------------\n'
            string += '-------------------------------------------------------------------------------------------------------------------\n'

            string += ' sum  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}\n'
            string += '-------------------------------------------------------------------------------------------------------------------\n\n'
            form += (*np.fromiter(map(math.fsum, decomp.prop_el.T), dtype=np.float64, count=3) + 1.e-10, \
                     *np.fromiter(map(math.fsum, decomp.prop_nuc.T), dtype=np.float64, count=3) + 1.e-10, \
                     *np.fromiter(map(math.fsum, decomp.prop_el.T + decomp.prop_nuc.T), dtype=np.float64, count=3) + 1.e-10,)

        return string.format(*form)


def table_bonds(mol: gto.Mole, decomp: DecompCls, cent: np.ndarray) -> str:
        """
        this function prints the results based on a bond-based partitioning
        """
        # inter-atomic distance array
        dist = gto.mole.inter_distance(mol) * lib.param.BOHR

        # init string & form
        string: str = ''
        form: Tuple[Any, ...] = ()

        if decomp.prop == 'energy':

            string += '--------------------------------------------------------\n'
            string += '{:^55}\n'
            string += '{:^55}\n'
            string += '--------------------------------------------------------\n'
            string += '  MO  |   electronic  |    atom(s)    |   bond length\n'
            string += '--------------------------------------------------------\n'
            form += ('ground-state energy', decomp.orbs,)

            for i in range(2):
                string += '--------------------------------------------------------\n'
                string += '{:^55}\n'
                string += '--------------------------------------------------------\n'
                form += ('alpha-spin',) if i == 0 else ('beta-spin',)
                for j in range(decomp.prop_el[i].size):
                    core = cent[i][j, 0] == cent[i][j, 1]
                    string += '  {:>2d}  |{:>12.5f}   |    {:<11s}|  {:>10s}\n'
                    form += (j, decomp.prop_el[i][j], \
                             '{:s}{:d}'.format(mol.atom_symbol(cent[0][j, 0]), cent[i][j, 0]) if core \
                             else '{:s}{:d}-{:s}{:d}'.format(mol.atom_symbol(cent[i][j, 0]), cent[i][j, 0], \
                                                               mol.atom_symbol(cent[i][j, 1]), cent[i][j, 1]), \
                             '' if core else '{:>.6f}'.format(dist[cent[i][j, 0], cent[i][j, 1]]),)

            string += '--------------------------------------------------------\n'
            string += '--------------------------------------------------------\n'
            string += ' sum  |{:>12.5f}   |\n'
            form += (np.sum(decomp.prop_el[0]) + np.sum(decomp.prop_el[1]),)

            string += '-----------------------\n'
            string += ' nuc  |{:>+12.5f}   |\n'
            form += (np.sum(decomp.prop_nuc),)

            string += '-----------------------\n'
            string += '-----------------------\n'
            string += ' tot  |{:>12.5f}   |\n'
            string += '-----------------------\n\n'
            form += (np.sum(decomp.prop_el[0]) + np.sum(decomp.prop_el[1]) + np.sum(decomp.prop_nuc),)

        elif decomp.prop == 'dipole':

            string += '----------------------------------------------------------------------------\n'
            string += '{:^75}\n'
            string += '{:^75}\n'
            string += '----------------------------------------------------------------------------\n'
            string += '  MO  |             electronic            |    atom(s)    |   bond length\n'
            string += '----------------------------------------------------------------------------\n'
            string += '      |     x     /     y     /     z     |\n'
            string += '----------------------------------------------------------------------------\n'
            string += '----------------------------------------------------------------------------\n'
            form += ('ground-state dipole moment', decomp.orbs,)

            for i in range(2):
                string += '----------------------------------------------------------------------------\n'
                string += '{:^75}\n'
                string += '----------------------------------------------------------------------------\n'
                form += ('alpha-spin',) if i == 0 else ('beta-spin',)
                for j in range(decomp.prop_el[i].shape[0]):
                    core = cent[i][j, 0] == cent[i][j, 1]
                    string += '  {:>2d}  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  |    {:<11s}|  {:>10s}\n'
                    form += (j, *decomp.prop_el[i][j] + 1.e-10, \
                             '{:s}{:d}'.format(mol.atom_symbol(cent[i][j, 0]), cent[i][j, 0]) if core \
                             else '{:s}{:d}-{:s}{:d}'.format(mol.atom_symbol(cent[i][j, 0]), cent[i][j, 0], \
                                                               mol.atom_symbol(cent[i][j, 1]), cent[i][j, 1]), \
                             '' if core else '{:>.6f}'. \
                             format(dist[cent[i][j, 0], cent[i][j, 1]]),)

            string += '----------------------------------------------------------------------------\n'
            string += '----------------------------------------------------------------------------\n'

            string += ' sum  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  |\n'
            form += (*(np.fromiter(map(math.fsum, decomp.prop_el[0].T), dtype=np.float64, count=3) + \
                     np.fromiter(map(math.fsum, decomp.prop_el[1].T), dtype=np.float64, count=3)) + 1.e-10,)

            string += '----------------------------------------------------------------------------\n'
            string += ' nuc  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  |\n'
            form += (*np.fromiter(map(math.fsum, decomp.prop_nuc.T), dtype=np.float64, count=3) + 1.e-10,)

            string += '----------------------------------------------------------------------------\n'
            string += '----------------------------------------------------------------------------\n'

            string += ' tot  | {:>8.3f}  / {:>8.3f}  / {:>8.3f}  |\n'
            string += '----------------------------------------------------------------------------\n\n'
            form += (*(np.fromiter(map(math.fsum, decomp.prop_el[0].T), dtype=np.float64, count=3) + \
                     np.fromiter(map(math.fsum, decomp.prop_el[1].T), dtype=np.float64, count=3) + \
                     np.fromiter(map(math.fsum, decomp.prop_nuc.T), dtype=np.float64, count=3)) + 1.e-10,)

        return string.format(*form)


def _ref(mol: gto.Mole, decomp: DecompCls) -> str:
        """
        this functions returns the correct (formatted) reference function
        """
        if decomp.ref == 'restricted':
            if mol.spin == 0:
                ref = 'RHF' if decomp.xc == '' else 'RKS'
            else:
                ref = 'ROHF' if decomp.xc == '' else 'ROKS'
        else:
            ref = 'UHF' if decomp.xc == '' else 'UKS'
        return ref




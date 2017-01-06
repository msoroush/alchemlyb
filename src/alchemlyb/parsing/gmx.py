"""Functions for processing datasets obtained from gromacs.

"""
import pandas as pd

import gromacs
from gromacs.formats import XVG


def extract_u_nk(xvg, T):
    """Return reduced potentials `u_nk` from a Hamiltonian differences XVG file.
    
    Parameters
    ----------
    xvg : str
        Path to XVG file to extract data from.
    T : float
        Temperature in Kelvin the simulations sampled.
    
    Returns
    -------
    u_nk : DataFrame
        Potential energy for each alchemical state (k) for each frame (n).
    
    """

    col_match = r"\xD\f{}H \xl\f{}"
    k_b = 8.3144621E-3
    beta = 1/(k_b * T)
    
    # extract a DataFrame from XVG data
    xvg = XVG(xvg)
    df = xvg.to_df()

    # drop duplicate columns if we (stupidly) have them
    df = df.iloc[:, ~df.columns.duplicated()]
    
    times = df[df.columns[0]]

    # want to grab only dH columns
    DHcols = [col for col in df.columns if (col_match in col)]
    dH = df[DHcols]
    
    # not entirely sure if we need to get potentials relative to
    # the state actually sampled, but perhaps needed to stack
    # samples from all states?
    U = df[df.columns[1]]

    # gromacs also gives us pV directly; need this for reduced potential
    pV = df[df.columns[-1]]

    u_k = dict()
    cols= list()
    for col in dH:
        u_col = 'u' + col.split('to')[1]
        u_k[u_col] = beta * (dH[col].values + U.values + pV.values)
        cols.append(u_col)
    
    u_k = pd.DataFrame(u_k, columns=cols, index=pd.Float64Index(times.values, name='time (ps)'))
    u_k.name = 'reduced potential'
    
    return u_k


def extract_dHdl(xvg, name='fep-lambda'):
    """Return dH/dl from a Hamiltonian differences XVG file.
    
    Parameters
    ----------
    xvg : str
        Path to XVG file to extract data from.
    name : str
        Name of dH/dl vector to pull the column for.
    
    Returns
    -------
    dH/dl : Series
        dH/dl as a function of time for this lambda window.
    
    """
    # TODO: add checking of name

    # extract a DataFrame from XVG data
    xvg = XVG(xvg)
    df = xvg.to_df()
    
    times = df[df.columns[0]]

    # want to grab only dH/dl column specified
    dHdlcols = [col for col in df.columns if (name in col)][0]
    dHdl = df[dHdlcols]
    
    dHdl = pd.Series(dHdl.values, index=pd.Float64Index(times.values, name='time (ps)'),
                     name='dH/dl')
    
    return dHdl


def generate_xvg(tpr, edr, xvg):
    """Obtain an XVG from an EDR file giving Hamiltonian differences for each window.

    Parameters
    ----------
    tpr : str
        Path to TPR file.
    edr : str 
        Path to EDR file to use.
    xvg : str
        Path for new XVG file.

    Returns
    -------
    xvg : str
        Path of new XVG file.

    """
    gromacs.energy(f=edr, s=tpr, odh=xvg)

    return xvg
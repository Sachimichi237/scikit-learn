"""Compatibility fixes for older version of python, numpy and scipy

If you add content to this file, please give the version of the package
at which the fixe is no longer needed.
"""
# Authors: Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#          Gael Varoquaux <gael.varoquaux@normalesup.org>
#          Fabian Pedregosa <fpedregosa@acm.org>
#          Lars Buitinck
#
# License: BSD 3 clause

from distutils.version import LooseVersion

import numpy as np
import scipy.sparse as sp
import scipy
import scipy.stats
from scipy.sparse.linalg import lsqr as sparse_lsqr  # noqa


def _parse_version(version_string):
    version = []
    for x in version_string.split('.'):
        try:
            version.append(int(x))
        except ValueError:
            # x may be of the form dev-1ea1592
            version.append(x)
    return tuple(version)


np_version = _parse_version(np.__version__)
sp_version = _parse_version(scipy.__version__)


if sp_version >= (1, 4):
    from scipy.sparse.linalg import lobpcg
else:
    # Backport of lobpcg functionality from scipy 1.4.0, can be removed
    # once support for sp_version < (1, 4) is dropped
    from ..externals._lobpcg import lobpcg  # noqa

if sp_version >= (1, 3):
    # Preserves earlier default choice of pinvh cutoff `cond` value.
    # Can be removed once issue #14055 is fully addressed.
    from ..externals._scipy_linalg import pinvh
else:
    from scipy.linalg import pinvh # noqa


def _object_dtype_isnan(X):
    return X != X


# TODO: replace by copy=False, when only scipy > 1.1 is supported.
def _astype_copy_false(X):
    """Returns the copy=False parameter for
    {ndarray, csr_matrix, csc_matrix}.astype when possible,
    otherwise don't specify
    """
    if sp_version >= (1, 1) or not sp.issparse(X):
        return {'copy': False}
    else:
        return {}


def _joblib_parallel_args(**kwargs):
    """Set joblib.Parallel arguments in a compatible way for 0.11 and 0.12+

    For joblib 0.11 this maps both ``prefer`` and ``require`` parameters to
    a specific ``backend``.

    Parameters
    ----------

    prefer : str in {'processes', 'threads'} or None
        Soft hint to choose the default backend if no specific backend
        was selected with the parallel_backend context manager.

    require : 'sharedmem' or None
        Hard condstraint to select the backend. If set to 'sharedmem',
        the selected backend will be single-host and thread-based even
        if the user asked for a non-thread based backend with
        parallel_backend.

    See joblib.Parallel documentation for more details
    """
    import joblib

    if joblib.__version__ >= LooseVersion('0.12'):
        return kwargs

    extra_args = set(kwargs.keys()).difference({'prefer', 'require'})
    if extra_args:
        raise NotImplementedError('unhandled arguments %s with joblib %s'
                                  % (list(extra_args), joblib.__version__))
    args = {}
    if 'prefer' in kwargs:
        prefer = kwargs['prefer']
        if prefer not in ['threads', 'processes', None]:
            raise ValueError('prefer=%s is not supported' % prefer)
        args['backend'] = {'threads': 'threading',
                           'processes': 'multiprocessing',
                           None: None}[prefer]

    if 'require' in kwargs:
        require = kwargs['require']
        if require not in [None, 'sharedmem']:
            raise ValueError('require=%s is not supported' % require)
        if require == 'sharedmem':
            args['backend'] = 'threading'
    return args


class loguniform(scipy.stats.reciprocal):
    """A class supporting log-uniform random variables.

    Parameters
    ----------
    low : float
        The minimum value
    high : float
        The maximum value

    Methods
    -------
    rvs(self, size=None, random_state=None)
        Generate log-uniform random variables

    The most useful method for Scikit-learn usage is highlighted here.
    For a full list, see
    `scipy.stats.reciprocal
    <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.reciprocal.html>`_.
    This list includes all functions of ``scipy.stats`` continuous
    distributions such as ``pdf``.

    Notes
    -----
    This class generates values between ``low`` and ``high`` or

        low <= loguniform(low, high).rvs() <= high

    The logarithmic probability density function (PDF) is uniform. When
    ``x`` is a uniformly distributed random variable between 0 and 1, ``10**x``
    are random variales that are equally likely to be returned.

    This class is an alias to ``scipy.stats.reciprocal``, which uses the
    reciprocal distribution:
    https://en.wikipedia.org/wiki/Reciprocal_distribution

    Examples
    --------

    >>> from sklearn.utils.fixes import loguniform
    >>> rv = loguniform(1e-3, 1e1)
    >>> rvs = rv.rvs(random_state=42, size=1000)
    >>> rvs.min()  # doctest: +SKIP
    0.0010435856341129003
    >>> rvs.max()  # doctest: +SKIP
    9.97403052786026
    """

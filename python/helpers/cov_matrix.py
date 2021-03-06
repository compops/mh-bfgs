###############################################################################
#    Constructing Metropolis-Hastings proposals using damped BFGS updates
#    Copyright (C) 2018  Johan Dahlin < uni (at) johandahlin [dot] com >
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
###############################################################################

"""Helpers for checking covariance matrices."""

import numpy as np
from scipy.linalg import eigh
from scipy.stats._multivariate import _eigvalsh_to_eps

def is_psd(cov_matrix):
    """ Checks if positive semi-definite matrix.

        Computes the eigenvalues and checks for negative ones.

        Args:
            cov_matrix: a matrix to be checked.

        Returns:
           True if the array is positive semi-definite and False otherwise.

    """
    # Check for NaNs or Infs
    if isinstance(cov_matrix, np.ndarray):
        if np.any(np.isinf(cov_matrix)) or np.any(np.isnan(cov_matrix)):
            return False

    return np.all(np.linalg.eigvals(cov_matrix) > 0)

def is_valid_covariance_matrix(cov_matrix):
    """ Checks if valid covariance matrix.

        Computes the eigenvalues and checks for negative ones. Also checks
        if the matrix is singular.

        Args:
            cov_matrix: a matrix to be checked.

        Returns:
           True if the array is valid covariance matrix and False otherwise.

    """

    # Check for complex elements
    if np.sum(np.where(np.iscomplex(cov_matrix))) > 0:
        return False

    # Check eigenvalues
    try:
        eig_values = eigh(cov_matrix, lower=True, check_finite=True)[0]
        eps = _eigvalsh_to_eps(eig_values, None, None)
    except ValueError:
        print(cov_matrix)
        return False

    # Singular matrix (too small eigenvalues)
    if np.min(eig_values) < -eps:
        return False
    large_eig_values = eig_values[eig_values > eps]
    if len(large_eig_values) < len(eig_values):
        return False

    # Negative eigenvalues
    if np.min(eig_values) < 0.0:
        return False

    return True

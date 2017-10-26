"""Helpers for computing Hessians using quasi-Newton."""

import numpy as np
from parameter.mcmc.quasi_newton.sr1 import sr1_estimate
from parameter.mcmc.quasi_newton.bfgs import bfgs_estimate

def quasi_newton(mcmc, prop_gradient):
    """Implements Quasi-Newton methods for Hessian estimation."""
    mem_length = mcmc.settings['qn_memory_length']
    base_hessian = mcmc.settings['base_hessian']
    strategy = mcmc.settings['qn_strategy']
    only_accepted_info = mcmc.settings['qn_only_accepted_info']
    no_params = mcmc.model.no_params_to_estimate

    # Extract parameters and gradients
    idx = range(mcmc.current_iter - mem_length, mcmc.current_iter)
    parameters = mcmc.prop_free_params[idx, :]
    gradients = mcmc.prop_grad[idx, :]
    hessians = mcmc.prop_hess[idx, :, :]
    accepted = mcmc.accepted[idx]
    target = mcmc.prop_log_prior[idx] + mcmc.prop_log_like[idx]
    target = np.concatenate(target).reshape(-1)

    # Keep only unique parameters and gradients
    if only_accepted_info:
        idx = np.where(accepted > 0)[0]

        # No available infomation, so quit
        if len(idx) is 0:
            if mcmc.settings['verbose']:
                print("Not enough samples to estimate Hessian...")
            return None, 0

        parameters = parameters[idx, :]
        gradients = gradients[idx, :]
        hessians = hessians[idx, :, :]
        target = target[idx]
        accepted = accepted[idx, :]

    # Sort and compute differences
    idx = np.argsort(target)
    parameters = parameters[idx, :]
    gradients = gradients[idx, :]
    hessians = np.matmul(hessians[idx, :], hessians[idx, :])

    param_diff = np.zeros((len(idx) - 1, no_params))
    grad_diff = np.zeros((len(idx) - 1, no_params))

    for i in range(len(idx) - 1):
        param_diff[i, :] = parameters[i+1, :] - parameters[i, :]
        grad_diff[i, :] = gradients[i+1, :] - gradients[i, :]

    initial_hessian = _init_hessian_estimate(mcmc=mcmc,
                                             prop_gradient=prop_gradient,
                                             param_diff=param_diff,
                                             grad_diff=grad_diff)

    if strategy is 'bfgs':
        return bfgs_estimate(initial_hessian=initial_hessian,
                             mcmc=mcmc,
                             param_diff=param_diff,
                             grad_diff=grad_diff)
    elif strategy is 'sr1':
        return sr1_estimate(initial_hessian=initial_hessian,
                            mcmc=mcmc,
                            param_diff=param_diff,
                            grad_diff=grad_diff)


    else:
        raise NameError("Unknown quasi-Newton algorithm selected...")

def _init_hessian_estimate(mcmc, prop_gradient, param_diff, grad_diff):
    """Implements different strategies to initialise the Hessian."""
    strategy = mcmc.settings['qn_initial_hessian']
    scaling = mcmc.settings['qn_initial_hessian_scaling']
    fixed_hessian = mcmc.settings['qn_initial_hessian_fixed']
    identity_matrix = np.diag(np.ones(mcmc.model.no_params_to_estimate))

    if strategy is 'fixed':
        return fixed_hessian

    if strategy is 'scaled_gradient':
        return identity_matrix * scaling / np.linalg.norm(prop_gradient, 2)

    if strategy is 'scaled_curvature':
        scaled_curvature = np.dot(param_diff[0], grad_diff[0])
        scaled_curvature *= np.dot(grad_diff[0], grad_diff[0])
        return identity_matrix * np.abs(scaled_curvature)

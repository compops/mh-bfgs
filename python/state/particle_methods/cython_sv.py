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

"""Particle methods."""
import numpy as np
from state.particle_methods.cython_sv_helper import bpf_sv, flps_sv
from state.base_state_inference import BaseStateInference

class ParticleMethodsCythonSV(BaseStateInference):
    """Particle methods."""

    def __init__(self, new_settings=None):
        self.name = "Particle methods (Cython implementation)"
        self.settings = {'no_particles': 100,
                         'resampling_method': 'systematic',
                         'fixed_lag': 0,
                         'initial_state': 0.0,
                         'generate_initial_state': False,
                         'estimate_gradient': False,
                         'estimate_hessian': False
                         }
        if new_settings:
            self.settings.update(new_settings)

    def filter(self, model):
        """Bootstrap particle filter for SV model."""
        self.name = "Bootstrap particle filter (Cython)"
        obs = np.array(model.obs.flatten())
        params = model.get_all_params()
        xhatf, ll, xtraj = bpf_sv(obs, mu=params[0],
                                  phi=params[1], sigmav=params[2])
        self.results.update({'filt_state_est': np.array(xhatf).reshape((model.no_obs+1, 1))})
        self.results.update({'state_trajectory': np.array(xtraj).reshape((model.no_obs+1, 1))})
        self.results.update({'log_like': ll})

    def smoother(self, model):
        """Fixed-lag particle smoother for SV model."""
        self.name = "Fixed-lag particle smoother (Cython)"
        obs = np.array(model.obs.flatten())
        params = model.get_all_params()
        xhatf, xhats, ll, gradient, xtraj = flps_sv(obs,
                                                    mu=params[0],
                                                    phi=params[1],
                                                    sigmav=params[2])

        # Compute estimate of gradient and Hessian
        gradient = np.array(gradient).reshape((model.no_params, model.no_obs+1))
        log_joint_gradient_estimate = np.sum(gradient, axis=1)

        try:
            part1 = np.mat(gradient).transpose()
            part1 = np.dot(np.mat(gradient), part1)
            part2 = np.mat(log_joint_gradient_estimate)
            part2 = np.dot(np.mat(log_joint_gradient_estimate).transpose(), part2)
            log_joint_hessian_estimate = part1 - part2 / model.no_obs
        except:
            print("Numerical problems in Segal-Weinstein estimator, returning identity.")
            log_joint_hessian_estimate = np.eye(model.no_params)

        self.results.update({'filt_state_est': np.array(xhatf).reshape((model.no_obs+1, 1))})
        self.results.update({'state_trajectory': np.array(xtraj).reshape((model.no_obs+1, 1))})
        self.results.update({'log_like': ll})
        self.results.update({'smo_state_est': np.array(xhats).reshape((model.no_obs+1, 1))})
        self.results.update({'log_joint_gradient_estimate': log_joint_gradient_estimate})
        self.results.update({'log_joint_hessian_estimate': log_joint_hessian_estimate})

        self._estimate_gradient_and_hessian(model)

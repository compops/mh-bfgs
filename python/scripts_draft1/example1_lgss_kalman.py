"""Script for reproducing example 1 in paper."""
import numpy as np
import scripts_draft1.mh2_lgss as mh
import scripts_draft1.qmh_lgss as qmh


def main(seed_offset=0):
    """Runs the experiment."""

    mh_settings = {'no_iters': 10000,
                   'no_burnin_iters': 3000,
                   'step_size': 1.0,
                   'base_hessian': np.eye(3) * 0.05**2,
                   'initial_params': (0.0, 0.1, 0.2),
                   'hessian_correction_verbose': True,
                   'qn_initial_hessian': 'scaled_gradient',
                   'qn_initial_hessian_scaling': 0.01,
                   'verbose': False,
                   'trust_region_size': None,
                   'qn_only_accepted_info': True,
                   'qn_memory_length': 20
                   }


if __name__ == '__main__':
    main()
#     sim_name = 'example1_mh2_' + str(seed_offset)
#     mh.run(new_mh_settings=mh_settings,
#            sim_name=sim_name,
#            seed_offset=seed_offset)

    mh_settings.update({'qn_strategy': 'bfgs'})
    sim_name = 'example1_qmh_bfgs_' + str(seed_offset)
    sim_desc = ('Damped BFGS for estimating Hessian. Scaling the initial ',
                'Hessian such that the gradient gives a step of 0.01. Non-PD ',
                'estimates are replaced with an empirical approximation of the ',
                'Hessian.')
#     qmh.run(new_mh_settings=mh_settings,
#             sim_name=sim_name,
#             sim_desc=sim_desc,
#             seed_offset=seed_offset)

    mh_settings.update({'qn_strategy': 'sr1',
                        'hessian_correction': 'flip'})
    sim_name = 'example1_qmh_sr1_flip_' + str(seed_offset)
    sim_desc = ('SR1 for estimating Hessian. Scaling the initial Hessian ',
                'such that the gradient gives a step of 0.01. Non-PD estimates ',
                'are corrected by flipping negative eigenvalues.')
#     qmh.run(new_mh_settings=mh_settings,
#             sim_name=sim_name,
#             sim_desc=sim_desc,
#             seed_offset=seed_offset)

    mh_settings.update({'qn_strategy': 'sr1',
                        'hessian_correction': 'replace'})
    sim_name = 'example1_qmh_sr1_hyb_' + str(seed_offset)
    sim_desc = ('SR1 for estimating Hessian. Scaling the initial Hessian ',
                'such that the gradient gives a step of 0.01. Non-PD estimates ',
                'are replaced with an empirical approximation of the Hessian.')
    qmh.run(new_mh_settings=mh_settings,
            sim_name=sim_name,
            sim_desc=sim_desc,
            seed_offset=seed_offset)

    return None

if __name__ == '__main__':
    main()

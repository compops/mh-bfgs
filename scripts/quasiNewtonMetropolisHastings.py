import numpy as np
import matplotlib.pylab as plt

from models import linearGaussianModelWithMean
from models.helpers import getInferenceModel
from state import kalmanMethods
from parameter.mcmc import metropolisHastings

def run():
    # System model
    systemModel = linearGaussianModelWithMean.model()
    systemModel.parameters['mu'] = 0.20
    systemModel.parameters['phi'] = 0.80
    systemModel.parameters['sigma_v'] = 1.0
    systemModel.parameters['sigma_e'] = 0.10
    systemModel.noObservations = 500
    systemModel.initialState = 0.0
    systemModel.generateData()

    # Inference model
    inferenceModel = getInferenceModel(systemModel, 
                                       parametersToEstimate = ('mu', 'phi', 'sigma_v'),
                                       unRestrictedParameters = True)

    # Kalman filter
    kalman = kalmanMethods.FilteringSmoothing()
    kalmanSettings = {'initialState': systemModel.initialState,
                      'initialCovariance': 1e-5,
                      'estimateGradients': True,
                      'estimateHessians': True
    }
    kalman.settings = kalmanSettings
    
    # Metropolis-Hastings
    mhSettings = {'noIters': 1000, 
                  'noBurnInIters': 200, 
                  'stepSize': 1.0, 
                  'initialParameters': (0.2, 0.8, 1.0), 
                  'verbose': False,
                  'printWarningsForUnstableSystems': False,
                  'baseStepSize': 1e-2,
                  'memoryLength': 10,
                  'initialHessian': 1e-2,
                  'trustRegionSize': 0,
                  'useDampedBFGS' : True
                  }
    mhSampler = metropolisHastings.ParameterEstimator(mhSettings)
    mhSampler.run(kalman, inferenceModel, 'qmh')
    mhSampler.plot()

    return(mhSampler)


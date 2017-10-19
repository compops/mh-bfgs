import json
import numpy as np

###############################################################################
# Load data
###############################################################################

with open('tests/dataFromRun.json') as data_file:    
    data = json.load(data_file)

allParameters = np.array(data['parameters'])
allGradients = np.array(data['gradient'])
allHessians = np.array(data['hessian'])
allAccepted = np.array(data['accepted'])
allLogPrior = np.array(data['logPrior'])
allLogLikelihood = np.array(data['logLikelihood'])

###############################################################################
# Setup BFGS update
###############################################################################
currentIteration = 20
memoryLength = 10
baseStepSize = 0.01
initialHessian = 0.01

noParameters = allParameters.shape[1]
identityMatrix = np.diag(np.ones(noParameters))

# Extract parameters and gradidents
idx = range(currentIteration - memoryLength, currentIteration)
parameters = allParameters[idx, :]
gradients = allGradients[idx, :]
hessians = allHessians[idx, :, :]
accepted = allAccepted[idx]
target = allLogPrior[idx] + allLogLikelihood[idx]

# Keep only unique parameters and gradients
idx = np.where(accepted > 0)[0]
parameters = parameters[idx, :]
gradients = gradients[idx, :]
hessians = hessians[idx, :, :]
target = np.concatenate(target[idx]).reshape(-1)    
accepted = accepted[idx, :]

# Sort and compute differences
idx = np.argsort(target)
parameters = parameters[idx, :]
gradients = gradients[idx, :]
hessians = hessians[idx, :]

parametersDiff = np.zeros((len(idx) - 1, noParameters))
gradientsDiff = np.zeros((len(idx) - 1, noParameters))

for i in range(len(idx) - 1):
    parametersDiff[i, :] = parameters[i+1, :] - parameters[i, :]
    gradientsDiff[i, :] = gradients[i+1, :] - gradients[i, :]
    print(np.dot(parametersDiff[i], gradientsDiff[i]))

inverseHessianEstimate = 0.0001 * identityMatrix
i = 4

quadraticFormSB = np.dot(np.dot(parametersDiff[i], inverseHessianEstimate), parametersDiff[i])
curvatureCondition = np.dot(parametersDiff[i], gradientsDiff[i])

term1 = (curvatureCondition + quadraticFormSB) / curvatureCondition**2
term1 *= np.outer(parametersDiff[i], parametersDiff[i])

term2 = np.dot(np.dot(inverseHessianEstimate, gradientsDiff[i]), parametersDiff[i])
term2 += np.dot(np.dot(parametersDiff[i], gradientsDiff[i]), inverseHessianEstimate)
term2 /= curvatureCondition

inverseHessianEstimate += term1 - term2
noEffectiveSamples += 1

noEffectiveSamples[currentIteration] = noEffectiveSamples
naturalGradient = np.dot(inverseHessianEstimate, proposedGradient)
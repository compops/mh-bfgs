import numpy as np
import os
from scipy.special import gammaln
import matplotlib.pylab as plt
from palettable.colorbrewer.qualitative import Dark2_8

def checkSettingsHelper(sampler):
    if not 'noIters' in sampler.settings:
        sampler.settings.update({'noIters': 1000})
        print("Missing settings: noIters, defaulting to " + str(sampler.settings['noIters']) + ".")

    if not 'noBurnInIters' in sampler.settings:
        sampler.settings.update({'noBurnInIters': 250})
        print("Missing settings: noBurnInIters, defaulting to " + str(sampler.settings['noBurnInIters']) + ".")

    if not 'stepSize' in sampler.settings:
        sampler.settings.update({'stepSize': 0.10})
        print("Missing settings: stepSize, defaulting to " + str(sampler.settings['stepSize']) + ".")      

# Print small progress reports
def printProgressReportToScreen(sampler):
    iteration = sampler.currentIteration

    print("################################################################################################ ")
    print(" Iteration: " + str(iteration + 1) + " of : " + str(sampler.settings['noIters']) + " completed.")
    print("")
    print(" Current state of the Markov chain:               ")
    print(["%.4f" % v for v in sampler.restrictedParameters[iteration - 1, :]])
    print("")
    print(" Proposed next state of the Markov chain:         ")
    print(["%.4f" % v for v in sampler.restrictedParameters[iteration, :]])
    print("")
    print(" Current posterior mean estimate: ")
    print(["%.4f" % v for v in np.mean(sampler.restrictedParameters[range(iteration), :], axis=0)])
    print("")
    print(" Current acceptance rate:                         ")
    print("%.4f" % np.mean(sampler.accepted[range(iteration)]))
    # if (sampler.iter > (sampler.nBurnIn * 1.5)):
    #     print("")
    #     print(" Current IACT values:                         ")
    #     print(["%.2f" % v for v in sampler.calcIACT()])
    #     print("")
    #     print(" Current log-SJD value:                          ")
    #     print(str(np.log(sampler.calcSJD())))
    if 'BFGS' in sampler.settings['hessianEstimate'] or 'SR1' in sampler.settings['hessianEstimate']:
        if (iteration > sampler.settings['memoryLength']):
            noEffectiveSamples = sampler.noEffectiveSamples[range(iteration)]
            idx = np.where(noEffectiveSamples > 0)
            if idx:
                print("")
                print(" Mean number of samples for Hessian estimate:           ")
                print("%.4f" % np.mean(noEffectiveSamples[idx]))
    print("################################################################################################ ")

# Check if dirs for outputs exists, otherwise create them
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


# Check if a matrix is positive semi-definite by checking for negative eigenvalues
def isPSD(x):
    return np.all(np.linalg.eigvals(x) > 0)

# Zero-variance post processing with linear correction
def zvpost_linear_prototype(sampler):
    ahat = np.zeros((sampler.nPars, sampler.nPars))
    for i in range(sampler.nPars):
        z = -0.5 * sampler.gradient[sampler.nBurnIn:sampler.nIter, :]
        g = sampler.th[sampler.nBurnIn:sampler.nIter, i]

        covAll = np.cov(np.vstack((z.transpose(), g.transpose())))
        Sigma = np.linalg.inv(covAll[0:3, 0:3])
        sigma = covAll[0:3, 3]
        ahat[:, i] = - np.dot(Sigma, sigma)
    sampler.thzv = sampler.th[sampler.nBurnIn:sampler.nIter, :] + np.dot(z, ahat)

# Logit transform
def logit(x):
    return np.log(x / (1.0 - x))

# Inverse logit transform
def invlogit(x):
    return np.exp(x) / (1.0 + np.exp(x))

def plotResults(sampler):
    noBins = int(np.floor(np.sqrt(len(sampler.results['parameterTrace'][:, 0]))))
    noParameters = sampler.settings['noParametersToEstimate']
    parameterNames = sampler.settings['parametersToEstimate']

    plt.figure()
    for i in range(noParameters):
        plt.subplot(noParameters, 2, 2 * i + 1)
        plt.hist(sampler.results['parameterTrace'][:, i], bins=noBins, color = Dark2_8.mpl_colors[i])
        plt.ylabel("Marginal posterior probability")
        plt.xlabel(parameterNames[i])
        plt.subplot(noParameters, 2, 2 * i + 2)
        plt.plot(sampler.results['parameterTrace'][:, i], color = Dark2_8.mpl_colors[i])
        plt.ylabel("Parameter trace")
        plt.xlabel(parameterNames[i])
    plt.show()


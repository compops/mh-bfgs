import numpy as np
from scipy.stats import norm

class FilteringSmoothing(object):
    className = "Kalman methods"
    settings = {}
    settings.update({'initialState': 0.0})
    settings.update({'initialCovariance': 1e-5})
    settings.update({'estimateGradients': False})
    settings.update({'estimateHessians': False})
    
    def filter(self, model):
        self.stateEstimatorType = "Kalman filter"

        predictedStateEstimate = np.zeros((model.noObservations + 1))
        predictedStateCovariance = np.zeros((model.noObservations + 1))
        filteredStateEstimate = np.zeros((model.noObservations))
        filteredStateCovariance = np.zeros((model.noObservations))
        kalmanGain = np.zeros(model.noObservations)
        logLikelihood = np.zeros(model.noObservations)

        filteredStateEstimate[0] = self.settings['initialState']
        filteredStateCovariance[0] = self.settings['initialCovariance']

        mu = model.parameters['mu']
        A = model.parameters['phi']
        Q = model.parameters['sigma_v']**2
        C = 1.0
        R = model.parameters['sigma_e']**2

        for t in range(1, model.noObservations):
            # Prediction step
            predictedStateEstimate[t] = mu + A * (filteredStateEstimate[t-1]- mu)
            predictedStateCovariance[t] = A * filteredStateCovariance[t-1] * A + Q

            # Correction step
            predictedObservationCovariance = C * predictedStateCovariance[t] * C + R
            kalmanGain[t] = predictedStateCovariance[t] * C / predictedObservationCovariance

            filteredStateEstimate[t] = predictedStateEstimate[t] + kalmanGain[t] * (model.observations[t] - C * predictedStateEstimate[t])
            filteredStateCovariance[t] = predictedStateCovariance[t] - kalmanGain[t] * C * predictedStateCovariance[t]

            logLikelihood[t] = norm.logpdf(model.observations[t], C * predictedStateEstimate[t], np.sqrt(predictedObservationCovariance))

        self.logLikelihood = np.sum(logLikelihood)
        self.filteredStateEstimate = filteredStateEstimate
        self.predictedStateEstimate = predictedStateEstimate
        self.xtraj = filteredStateEstimate
        self.predictedStateCovariance = predictedStateCovariance
        self.filteredStateCovariance = filteredStateCovariance
        self.kalmanGain = kalmanGain

    def smoother(self, model):
        self.stateEstimatorType = "Kalman smoother (RTS)"

        smootherGain = np.zeros((model.noObservations, 1))
        smoothedStateCovarianceTwoStep = np.zeros((model.noObservations, 1))
        smoothedStateEstimate = np.zeros((model.noObservations, 1))
        smoothedStateCovariance = np.zeros((model.noObservations, 1))

        mu = model.parameters['mu']
        A = model.parameters['phi']
        Q = model.parameters['sigma_v']**2
        C = 1.0
        R = model.parameters['sigma_e']**2

        # Run the preliminary Kalman filter
        self.filter(model)
        smoothedStateCovariance[model.noObservations - 1] = self.filteredStateCovariance[model.noObservations - 1]
        smoothedStateEstimate[model.noObservations - 1] = self.filteredStateEstimate[model.noObservations - 1]

        for t in range((model.noObservations - 2), 0, -1):
            smootherGain[t] = self.filteredStateCovariance[t] * A / self.predictedStateCovariance[t + 1]
            smoothedStateEstimate[t] = self.filteredStateEstimate[t] + smootherGain[t] * (smoothedStateEstimate[t + 1] - self.predictedStateEstimate[t + 1])
            smoothedStateCovariance[t] = self.filteredStateCovariance[t] + smootherGain[t] * (smoothedStateCovariance[t + 1] - self.predictedStateCovariance[t + 1]) * smootherGain[t]

        if self.settings['estimateGradients'] or self.settings['estimateHessians']:
            # Calculate the two-step smoothing covariance
            smoothedStateCovarianceTwoStep[model.noObservations - 1] = (1 - self.kalmanGain[model.noObservations - 1]) * A * self.filteredStateCovariance[model.noObservations - 1]

            for t in range((model.noObservations - 2), 0, -1):
                smoothedStateCovarianceTwoStep[t] = self.filteredStateCovariance[t] * smootherGain[t - 1] + smootherGain[t - 1] * (smoothedStateCovarianceTwoStep[t + 1] - A * self.filteredStateCovariance[t]) * smootherGain[t - 1]

            # Gradient and Hessian estimation using the Segal and Weinstein estimators
            gradientPart = np.zeros((4, model.noObservations))
            for t in range(1, model.noObservations):
                xtt = smoothedStateEstimate[t]
                xt = smoothedStateEstimate[t - 1]

                kappa = xtt * model.observations[t]
                eta = xtt * xtt + smoothedStateCovariance[t]
                eta1 = xt * xt + smoothedStateCovariance[t - 1]
                phi = xt * xtt + smoothedStateCovarianceTwoStep[t]
                px = xtt - mu - A * (xt - mu)
                
                Q1 = model.parameters['sigma_v']**(-1)
                Q2 = model.parameters['sigma_v']**(-2)
                Q3 = model.parameters['sigma_v']**(-3)
                
                gradientPart[0, t] = Q2 * px * (1.0 - A)
                gradientPart[1, t] = Q2 * (1.0 - A**2) * (phi - A * eta1 - xt * mu * (1.0 - 2.0 * A) - xtt * mu + mu**2 * (1.0 - A))
                gradientPart[2, t] = eta - 2 * A * phi + A**2 * eta1
                gradientPart[2, t] += -2.0 * (xtt - A * smoothedStateEstimate[t-1]) * (1.0 - A) * mu
                gradientPart[2, t] += mu**2 * (1.0 - A)**2
                gradientPart[2, t] = Q2 * (gradientPart[2, t]) - 1.0
                gradientPart[3, t] = 0.0
            
            gradientSum = np.sum(gradientPart, axis=1)

            if self.settings['estimateHessians']:
                hessian = np.dot(np.mat(gradientPart), np.mat(gradientPart).transpose()) - np.dot(np.mat(gradientSum).transpose(), np.mat(gradientSum)) / model.noObservations

            # Add the log-prior derivatives
            logPriorGradients = model.gradientLogPrior()
            logPriorHessian = model.hessianLogPrior()
            i = 0
            for firstParameter in logPriorGradients.keys():
                #gradientSum[i] += logPriorGradients[firstParameter]
                if self.settings['estimateHessians']:
                    j = 0                    
                    for secondParameter in logPriorGradients.keys():
                        #hessian[i, j] += logPriorHessian[firstParameter] + logPriorHessian[secondParameter]
                        j += 1
                i += 1

            gradient = {}
            gradientInternal = []
            i = 0
            for parameter in model.parameters.keys():
                if parameter in model.parametersToEstimate:
                    gradient.update({parameter: gradientSum[i]})
                    gradientInternal.append(gradientSum[i])
                i += 1

        self.smoothedStateCovariance = smoothedStateCovariance
        self.smoothedStateEstimate = smoothedStateEstimate

        if self.settings['estimateGradients'] or self.settings['estimateHessians']:
            self.gradientInternal = np.array(gradientInternal)
            self.gradient = gradient
        
        if self.settings['estimateHessians']:
            self.hessianInternal = hessian[np.ix_(model.parametersToEstimateIndex, model.parametersToEstimateIndex)]

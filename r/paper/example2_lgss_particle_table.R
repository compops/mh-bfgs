setwd("~/src/qnmh-sysid2018")
library("jsonlite")
library("xtable")
options(xtable.floating = FALSE)
options(xtable.timestamp = "")
source("r/paper/helper_table.R")

algorithms <- c("mh0pre", "mh1pre", "mh_bfgs")
bfgs_variants <- c("ignore_replace")
noSimulations <- 25
noAlgorithms <- length(algorithms) + length(bfgs_variants)

output <- array(0, dim = c(8, noSimulations, noAlgorithms))

for (i in 1:(noAlgorithms)) {
  for (j in 1:noSimulations) {

    if (i < 4) {
      algorithm <- paste("example2", paste(algorithms[i], j-1, sep="_"), sep="_")
    } else {
      algorithm <- paste(paste("example2", paste(algorithms[3], j-1, sep="_"), sep="_"), bfgs_variants[i-3], sep="_")
    }

    data <- read_json(paste("results/example2/",
                            paste(algorithm, "/data.json.gz", sep=""),
                            sep=""),
                      simplifyVector = TRUE)
    result <- read_json(paste("results/example2/",
                              paste(algorithm, "/mcmc_output.json.gz", sep=""),
                              sep=""),
                        simplifyVector = TRUE)
    settings <- read_json(paste("results/example2/",
                                paste(algorithm, "/settings.json.gz", sep=""),
                                sep=""),
                          simplifyVector = TRUE)

    output[, j, i] <- helper_table(data, result, settings)
    print(output[, j, i])
  }
}

medianOutput <- matrix(0, nrow = noAlgorithms, ncol = 6)
for (i in 1:noAlgorithms) {
  outputMethod <- matrix(as.numeric(output[-1, , i]), nrow = noSimulations, ncol = 7, byrow = TRUE)
  medianOutput[i, 1] <- median(outputMethod[, 1], na.rm = TRUE)
  medianOutput[i, 2] <- median(outputMethod[, 2], na.rm = TRUE)
  max_iact <- rep(0, noSimulations)
  for (j in 1:noSimulations) {
    max_iact[j] <- max(outputMethod[j, 3:5], na.rm = TRUE)
  }
  medianOutput[i, 3] <- median(max_iact, na.rm = TRUE)
  medianOutput[i, 4] <- IQR(max_iact, na.rm = TRUE)
  medianOutput[i, 5] <- median(outputMethod[, 6], na.rm = TRUE)
  medianOutput[i, 6] <- median(outputMethod[, 7], na.rm = TRUE)
}

medianOutput[, 1] <- round(medianOutput[, 1], 2)
medianOutput[, 2] <- round(medianOutput[, 2], 2)
medianOutput[, 3] <- round(medianOutput[, 3], 0)
medianOutput[, 4] <- round(medianOutput[, 4], 0)
medianOutput[, 5] <- round(medianOutput[, 5]*1000, 2)
medianOutput[, 6] <- round(medianOutput[, 6]*1000, 2)

row.names(medianOutput) <- c("pMH0", "pMH1", "dBFGS", "iBFGS-hyb")
xtable(medianOutput, digits = c(0, 2, 2, 0, 0, 2, 2))


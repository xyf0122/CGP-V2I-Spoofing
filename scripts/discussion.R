# Recompute supporting statistics with base R only.
# From repository root: Rscript scripts/discussion.R
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- normalizePath(file.path(dirname(script), ".."))
out <- file.path(root, "results")
f <- read.csv(file.path(out, "discussion_features.csv"))
s <- read.csv(file.path(root, "data", "survey_covariates.csv"))
d <- merge(f, s, by = "participant_id", sort = TRUE)
stopifnot(nrow(d) == 32, !anyNA(d))

# Same PCA, standardization, k-means algorithm and nstart as archived FigD_3.R.
vars <- c("t2_hat", "ttb0", "v0_mph", "a_pre", "a_post", "jerk_p95", "vmin_mph")
pca <- prcomp(d[, vars], scale. = TRUE)
set.seed(7)
km <- kmeans(pca$x[, 1:3], centers = 3, nstart = 50)
scores <- data.frame(participant_id = d$participant_id, PC1 = pca$x[,1], PC2 = pca$x[,2], cluster = km$cluster)
write.csv(scores, file.path(out, "pca_scores.csv"), row.names = FALSE)
write.csv(data.frame(component = seq_along(pca$sdev), explained_fraction = pca$sdev^2 / sum(pca$sdev^2)),
          file.path(out, "pca_variance.csv"), row.names = FALSE)
write.csv(data.frame(feature = rownames(pca$rotation), pca$rotation), file.path(out, "pca_loadings.csv"), row.names = FALSE)

# FigD_4.R uses six standardized features for its separate cluster display.
set.seed(7)
km2 <- kmeans(scale(d[, c("t2_hat", "ttb0", "v0_mph", "a_post", "jerk_p95", "vmin_mph")]), centers = 3, nstart = 50)
write.csv(data.frame(participant_id = d$participant_id, cluster = km2$cluster), file.path(out, "timing_clusters.csv"), row.names = FALSE)
fit <- lm(t2_hat ~ ttb0, data = d)
grid <- data.frame(ttb0 = seq(min(d$ttb0), max(d$ttb0), length.out = 200))
write.csv(cbind(grid, predict(fit, grid, interval = "confidence", level = .95)), file.path(out, "timing_regression.csv"), row.names = FALSE)
co <- summary(fit)$coefficients
write.csv(data.frame(term = rownames(co), co, check.names = FALSE), file.path(out, "timing_regression_coefficients.csv"), row.names = FALSE)

metrics <- c("t2_hat", "ttb0", "slack0", "v0_mph", "d0_ft", "a_pre", "a_post", "da", "jerk_p95", "vmin_mph")
blocks <- list(Demo = c("age", "gender", "yrs_drive", "days_drive"),
               Att = c("comfort_pre", "trust_pre", "purchase_pre"),
               Post = c("abnormal", "cyber_belief", "opinion_change"))
# linkET's numeric-block default selects Euclidean distances when any block
# contains a row summing to zero. Make that choice explicit and verify it.
stopifnot(any(vapply(blocks, function(cols) any(rowSums(d[, cols]) == 0), logical(1))))
# One-sided permutation test for positive distance association, 999 permutations.
# Explicit base-R RNG and ordering make the rerun deterministic; permutation
# p-values need not equal rounded values from a different package/RNG version.
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
set.seed(123)
permutations <- replicate(999, sample.int(nrow(d)))
mantel <- list()
for (block in names(blocks)) {
  dx <- as.matrix(dist(d[, blocks[[block]]], method = "euclidean"))
  lower <- lower.tri(dx)
  for (metric in metrics) {
    dy <- as.matrix(dist(d[, metric, drop = FALSE], method = "euclidean"))[lower]
    observed <- cor(dx[lower], dy)
    permuted <- apply(permutations, 2, function(p) cor(dx[p, p][lower], dy))
    pvalue <- (1 + sum(permuted >= observed - sqrt(.Machine$double.eps))) / 1000
    mantel[[length(mantel) + 1L]] <- data.frame(spec = block, env = metric, r = observed, p = pvalue, permutations = 999)
  }
}
write.csv(do.call(rbind, mantel), file.path(out, "mantel_results.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(out, "R_session_info.txt"))
cat("PCA, clustering, regression and 30 Mantel comparisons reproduced.\n")
cat("Timing regression slope:", unname(co[2,1]), "\n")

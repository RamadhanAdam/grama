# final.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.987 [0.960, 1.000] | 0.003 [-0.040, 0.049] | 0.655 | 0.655 | 0.911 |
| grama_flame | 3 | 0.905 [0.896, 0.922] | -0.078 [-0.102, -0.054] | 0.250 | 0.500 | 0.030 |
| grama_hdbscan (reference) | 3 | 0.984 [0.951, 1.000] | | | | |
| grama_norm_clip | 3 | 0.951 [0.951, 0.951] | -0.033 [-0.049, 0.000] | 0.157 | 0.472 | 0.184 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.984 [0.951, 1.000] | 0.030 [0.000, 0.049] | 0.180 | 0.539 | 0.188 |
| grama_flame | 3 | 0.926 [0.896, 0.960] | -0.028 [-0.054, 0.000] | 0.180 | 0.539 | 0.218 |
| grama_hdbscan (reference) | 3 | 0.954 [0.951, 0.960] | | | | |
| grama_norm_clip | 3 | 0.942 [0.924, 0.951] | -0.012 [-0.037, 0.000] | 0.317 | 0.539 | 0.423 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.877 [0.795, 0.948] | 0.182 [-0.002, 0.415] | 0.500 | 1.000 | 0.277 |
| grama_flame | 3 | 0.558 [0.454, 0.661] | -0.137 [-0.393, 0.000] | 0.180 | 0.539 | 0.397 |
| grama_hdbscan (reference) | 3 | 0.695 [0.472, 0.951] | | | | |
| grama_norm_clip | 3 | 0.770 [0.511, 0.948] | 0.075 [-0.002, 0.189] | 0.500 | 1.000 | 0.326 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.971 [0.951, 1.000] | 0.005 [-0.036, 0.049] | 0.750 | 0.750 | 0.857 |
| grama_flame | 3 | 0.924 [0.896, 0.957] | -0.042 [-0.054, -0.029] | 0.250 | 0.750 | 0.029 |
| grama_hdbscan (reference) | 3 | 0.966 [0.948, 1.000] | | | | |
| grama_norm_clip | 3 | 0.940 [0.922, 0.951] | -0.026 [-0.078, 0.000] | 0.317 | 0.750 | 0.423 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.669 [0.315, 0.896] | -0.244 [-0.581, -0.053] | 0.250 | 0.750 | 0.286 |
| grama_flame | 3 | 0.931 [0.892, 0.951] | 0.018 [-0.004, 0.056] | 0.750 | 0.750 | 0.440 |
| grama_hdbscan (reference) | 3 | 0.913 [0.895, 0.948] | | | | |
| grama_norm_clip | 3 | 0.814 [0.787, 0.861] | -0.099 [-0.161, -0.035] | 0.250 | 0.750 | 0.113 |


# defence.tpr: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.142 [0.108, 0.178] | 0.142 [0.108, 0.178] | 0.250 | 0.250 | 0.019 |
| grama_hdbscan (reference) | 3 | 0.000 [0.000, 0.000] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.183 [0.112, 0.225] | 0.011 [-0.025, 0.057] | 0.655 | 0.655 | 0.700 |
| grama_hdbscan (reference) | 3 | 0.172 [0.136, 0.212] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.921 [0.858, 0.970] | 0.320 [0.275, 0.378] | 0.250 | 0.250 | 0.009 |
| grama_hdbscan (reference) | 3 | 0.601 [0.583, 0.628] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.633 [0.529, 0.687] | 0.304 [0.145, 0.393] | 0.250 | 0.250 | 0.063 |
| grama_hdbscan (reference) | 3 | 0.328 [0.294, 0.384] | | | | |


# defence.fpr: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.378 [0.362, 0.398] | 0.281 [0.270, 0.290] | 0.250 | 0.250 | <0.001 |
| grama_hdbscan (reference) | 3 | 0.097 [0.072, 0.128] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.447 [0.434, 0.461] | 0.249 [0.234, 0.258] | 0.250 | 0.250 | <0.001 |
| grama_hdbscan (reference) | 3 | 0.198 [0.188, 0.207] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.339 [0.302, 0.377] | 0.168 [0.139, 0.184] | 0.250 | 0.250 | 0.007 |
| grama_hdbscan (reference) | 3 | 0.171 [0.158, 0.193] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.251 [0.241, 0.267] | 0.190 [0.176, 0.200] | 0.250 | 0.250 | 0.001 |
| grama_hdbscan (reference) | 3 | 0.061 [0.046, 0.073] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.173 [0.136, 0.212] | 0.154 [0.115, 0.187] | 0.250 | 0.250 | 0.018 |
| grama_hdbscan (reference) | 3 | 0.019 [0.011, 0.025] | | | | |


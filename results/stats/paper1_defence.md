# final.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.05  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.871 [0.742, 0.976] | 0.170 [0.039, 0.398] | 0.250 | 0.250 | 0.276 |
| grama_hdbscan (reference) | 3 | 0.701 [0.578, 0.855] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.1  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.869 [0.797, 1.000] | -0.102 [-0.203, 0.049] | 0.500 | 0.500 | 0.317 |
| grama_hdbscan (reference) | 3 | 0.971 [0.951, 1.000] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| cnn_bigru_hdbscan | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_central | 3 | 0.999 [0.998, 1.000] | -0.001 [-0.002, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_deepsight | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg+cooccurrence_edges | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg+gru_instead_of_mamba | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg+mean_pool | 3 | 0.999 [0.998, 1.000] | -0.001 [-0.002, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_fedavg+no_id_embedding | 3 | 0.965 [0.943, 0.976] | -0.035 [-0.057, -0.024] | 0.250 | 1.000 | 0.079 |
| grama_fedavg+no_residual | 3 | 0.935 [0.806, 1.000] | -0.065 [-0.194, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_fedavg+no_temporal | 3 | 0.999 [0.998, 1.000] | -0.001 [-0.002, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_flame | 5 | 0.982 [0.946, 1.000] | -0.018 [-0.054, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_foolsgold | 5 | 0.986 [0.966, 1.000] | -0.014 [-0.034, 0.000] | 0.180 | 1.000 | 0.226 |
| grama_freqfed | 5 | 0.996 [0.988, 1.000] | -0.004 [-0.012, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_hdbscan (reference) | 5 | 1.000 [1.000, 1.000] | | | | |
| grama_hdbscan_eps1 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_eps4 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_eps8 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_last_layer | 3 | 0.993 [0.978, 1.000] | -0.007 [-0.022, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_mcs2 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_mcs5 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_normalize | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_rescale | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_standardize | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_pca | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_raw | 3 | 0.993 [0.978, 1.000] | -0.007 [-0.022, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_krum | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 5 | 0.996 [0.987, 1.000] | -0.004 [-0.013, 0.000] | 0.317 | 1.000 | 0.374 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 1.0  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 100.0  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 0.317 | 0.423 |
| grama_hdbscan (reference) | 3 | 0.999 [0.998, 1.000] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.999 [0.997, 1.000] | -0.001 [-0.003, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_freqfed | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_hdbscan_eps1 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_eps4 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_eps8 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_last_layer | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_mcs2 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_mcs5 | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_normalize | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_rescale | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_standardize | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_pca | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_raw | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 1.000 [0.999, 1.000] | 0.097 [0.017, 0.187] | 0.068 | 0.562 | 0.120 |
| grama_fedavg | 5 | 1.000 [0.999, 1.000] | 0.097 [0.017, 0.187] | 0.068 | 0.562 | 0.120 |
| grama_flame | 5 | 0.920 [0.862, 0.978] | 0.017 [-0.018, 0.059] | 0.593 | 1.000 | 0.484 |
| grama_foolsgold | 5 | 1.000 [1.000, 1.000] | 0.097 [0.017, 0.187] | 0.068 | 0.562 | 0.119 |
| grama_freqfed | 5 | 0.963 [0.947, 0.983] | 0.060 [-0.026, 0.151] | 0.625 | 1.000 | 0.301 |
| grama_hdbscan (reference) | 5 | 0.903 [0.813, 0.983] | | | | |
| grama_krum | 5 | 0.974 [0.947, 0.999] | 0.072 [-0.009, 0.172] | 0.144 | 0.562 | 0.247 |
| grama_median | 5 | 0.706 [0.617, 0.816] | -0.196 [-0.276, -0.117] | 0.062 | 0.562 | 0.012 |
| grama_norm_clip | 5 | 1.000 [0.999, 1.000] | 0.097 [0.017, 0.187] | 0.068 | 0.562 | 0.120 |
| grama_trimmed_mean | 5 | 0.999 [0.997, 1.000] | 0.096 [0.016, 0.187] | 0.068 | 0.562 | 0.122 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.643 [0.443, 0.840] | 0.071 [-0.063, 0.180] | 0.438 | 1.000 | 0.345 |
| grama_fedavg | 5 | 0.778 [0.647, 0.911] | 0.205 [0.104, 0.307] | 0.062 | 1.000 | 0.026 |
| grama_flame | 5 | 0.498 [0.373, 0.607] | -0.074 [-0.136, -0.017] | 0.062 | 1.000 | 0.093 |
| grama_foolsgold | 5 | 1.000 [1.000, 1.000] | 0.428 [0.273, 0.543] | 0.062 | 1.000 | 0.006 |
| grama_freqfed | 5 | 0.554 [0.331, 0.782] | -0.019 [-0.135, 0.091] | 0.812 | 1.000 | 0.788 |
| grama_hdbscan (reference) | 5 | 0.572 [0.457, 0.727] | | | | |
| grama_hdbscan_eps1 | 3 | 0.582 [0.506, 0.732] | -0.080 [-0.129, -0.051] | 0.250 | 1.000 | 0.084 |
| grama_hdbscan_eps4 | 3 | 0.724 [0.564, 0.999] | 0.062 [0.007, 0.139] | 0.250 | 1.000 | 0.254 |
| grama_hdbscan_eps8 | 3 | 0.628 [0.415, 0.880] | -0.033 [-0.142, 0.023] | 1.000 | 1.000 | 0.603 |
| grama_hdbscan_last_layer | 3 | 0.710 [0.542, 0.933] | 0.049 [-0.024, 0.097] | 0.500 | 1.000 | 0.319 |
| grama_hdbscan_mcs2 | 3 | 0.530 [0.340, 0.684] | -0.132 [-0.225, 0.007] | 0.500 | 1.000 | 0.203 |
| grama_hdbscan_mcs5 | 3 | 0.623 [0.398, 0.933] | -0.038 [-0.167, 0.073] | 0.750 | 1.000 | 0.642 |
| grama_hdbscan_no_normalize | 3 | 0.581 [0.302, 0.820] | -0.080 [-0.264, 0.065] | 0.750 | 1.000 | 0.496 |
| grama_hdbscan_no_rescale | 3 | 0.653 [0.540, 0.792] | -0.008 [-0.069, 0.069] | 1.000 | 1.000 | 0.859 |
| grama_hdbscan_no_standardize | 3 | 0.660 [0.498, 0.933] | -0.001 [-0.068, 0.073] | 1.000 | 1.000 | 0.985 |
| grama_hdbscan_pca | 3 | 0.698 [0.446, 0.914] | 0.036 [-0.119, 0.175] | 0.750 | 1.000 | 0.711 |
| grama_hdbscan_raw | 3 | 0.559 [0.425, 0.697] | -0.102 [-0.163, -0.011] | 0.250 | 1.000 | 0.158 |
| grama_krum | 5 | 0.594 [0.406, 0.784] | 0.022 [-0.054, 0.108] | 0.812 | 1.000 | 0.673 |
| grama_median | 5 | 0.401 [0.267, 0.517] | -0.171 [-0.259, -0.078] | 0.062 | 1.000 | 0.030 |
| grama_norm_clip | 5 | 0.749 [0.599, 0.900] | 0.177 [0.087, 0.267] | 0.062 | 1.000 | 0.033 |
| grama_trimmed_mean | 5 | 0.577 [0.383, 0.792] | 0.005 [-0.099, 0.092] | 1.000 | 1.000 | 0.932 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.887 [0.661, 1.000] | 0.213 [0.000, 0.374] | 0.180 | 0.719 | 0.196 |
| grama_flame | 3 | 0.702 [0.543, 0.976] | 0.027 [-0.040, 0.145] | 1.000 | 1.000 | 0.690 |
| grama_foolsgold | 3 | 1.000 [1.000, 1.000] | 0.325 [0.000, 0.602] | 0.180 | 0.719 | 0.205 |
| grama_hdbscan (reference) | 3 | 0.675 [0.398, 1.000] | | | | |
| grama_norm_clip | 3 | 0.888 [0.814, 1.000] | 0.214 [0.000, 0.452] | 0.180 | 0.719 | 0.245 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 3 | 0.005 [0.000, 0.014] | -0.995 [-1.000, -0.986] | 0.250 | 1.000 | <0.001 |
| grama_freqfed | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 0.984 [0.951, 1.000] | -0.016 [-0.049, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.920 [0.793, 1.000] | -0.080 [-0.207, 0.000] | 0.180 | 1.000 | 0.267 |
| grama_fedavg | 5 | 0.866 [0.750, 0.983] | -0.134 [-0.250, -0.017] | 0.068 | 0.562 | 0.117 |
| grama_flame | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 5 | 0.063 [0.000, 0.182] | -0.937 [-1.000, -0.818] | 0.062 | 0.562 | <0.001 |
| grama_freqfed | 5 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 5 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 5 | 0.990 [0.970, 1.000] | -0.010 [-0.030, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_median | 5 | 0.942 [0.827, 1.000] | -0.058 [-0.173, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_norm_clip | 5 | 0.938 [0.823, 1.000] | -0.062 [-0.177, 0.000] | 0.180 | 1.000 | 0.339 |
| grama_trimmed_mean | 5 | 0.938 [0.822, 1.000] | -0.062 [-0.178, 0.000] | 0.180 | 1.000 | 0.336 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.703 [0.431, 0.942] | -0.194 [-0.467, -0.043] | 0.062 | 0.562 | 0.223 |
| grama_fedavg | 5 | 0.750 [0.600, 0.902] | -0.148 [-0.333, 0.038] | 0.273 | 1.000 | 0.257 |
| grama_flame | 5 | 0.837 [0.672, 1.000] | -0.060 [-0.239, 0.059] | 0.655 | 1.000 | 0.525 |
| grama_foolsgold | 5 | 0.030 [0.012, 0.048] | -0.868 [-0.985, -0.665] | 0.062 | 0.562 | 0.001 |
| grama_freqfed | 5 | 0.916 [0.748, 1.000] | 0.018 [0.000, 0.055] | 0.317 | 1.000 | 0.374 |
| grama_hdbscan (reference) | 5 | 0.898 [0.693, 1.000] | | | | |
| grama_krum | 5 | 0.982 [0.945, 1.000] | 0.084 [0.000, 0.252] | 0.317 | 1.000 | 0.374 |
| grama_median | 5 | 0.807 [0.591, 0.995] | -0.091 [-0.242, -0.005] | 0.068 | 0.562 | 0.295 |
| grama_norm_clip | 5 | 0.833 [0.609, 0.996] | -0.065 [-0.160, -0.004] | 0.109 | 0.653 | 0.240 |
| grama_trimmed_mean | 5 | 0.823 [0.610, 0.993] | -0.074 [-0.187, -0.007] | 0.109 | 0.653 | 0.260 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 0.929 [0.787, 1.000] | -0.071 [-0.213, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.986 [0.958, 1.000] | -0.014 [-0.042, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_fedavg | 3 | 0.911 [0.758, 1.000] | -0.089 [-0.242, 0.000] | 0.180 | 1.000 | 0.369 |
| grama_flame | 3 | 0.993 [0.980, 1.000] | -0.007 [-0.020, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_foolsgold | 3 | 0.888 [0.797, 0.971] | -0.112 [-0.203, -0.029] | 0.250 | 1.000 | 0.157 |
| grama_freqfed | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.986 [0.958, 1.000] | -0.014 [-0.042, 0.001] | 0.655 | 1.000 | 0.386 |
| grama_fedavg | 5 | 0.411 [0.174, 0.718] | -0.589 [-0.826, -0.281] | 0.062 | 0.562 | 0.017 |
| grama_flame | 5 | 0.990 [0.970, 1.000] | -0.010 [-0.030, 0.001] | 0.285 | 1.000 | 0.369 |
| grama_foolsgold | 5 | 0.573 [0.464, 0.673] | -0.427 [-0.535, -0.327] | 0.062 | 0.562 | 0.002 |
| grama_freqfed | 5 | 0.978 [0.955, 1.000] | -0.022 [-0.044, -0.000] | 0.109 | 0.762 | 0.169 |
| grama_hdbscan (reference) | 5 | 1.000 [0.999, 1.000] | | | | |
| grama_krum | 5 | 0.979 [0.936, 1.000] | -0.021 [-0.064, 0.001] | 0.655 | 1.000 | 0.382 |
| grama_median | 5 | 1.000 [0.999, 1.000] | -0.000 [-0.001, 0.001] | 0.655 | 1.000 | 0.856 |
| grama_norm_clip | 5 | 0.990 [0.970, 1.000] | -0.010 [-0.030, 0.001] | 0.655 | 1.000 | 0.391 |
| grama_trimmed_mean | 5 | 0.971 [0.912, 1.000] | -0.029 [-0.087, 0.001] | 0.285 | 1.000 | 0.372 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 1.000 [0.999, 1.000] | 0.097 [0.004, 0.254] | 0.109 | 0.870 | 0.276 |
| grama_fedavg | 5 | 0.356 [0.190, 0.512] | -0.547 [-0.797, -0.265] | 0.062 | 0.562 | 0.025 |
| grama_flame | 5 | 0.913 [0.810, 0.992] | 0.011 [-0.159, 0.179] | 0.465 | 1.000 | 0.911 |
| grama_foolsgold | 5 | 0.607 [0.487, 0.720] | -0.295 [-0.486, -0.118] | 0.125 | 0.870 | 0.047 |
| grama_freqfed | 5 | 0.933 [0.852, 1.000] | 0.031 [-0.097, 0.165] | 0.593 | 1.000 | 0.697 |
| grama_hdbscan (reference) | 5 | 0.902 [0.745, 0.996] | | | | |
| grama_krum | 5 | 0.772 [0.408, 1.000] | -0.131 [-0.542, 0.213] | 0.715 | 1.000 | 0.578 |
| grama_median | 5 | 0.834 [0.607, 0.989] | -0.069 [-0.343, 0.192] | 0.812 | 1.000 | 0.682 |
| grama_norm_clip | 5 | 1.000 [1.000, 1.000] | 0.098 [0.004, 0.255] | 0.109 | 0.870 | 0.277 |
| grama_trimmed_mean | 5 | 0.815 [0.631, 0.939] | -0.088 [-0.335, 0.164] | 0.438 | 1.000 | 0.558 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_fedavg | 3 | 1.000 [0.999, 1.000] | -0.000 [-0.001, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_flame | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan (reference) | 3 | 1.000 [1.000, 1.000] | | | | |
| grama_krum | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 0.999 [0.998, 1.000] | -0.001 [-0.002, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_norm_clip | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_fedavg | 3 | 0.999 [0.998, 1.000] | -0.000 [-0.000, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_flame | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 3 | 0.742 [0.305, 1.000] | -0.258 [-0.695, 0.000] | 0.180 | 1.000 | 0.361 |
| grama_freqfed | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan (reference) | 3 | 0.999 [0.998, 1.000] | | | | |
| grama_hdbscan_eps1 | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_eps4 | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_eps8 | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_last_layer | 3 | 0.982 [0.948, 1.000] | -0.017 [-0.052, 0.000] | 0.180 | 1.000 | 0.421 |
| grama_hdbscan_mcs2 | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_mcs5 | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_no_normalize | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_rescale | 3 | 0.999 [0.998, 1.000] | -0.000 [-0.000, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_no_standardize | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_pca | 3 | 0.999 [0.998, 1.000] | -0.001 [-0.002, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_raw | 3 | 0.997 [0.992, 1.000] | -0.003 [-0.008, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_krum | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_median | 3 | 0.993 [0.980, 1.000] | -0.006 [-0.018, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_norm_clip | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_trimmed_mean | 3 | 0.999 [0.998, 1.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.833 [0.784, 0.919] | -0.156 [-0.213, -0.074] | 0.125 | 1.000 | 0.020 |
| grama_fedavg | 5 | 0.618 [0.342, 0.876] | -0.371 [-0.648, -0.123] | 0.062 | 0.562 | 0.069 |
| grama_flame | 5 | 0.984 [0.954, 1.000] | -0.005 [-0.016, 0.001] | 0.655 | 1.000 | 0.405 |
| grama_foolsgold | 5 | 0.964 [0.936, 0.991] | -0.026 [-0.048, -0.004] | 0.312 | 1.000 | 0.105 |
| grama_freqfed | 5 | 0.999 [0.998, 1.000] | 0.009 [-0.001, 0.028] | 0.414 | 1.000 | 0.374 |
| grama_hdbscan (reference) | 5 | 0.989 [0.970, 1.000] | | | | |
| grama_krum | 5 | 0.991 [0.973, 1.000] | 0.001 [-0.027, 0.030] | 0.715 | 1.000 | 0.942 |
| grama_median | 5 | 0.928 [0.817, 0.995] | -0.062 [-0.175, 0.016] | 0.438 | 1.000 | 0.352 |
| grama_norm_clip | 5 | 0.896 [0.813, 0.970] | -0.093 [-0.177, -0.009] | 0.144 | 1.000 | 0.129 |
| grama_trimmed_mean | 5 | 0.904 [0.823, 0.984] | -0.086 [-0.169, -0.004] | 0.188 | 1.000 | 0.151 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.571 [0.301, 0.817] | -0.393 [-0.646, -0.150] | 0.062 | 1.000 | 0.052 |
| grama_fedavg | 5 | 0.564 [0.263, 0.866] | -0.400 [-0.687, -0.113] | 0.125 | 1.000 | 0.076 |
| grama_flame | 5 | 0.737 [0.499, 0.969] | -0.227 [-0.457, 0.000] | 0.144 | 1.000 | 0.170 |
| grama_foolsgold | 5 | 0.808 [0.533, 0.989] | -0.156 [-0.409, 0.000] | 0.273 | 1.000 | 0.271 |
| grama_freqfed | 5 | 0.743 [0.412, 0.981] | -0.221 [-0.540, 0.011] | 0.273 | 1.000 | 0.242 |
| grama_hdbscan (reference) | 5 | 0.964 [0.938, 0.990] | | | | |
| grama_hdbscan_eps1 | 3 | 0.969 [0.910, 1.000] | -0.013 [-0.039, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_eps4 | 3 | 0.919 [0.882, 0.948] | -0.064 [-0.074, -0.049] | 0.250 | 1.000 | 0.013 |
| grama_hdbscan_eps8 | 3 | 0.911 [0.809, 1.000] | -0.071 [-0.139, 0.000] | 0.180 | 1.000 | 0.220 |
| grama_hdbscan_last_layer | 3 | 0.558 [0.136, 0.805] | -0.425 [-0.813, -0.195] | 0.250 | 1.000 | 0.162 |
| grama_hdbscan_mcs2 | 3 | 0.993 [0.980, 1.000] | 0.011 [-0.020, 0.050] | 0.750 | 1.000 | 0.650 |
| grama_hdbscan_mcs5 | 3 | 0.859 [0.635, 0.998] | -0.123 [-0.314, 0.000] | 0.180 | 1.000 | 0.331 |
| grama_hdbscan_no_normalize | 3 | 0.765 [0.518, 0.926] | -0.217 [-0.430, -0.074] | 0.250 | 1.000 | 0.184 |
| grama_hdbscan_no_rescale | 3 | 0.742 [0.518, 0.896] | -0.240 [-0.431, -0.101] | 0.250 | 1.000 | 0.135 |
| grama_hdbscan_no_standardize | 3 | 0.991 [0.977, 1.000] | 0.009 [-0.002, 0.028] | 0.655 | 1.000 | 0.455 |
| grama_hdbscan_pca | 3 | 0.772 [0.407, 0.989] | -0.210 [-0.542, -0.011] | 0.250 | 1.000 | 0.335 |
| grama_hdbscan_raw | 3 | 0.625 [0.456, 0.868] | -0.357 [-0.544, -0.129] | 0.250 | 1.000 | 0.099 |
| grama_krum | 5 | 0.802 [0.531, 0.981] | -0.162 [-0.423, 0.006] | 0.273 | 1.000 | 0.279 |
| grama_median | 5 | 0.595 [0.305, 0.884] | -0.369 [-0.656, -0.088] | 0.125 | 1.000 | 0.086 |
| grama_norm_clip | 5 | 0.592 [0.349, 0.811] | -0.372 [-0.613, -0.156] | 0.062 | 1.000 | 0.048 |
| grama_trimmed_mean | 5 | 0.582 [0.322, 0.829] | -0.383 [-0.627, -0.138] | 0.062 | 1.000 | 0.057 |


# defence.tpr: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.000 [0.000, 0.000] | -0.014 [-0.042, 0.000] | 0.317 | 0.635 | 0.423 |
| grama_hdbscan (reference) | 3 | 0.014 [0.000, 0.042] | | | | |
| grama_krum | 3 | 0.000 [0.000, 0.000] | -0.014 [-0.042, 0.000] | 0.317 | 0.635 | 0.423 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.028 [0.000, 0.067] | 0.028 [0.000, 0.067] | 0.180 | 1.000 | 0.293 |
| grama_flame | 3 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 3 | 0.806 [0.768, 0.833] | 0.806 [0.768, 0.833] | 0.250 | 1.000 | <0.001 |
| grama_freqfed | 3 | 0.442 [0.375, 0.533] | 0.442 [0.375, 0.533] | 0.250 | 1.000 | 0.011 |
| grama_hdbscan (reference) | 3 | 0.000 [0.000, 0.000] | | | | |
| grama_hdbscan_eps1 | 3 | 0.150 [0.018, 0.217] | 0.150 [0.018, 0.217] | 0.250 | 1.000 | 0.151 |
| grama_hdbscan_eps4 | 3 | 0.023 [0.000, 0.054] | 0.023 [0.000, 0.054] | 0.180 | 1.000 | 0.277 |
| grama_hdbscan_eps8 | 3 | 0.006 [0.000, 0.017] | 0.006 [0.000, 0.017] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_last_layer | 3 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_mcs2 | 3 | 0.017 [0.000, 0.036] | 0.017 [0.000, 0.036] | 0.180 | 1.000 | 0.233 |
| grama_hdbscan_mcs5 | 3 | 0.023 [0.000, 0.054] | 0.023 [0.000, 0.054] | 0.180 | 1.000 | 0.277 |
| grama_hdbscan_no_normalize | 3 | 0.132 [0.100, 0.179] | 0.132 [0.100, 0.179] | 0.250 | 1.000 | 0.031 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_hdbscan_no_standardize | 3 | 0.067 [0.017, 0.150] | 0.067 [0.017, 0.150] | 0.250 | 1.000 | 0.247 |
| grama_hdbscan_pca | 3 | 0.023 [0.000, 0.036] | 0.023 [0.000, 0.036] | 0.180 | 1.000 | 0.184 |
| grama_hdbscan_raw | 3 | 0.012 [0.000, 0.018] | 0.012 [0.000, 0.018] | 0.180 | 1.000 | 0.184 |
| grama_krum | 3 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.039 [0.015, 0.066] | 0.039 [0.015, 0.066] | 0.068 | 0.312 | 0.055 |
| grama_flame | 5 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 1.000 | 1.000 | 1.000 |
| grama_foolsgold | 5 | 0.969 [0.961, 0.977] | 0.969 [0.961, 0.977] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.126 [0.083, 0.169] | 0.126 [0.083, 0.169] | 0.062 | 0.312 | 0.006 |
| grama_hdbscan (reference) | 5 | 0.000 [0.000, 0.000] | | | | |
| grama_krum | 5 | 0.002 [0.000, 0.007] | 0.002 [0.000, 0.007] | 0.317 | 0.635 | 0.374 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.017 [0.005, 0.028] | 0.000 [-0.029, 0.024] | 1.000 | 1.000 | 0.982 |
| grama_flame | 5 | 0.000 [0.000, 0.000] | -0.016 [-0.048, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_foolsgold | 5 | 1.000 [1.000, 1.000] | 0.984 [0.952, 1.000] | 0.062 | 1.000 | <0.001 |
| grama_freqfed | 5 | 0.133 [0.086, 0.190] | 0.117 [0.038, 0.188] | 0.125 | 1.000 | 0.048 |
| grama_hdbscan (reference) | 5 | 0.016 [0.000, 0.048] | | | | |
| grama_hdbscan_eps1 | 3 | 0.133 [0.065, 0.185] | 0.106 [0.065, 0.149] | 0.250 | 1.000 | 0.048 |
| grama_hdbscan_eps4 | 3 | 0.040 [0.000, 0.121] | 0.013 [0.000, 0.040] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_eps8 | 3 | 0.005 [0.000, 0.016] | -0.022 [-0.065, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_last_layer | 3 | 0.000 [0.000, 0.000] | -0.027 [-0.081, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_mcs2 | 3 | 0.038 [0.000, 0.113] | 0.011 [0.000, 0.032] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_mcs5 | 3 | 0.033 [0.000, 0.056] | 0.007 [-0.024, 0.044] | 0.655 | 1.000 | 0.773 |
| grama_hdbscan_no_normalize | 3 | 0.000 [0.000, 0.000] | -0.027 [-0.081, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | -0.027 [-0.081, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_hdbscan_no_standardize | 3 | 0.092 [0.000, 0.145] | 0.065 [0.000, 0.132] | 0.180 | 1.000 | 0.227 |
| grama_hdbscan_pca | 3 | 0.003 [0.000, 0.009] | -0.024 [-0.081, 0.009] | 0.655 | 1.000 | 0.488 |
| grama_hdbscan_raw | 3 | 0.000 [0.000, 0.000] | -0.027 [-0.081, 0.000] | 0.317 | 1.000 | 0.423 |
| grama_krum | 5 | 0.011 [0.008, 0.018] | -0.005 [-0.031, 0.008] | 0.625 | 1.000 | 0.730 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.326 [0.250, 0.429] | 0.291 [0.233, 0.339] | 0.250 | 0.500 | 0.011 |
| grama_foolsgold | 3 | 0.362 [0.304, 0.450] | 0.327 [0.214, 0.433] | 0.250 | 0.500 | 0.036 |
| grama_hdbscan (reference) | 3 | 0.035 [0.000, 0.089] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.168 [0.129, 0.244] | 0.154 [0.113, 0.236] | 0.250 | 0.500 | 0.063 |
| grama_foolsgold | 3 | 0.985 [0.956, 1.000] | 0.971 [0.939, 0.992] | 0.250 | 0.500 | <0.001 |
| grama_hdbscan (reference) | 3 | 0.014 [0.008, 0.018] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.900 [0.833, 0.963] | 0.207 [0.074, 0.417] | 0.250 | 0.500 | 0.191 |
| grama_hdbscan (reference) | 3 | 0.693 [0.417, 0.889] | | | | |
| grama_krum | 3 | 0.758 [0.375, 0.963] | 0.065 [-0.042, 0.161] | 0.500 | 0.500 | 0.387 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.023 [0.000, 0.050] | -0.675 [-0.767, -0.625] | 0.250 | 1.000 | 0.005 |
| grama_flame | 3 | 0.858 [0.817, 0.917] | 0.160 [0.133, 0.196] | 0.250 | 1.000 | 0.014 |
| grama_foolsgold | 3 | 0.079 [0.000, 0.200] | -0.619 [-0.767, -0.483] | 0.250 | 1.000 | 0.017 |
| grama_freqfed | 3 | 0.852 [0.833, 0.867] | 0.155 [0.100, 0.214] | 0.250 | 1.000 | 0.043 |
| grama_hdbscan (reference) | 3 | 0.698 [0.643, 0.767] | | | | |
| grama_krum | 3 | 0.743 [0.696, 0.783] | 0.046 [-0.017, 0.100] | 0.500 | 1.000 | 0.311 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.002 [0.000, 0.007] | -0.608 [-0.669, -0.545] | 0.062 | 0.312 | <0.001 |
| grama_flame | 5 | 0.662 [0.629, 0.684] | 0.051 [-0.009, 0.120] | 0.438 | 0.438 | 0.244 |
| grama_foolsgold | 5 | 0.160 [0.070, 0.231] | -0.451 [-0.522, -0.385] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.721 [0.699, 0.746] | 0.111 [0.037, 0.187] | 0.125 | 0.375 | 0.066 |
| grama_hdbscan (reference) | 5 | 0.611 [0.545, 0.670] | | | | |
| grama_krum | 5 | 0.654 [0.587, 0.720] | 0.043 [0.005, 0.080] | 0.188 | 0.375 | 0.126 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.037 [0.008, 0.079] | -0.412 [-0.533, -0.291] | 0.062 | 0.312 | 0.004 |
| grama_flame | 5 | 0.545 [0.514, 0.578] | 0.096 [-0.055, 0.246] | 0.465 | 0.930 | 0.341 |
| grama_foolsgold | 5 | 0.195 [0.122, 0.276] | -0.254 [-0.445, -0.083] | 0.125 | 0.375 | 0.069 |
| grama_freqfed | 5 | 0.566 [0.532, 0.597] | 0.117 [-0.029, 0.264] | 0.625 | 0.930 | 0.243 |
| grama_hdbscan (reference) | 5 | 0.449 [0.316, 0.582] | | | | |
| grama_krum | 5 | 0.568 [0.478, 0.658] | 0.119 [0.053, 0.173] | 0.068 | 0.312 | 0.026 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.342 [0.323, 0.370] | -0.539 [-0.677, -0.458] | 0.250 | 0.359 | 0.016 |
| grama_hdbscan (reference) | 3 | 0.881 [0.792, 1.000] | | | | |
| grama_krum | 3 | 0.986 [0.958, 1.000] | 0.105 [0.000, 0.167] | 0.180 | 0.359 | 0.185 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.084 [0.036, 0.167] | -0.800 [-0.933, -0.717] | 0.250 | 1.000 | 0.007 |
| grama_flame | 3 | 0.250 [0.183, 0.317] | -0.634 [-0.700, -0.536] | 0.250 | 1.000 | 0.006 |
| grama_foolsgold | 3 | 0.040 [0.017, 0.067] | -0.844 [-0.917, -0.750] | 0.250 | 1.000 | 0.003 |
| grama_freqfed | 3 | 0.250 [0.250, 0.250] | -0.634 [-0.733, -0.536] | 0.250 | 1.000 | 0.008 |
| grama_hdbscan (reference) | 3 | 0.884 [0.786, 0.983] | | | | |
| grama_krum | 3 | 0.937 [0.929, 0.950] | 0.053 [-0.050, 0.143] | 0.500 | 1.000 | 0.443 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.094 [0.081, 0.107] | -0.718 [-0.750, -0.698] | 0.062 | 0.312 | <0.001 |
| grama_flame | 5 | 0.319 [0.287, 0.349] | -0.493 [-0.545, -0.449] | 0.062 | 0.312 | <0.001 |
| grama_foolsgold | 5 | 0.095 [0.057, 0.130] | -0.718 [-0.767, -0.669] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.322 [0.294, 0.362] | -0.490 [-0.532, -0.437] | 0.062 | 0.312 | <0.001 |
| grama_hdbscan (reference) | 5 | 0.813 [0.798, 0.832] | | | | |
| grama_krum | 5 | 0.783 [0.733, 0.811] | -0.030 [-0.081, 0.007] | 0.625 | 0.625 | 0.305 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.115 [0.101, 0.134] | -0.597 [-0.667, -0.536] | 0.062 | 0.312 | <0.001 |
| grama_flame | 5 | 0.346 [0.305, 0.386] | -0.366 [-0.468, -0.268] | 0.062 | 0.312 | 0.003 |
| grama_foolsgold | 5 | 0.075 [0.048, 0.108] | -0.636 [-0.704, -0.569] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.318 [0.286, 0.349] | -0.393 [-0.479, -0.321] | 0.062 | 0.312 | <0.001 |
| grama_hdbscan (reference) | 5 | 0.712 [0.652, 0.774] | | | | |
| grama_krum | 5 | 0.703 [0.680, 0.735] | -0.009 [-0.047, 0.041] | 0.625 | 0.625 | 0.757 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.834 [0.778, 0.917] | 0.236 [-0.065, 0.625] | 0.500 | 0.500 | 0.366 |
| grama_hdbscan (reference) | 3 | 0.597 [0.292, 0.871] | | | | |
| grama_krum | 3 | 0.761 [0.417, 0.963] | 0.164 [0.032, 0.333] | 0.250 | 0.500 | 0.208 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.012 [0.000, 0.036] | -0.563 [-0.700, -0.383] | 0.250 | 1.000 | 0.027 |
| grama_flame | 3 | 0.802 [0.700, 0.857] | 0.227 [0.150, 0.317] | 0.250 | 1.000 | 0.043 |
| grama_foolsgold | 3 | 0.328 [0.250, 0.400] | -0.248 [-0.393, 0.017] | 0.500 | 1.000 | 0.202 |
| grama_freqfed | 3 | 0.833 [0.750, 0.900] | 0.258 [0.107, 0.467] | 0.250 | 1.000 | 0.139 |
| grama_hdbscan (reference) | 3 | 0.575 [0.383, 0.700] | | | | |
| grama_hdbscan_eps1 | 3 | 0.830 [0.817, 0.857] | 0.255 [0.117, 0.433] | 0.250 | 1.000 | 0.113 |
| grama_hdbscan_eps4 | 3 | 0.565 [0.383, 0.661] | -0.011 [-0.050, 0.018] | 0.655 | 1.000 | 0.650 |
| grama_hdbscan_eps8 | 3 | 0.382 [0.217, 0.500] | -0.194 [-0.214, -0.167] | 0.250 | 1.000 | 0.005 |
| grama_hdbscan_last_layer | 3 | 0.173 [0.117, 0.268] | -0.403 [-0.583, -0.250] | 0.250 | 1.000 | 0.054 |
| grama_hdbscan_mcs2 | 3 | 0.615 [0.533, 0.696] | 0.040 [-0.083, 0.150] | 0.750 | 1.000 | 0.614 |
| grama_hdbscan_mcs5 | 3 | 0.716 [0.650, 0.767] | 0.141 [0.067, 0.267] | 0.250 | 1.000 | 0.156 |
| grama_hdbscan_no_normalize | 3 | 0.218 [0.117, 0.321] | -0.357 [-0.483, -0.267] | 0.250 | 1.000 | 0.032 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | -0.575 [-0.700, -0.383] | 0.250 | 1.000 | 0.027 |
| grama_hdbscan_no_standardize | 3 | 0.621 [0.567, 0.679] | 0.045 [-0.133, 0.233] | 0.750 | 1.000 | 0.711 |
| grama_hdbscan_pca | 3 | 0.524 [0.350, 0.650] | -0.052 [-0.071, -0.033] | 0.250 | 1.000 | 0.043 |
| grama_hdbscan_raw | 3 | 0.085 [0.067, 0.100] | -0.490 [-0.633, -0.283] | 0.250 | 1.000 | 0.044 |
| grama_krum | 3 | 0.694 [0.650, 0.717] | 0.118 [0.017, 0.267] | 0.250 | 1.000 | 0.259 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.007 [0.000, 0.021] | -0.557 [-0.671, -0.432] | 0.062 | 0.312 | 0.001 |
| grama_flame | 5 | 0.662 [0.625, 0.725] | 0.098 [-0.003, 0.199] | 0.312 | 0.938 | 0.168 |
| grama_foolsgold | 5 | 0.459 [0.403, 0.516] | -0.104 [-0.275, 0.067] | 0.312 | 0.938 | 0.352 |
| grama_freqfed | 5 | 0.675 [0.649, 0.705] | 0.112 [0.016, 0.224] | 0.062 | 0.312 | 0.134 |
| grama_hdbscan (reference) | 5 | 0.563 [0.434, 0.680] | | | | |
| grama_krum | 5 | 0.608 [0.535, 0.682] | 0.045 [-0.040, 0.113] | 0.465 | 0.938 | 0.358 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.031 [0.000, 0.083] | -0.385 [-0.513, -0.256] | 0.062 | 1.000 | 0.008 |
| grama_flame | 5 | 0.515 [0.452, 0.588] | 0.100 [0.002, 0.198] | 0.144 | 1.000 | 0.152 |
| grama_foolsgold | 5 | 0.625 [0.542, 0.708] | 0.210 [0.027, 0.355] | 0.125 | 1.000 | 0.095 |
| grama_freqfed | 5 | 0.517 [0.459, 0.587] | 0.101 [0.006, 0.198] | 0.144 | 1.000 | 0.140 |
| grama_hdbscan (reference) | 5 | 0.416 [0.306, 0.534] | | | | |
| grama_hdbscan_eps1 | 3 | 0.610 [0.252, 0.851] | 0.175 [0.024, 0.282] | 0.250 | 1.000 | 0.152 |
| grama_hdbscan_eps4 | 3 | 0.283 [0.122, 0.421] | -0.151 [-0.211, -0.106] | 0.250 | 1.000 | 0.040 |
| grama_hdbscan_eps8 | 3 | 0.108 [0.089, 0.122] | -0.326 [-0.518, -0.106] | 0.250 | 1.000 | 0.113 |
| grama_hdbscan_last_layer | 3 | 0.022 [0.016, 0.026] | -0.412 [-0.605, -0.211] | 0.250 | 1.000 | 0.069 |
| grama_hdbscan_mcs2 | 3 | 0.442 [0.260, 0.632] | 0.008 [-0.008, 0.033] | 0.655 | 1.000 | 0.579 |
| grama_hdbscan_mcs5 | 3 | 0.364 [0.122, 0.518] | -0.071 [-0.114, 0.008] | 0.500 | 1.000 | 0.215 |
| grama_hdbscan_no_normalize | 3 | 0.108 [0.033, 0.161] | -0.326 [-0.500, -0.195] | 0.250 | 1.000 | 0.069 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | -0.434 [-0.632, -0.228] | 0.250 | 1.000 | 0.065 |
| grama_hdbscan_no_standardize | 3 | 0.449 [0.293, 0.588] | 0.015 [-0.044, 0.065] | 0.750 | 1.000 | 0.681 |
| grama_hdbscan_pca | 3 | 0.217 [0.106, 0.371] | -0.217 [-0.456, -0.073] | 0.250 | 1.000 | 0.214 |
| grama_hdbscan_raw | 3 | 0.040 [0.000, 0.113] | -0.394 [-0.632, -0.220] | 0.250 | 1.000 | 0.085 |
| grama_krum | 5 | 0.450 [0.277, 0.612] | 0.034 [-0.071, 0.139] | 0.812 | 1.000 | 0.615 |


# defence.fpr: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.05  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_hdbscan (reference) | 3 | 0.292 [0.267, 0.317] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.1  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_hdbscan (reference) | 3 | 0.228 [0.213, 0.250] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_hdbscan | 3 | 0.158 [0.127, 0.190] | -0.006 [-0.030, 0.040] | 1.000 | 1.000 | 0.830 |
| grama_deepsight | 5 | 0.089 [0.054, 0.125] | -0.093 [-0.121, -0.068] | 0.062 | 1.000 | 0.004 |
| grama_flame | 5 | 0.343 [0.333, 0.352] | 0.161 [0.139, 0.183] | 0.062 | 1.000 | <0.001 |
| grama_foolsgold | 5 | 0.425 [0.331, 0.499] | 0.243 [0.141, 0.325] | 0.062 | 1.000 | 0.009 |
| grama_freqfed | 5 | 0.319 [0.293, 0.341] | 0.137 [0.110, 0.165] | 0.062 | 1.000 | <0.001 |
| grama_hdbscan (reference) | 5 | 0.182 [0.159, 0.205] | | | | |
| grama_hdbscan_eps1 | 3 | 0.321 [0.300, 0.340] | 0.158 [0.140, 0.183] | 0.250 | 1.000 | 0.007 |
| grama_hdbscan_eps4 | 3 | 0.120 [0.103, 0.133] | -0.043 [-0.050, -0.033] | 0.250 | 1.000 | 0.014 |
| grama_hdbscan_eps8 | 3 | 0.067 [0.047, 0.080] | -0.097 [-0.110, -0.077] | 0.250 | 1.000 | 0.011 |
| grama_hdbscan_last_layer | 3 | 0.132 [0.113, 0.153] | -0.031 [-0.070, -0.003] | 0.250 | 1.000 | 0.261 |
| grama_hdbscan_mcs2 | 3 | 0.187 [0.180, 0.197] | 0.023 [-0.003, 0.040] | 0.500 | 1.000 | 0.225 |
| grama_hdbscan_mcs5 | 3 | 0.186 [0.157, 0.200] | 0.022 [0.007, 0.043] | 0.250 | 1.000 | 0.179 |
| grama_hdbscan_no_normalize | 3 | 0.083 [0.060, 0.110] | -0.080 [-0.103, -0.047] | 0.250 | 1.000 | 0.043 |
| grama_hdbscan_no_rescale | 3 | 0.008 [0.000, 0.023] | -0.156 [-0.183, -0.133] | 0.250 | 1.000 | 0.009 |
| grama_hdbscan_no_standardize | 3 | 0.279 [0.253, 0.300] | 0.116 [0.070, 0.143] | 0.250 | 1.000 | 0.037 |
| grama_hdbscan_pca | 3 | 0.146 [0.120, 0.167] | -0.018 [-0.033, 0.010] | 0.500 | 1.000 | 0.330 |
| grama_hdbscan_raw | 3 | 0.053 [0.040, 0.073] | -0.110 [-0.143, -0.077] | 0.250 | 1.000 | 0.029 |
| grama_krum | 5 | 0.300 [0.300, 0.300] | 0.118 [0.095, 0.141] | 0.062 | 1.000 | <0.001 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 1.0  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_hdbscan (reference) | 3 | 0.188 [0.183, 0.193] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 100.0  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_hdbscan (reference) | 3 | 0.177 [0.133, 0.223] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.418 [0.406, 0.439] | 0.217 [0.181, 0.238] | 0.250 | 0.500 | 0.007 |
| grama_hdbscan (reference) | 3 | 0.202 [0.179, 0.225] | | | | |
| grama_krum | 3 | 0.330 [0.326, 0.335] | 0.128 [0.101, 0.150] | 0.250 | 0.500 | 0.012 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.077 [0.062, 0.086] | -0.239 [-0.308, -0.196] | 0.250 | 1.000 | 0.021 |
| grama_flame | 3 | 0.457 [0.425, 0.475] | 0.141 [0.054, 0.192] | 0.250 | 1.000 | 0.084 |
| grama_foolsgold | 3 | 0.212 [0.164, 0.254] | -0.105 [-0.154, -0.025] | 0.250 | 1.000 | 0.121 |
| grama_freqfed | 3 | 0.307 [0.283, 0.324] | -0.010 [-0.058, 0.025] | 1.000 | 1.000 | 0.731 |
| grama_hdbscan (reference) | 3 | 0.316 [0.279, 0.371] | | | | |
| grama_hdbscan_eps1 | 3 | 0.495 [0.471, 0.508] | 0.178 [0.137, 0.225] | 0.250 | 1.000 | 0.020 |
| grama_hdbscan_eps4 | 3 | 0.224 [0.196, 0.250] | -0.093 [-0.121, -0.074] | 0.250 | 1.000 | 0.023 |
| grama_hdbscan_eps8 | 3 | 0.195 [0.179, 0.212] | -0.122 [-0.158, -0.100] | 0.250 | 1.000 | 0.022 |
| grama_hdbscan_last_layer | 3 | 0.166 [0.164, 0.167] | -0.151 [-0.204, -0.113] | 0.250 | 1.000 | 0.032 |
| grama_hdbscan_mcs2 | 3 | 0.291 [0.263, 0.332] | -0.025 [-0.092, 0.033] | 0.750 | 1.000 | 0.558 |
| grama_hdbscan_mcs5 | 3 | 0.250 [0.204, 0.283] | -0.066 [-0.088, -0.037] | 0.250 | 1.000 | 0.049 |
| grama_hdbscan_no_normalize | 3 | 0.234 [0.213, 0.250] | -0.083 [-0.121, -0.042] | 0.250 | 1.000 | 0.069 |
| grama_hdbscan_no_rescale | 3 | 0.115 [0.033, 0.200] | -0.201 [-0.266, -0.079] | 0.250 | 1.000 | 0.081 |
| grama_hdbscan_no_standardize | 3 | 0.387 [0.329, 0.438] | 0.070 [-0.042, 0.158] | 0.500 | 1.000 | 0.355 |
| grama_hdbscan_pca | 3 | 0.180 [0.167, 0.200] | -0.137 [-0.171, -0.113] | 0.250 | 1.000 | 0.016 |
| grama_hdbscan_raw | 3 | 0.268 [0.230, 0.304] | -0.048 [-0.100, 0.025] | 0.500 | 1.000 | 0.329 |
| grama_krum | 3 | 0.373 [0.369, 0.375] | 0.057 [0.004, 0.096] | 0.250 | 1.000 | 0.174 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.104 [0.087, 0.126] | -0.325 [-0.355, -0.295] | 0.062 | 0.312 | <0.001 |
| grama_flame | 5 | 0.492 [0.484, 0.498] | 0.063 [0.033, 0.092] | 0.062 | 0.312 | 0.022 |
| grama_foolsgold | 5 | 0.243 [0.194, 0.290] | -0.186 [-0.247, -0.129] | 0.062 | 0.312 | 0.005 |
| grama_freqfed | 5 | 0.400 [0.376, 0.421] | -0.029 [-0.060, 0.003] | 0.144 | 0.312 | 0.189 |
| grama_hdbscan (reference) | 5 | 0.429 [0.398, 0.460] | | | | |
| grama_krum | 5 | 0.433 [0.423, 0.441] | 0.004 [-0.028, 0.036] | 0.812 | 0.812 | 0.836 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.125 [0.102, 0.147] | -0.413 [-0.476, -0.354] | 0.062 | 1.000 | <0.001 |
| grama_flame | 5 | 0.516 [0.475, 0.550] | -0.021 [-0.102, 0.053] | 0.812 | 1.000 | 0.659 |
| grama_foolsgold | 5 | 0.260 [0.199, 0.321] | -0.278 [-0.408, -0.167] | 0.062 | 1.000 | 0.017 |
| grama_freqfed | 5 | 0.389 [0.337, 0.435] | -0.149 [-0.221, -0.082] | 0.062 | 1.000 | 0.022 |
| grama_hdbscan (reference) | 5 | 0.538 [0.472, 0.616] | | | | |
| grama_hdbscan_eps1 | 3 | 0.732 [0.683, 0.774] | 0.207 [0.129, 0.254] | 0.250 | 1.000 | 0.034 |
| grama_hdbscan_eps4 | 3 | 0.390 [0.222, 0.514] | -0.134 [-0.278, -0.006] | 0.250 | 1.000 | 0.232 |
| grama_hdbscan_eps8 | 3 | 0.425 [0.375, 0.486] | -0.100 [-0.140, -0.034] | 0.250 | 1.000 | 0.095 |
| grama_hdbscan_last_layer | 3 | 0.289 [0.193, 0.384] | -0.235 [-0.307, -0.136] | 0.250 | 1.000 | 0.045 |
| grama_hdbscan_mcs2 | 3 | 0.421 [0.328, 0.486] | -0.104 [-0.226, -0.034] | 0.250 | 1.000 | 0.233 |
| grama_hdbscan_mcs5 | 3 | 0.403 [0.360, 0.469] | -0.121 [-0.194, -0.051] | 0.250 | 1.000 | 0.099 |
| grama_hdbscan_no_normalize | 3 | 0.525 [0.430, 0.642] | 0.000 [-0.124, 0.142] | 1.000 | 1.000 | 0.996 |
| grama_hdbscan_no_rescale | 3 | 0.315 [0.295, 0.333] | -0.209 [-0.220, -0.203] | 0.250 | 1.000 | <0.001 |
| grama_hdbscan_no_standardize | 3 | 0.630 [0.568, 0.672] | 0.106 [0.068, 0.153] | 0.250 | 1.000 | 0.051 |
| grama_hdbscan_pca | 3 | 0.276 [0.194, 0.373] | -0.249 [-0.360, -0.147] | 0.250 | 1.000 | 0.057 |
| grama_hdbscan_raw | 3 | 0.526 [0.415, 0.656] | 0.002 [-0.085, 0.102] | 1.000 | 1.000 | 0.976 |
| grama_krum | 5 | 0.502 [0.488, 0.516] | -0.036 [-0.109, 0.030] | 0.438 | 1.000 | 0.422 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.326 [0.299, 0.362] | 0.119 [0.078, 0.158] | 0.250 | 0.500 | 0.036 |
| grama_foolsgold | 3 | 0.261 [0.192, 0.308] | 0.054 [-0.012, 0.113] | 0.500 | 0.500 | 0.276 |
| grama_hdbscan (reference) | 3 | 0.207 [0.196, 0.221] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack alie_noisy, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.353 [0.344, 0.369] | 0.062 [-0.051, 0.129] | 0.500 | 1.000 | 0.389 |
| grama_foolsgold | 3 | 0.285 [0.193, 0.333] | -0.006 [-0.068, 0.113] | 1.000 | 1.000 | 0.931 |
| grama_hdbscan (reference) | 3 | 0.291 [0.215, 0.395] | | | | |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.270 [0.257, 0.282] | 0.124 [0.072, 0.152] | 0.250 | 0.500 | 0.041 |
| grama_hdbscan (reference) | 3 | 0.146 [0.119, 0.185] | | | | |
| grama_krum | 3 | 0.252 [0.227, 0.293] | 0.105 [0.099, 0.109] | 0.250 | 0.500 | <0.001 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.052 [0.029, 0.086] | -0.043 [-0.079, -0.016] | 0.250 | 1.000 | 0.149 |
| grama_flame | 3 | 0.215 [0.163, 0.267] | 0.120 [0.054, 0.192] | 0.250 | 1.000 | 0.094 |
| grama_foolsgold | 3 | 0.764 [0.679, 0.833] | 0.668 [0.604, 0.725] | 0.250 | 1.000 | 0.003 |
| grama_freqfed | 3 | 0.204 [0.175, 0.229] | 0.109 [0.067, 0.154] | 0.250 | 1.000 | 0.050 |
| grama_hdbscan (reference) | 3 | 0.095 [0.075, 0.108] | | | | |
| grama_krum | 3 | 0.192 [0.179, 0.209] | 0.097 [0.079, 0.107] | 0.250 | 1.000 | 0.008 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.052 [0.034, 0.071] | -0.025 [-0.047, -0.004] | 0.125 | 0.312 | 0.115 |
| grama_flame | 5 | 0.155 [0.140, 0.171] | 0.078 [0.050, 0.108] | 0.062 | 0.312 | 0.010 |
| grama_foolsgold | 5 | 0.727 [0.645, 0.798] | 0.650 [0.577, 0.714] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.148 [0.126, 0.167] | 0.071 [0.037, 0.099] | 0.062 | 0.312 | 0.016 |
| grama_hdbscan (reference) | 5 | 0.077 [0.062, 0.092] | | | | |
| grama_krum | 5 | 0.143 [0.113, 0.168] | 0.066 [0.047, 0.080] | 0.062 | 0.312 | 0.003 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack label_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.061 [0.037, 0.085] | 0.016 [-0.021, 0.053] | 0.438 | 0.438 | 0.504 |
| grama_flame | 5 | 0.156 [0.133, 0.174] | 0.111 [0.089, 0.133] | 0.062 | 0.312 | <0.001 |
| grama_foolsgold | 5 | 0.713 [0.648, 0.766] | 0.668 [0.604, 0.729] | 0.062 | 0.312 | <0.001 |
| grama_freqfed | 5 | 0.162 [0.124, 0.200] | 0.117 [0.089, 0.152] | 0.062 | 0.312 | 0.003 |
| grama_hdbscan (reference) | 5 | 0.045 [0.028, 0.076] | | | | |
| grama_krum | 5 | 0.115 [0.059, 0.173] | 0.070 [0.025, 0.128] | 0.068 | 0.312 | 0.080 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.323 [0.320, 0.326] | 0.223 [0.197, 0.250] | 0.250 | 0.500 | 0.005 |
| grama_hdbscan (reference) | 3 | 0.099 [0.072, 0.123] | | | | |
| grama_krum | 3 | 0.231 [0.219, 0.243] | 0.132 [0.097, 0.170] | 0.250 | 0.500 | 0.025 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.091 [0.083, 0.104] | 0.033 [0.021, 0.041] | 0.250 | 1.000 | 0.034 |
| grama_flame | 3 | 0.323 [0.321, 0.325] | 0.265 [0.254, 0.279] | 0.250 | 1.000 | <0.001 |
| grama_foolsgold | 3 | 0.044 [0.037, 0.053] | -0.014 [-0.029, 0.008] | 0.500 | 1.000 | 0.344 |
| grama_freqfed | 3 | 0.338 [0.317, 0.367] | 0.280 [0.254, 0.300] | 0.250 | 1.000 | 0.002 |
| grama_hdbscan (reference) | 3 | 0.058 [0.045, 0.067] | | | | |
| grama_krum | 3 | 0.145 [0.138, 0.156] | 0.087 [0.071, 0.111] | 0.250 | 1.000 | 0.019 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.118 [0.088, 0.149] | 0.066 [0.026, 0.107] | 0.062 | 0.312 | 0.050 |
| grama_flame | 5 | 0.327 [0.307, 0.344] | 0.274 [0.245, 0.303] | 0.062 | 0.312 | <0.001 |
| grama_foolsgold | 5 | 0.057 [0.037, 0.079] | 0.004 [-0.020, 0.028] | 1.000 | 1.000 | 0.769 |
| grama_freqfed | 5 | 0.313 [0.301, 0.326] | 0.261 [0.241, 0.282] | 0.062 | 0.312 | <0.001 |
| grama_hdbscan (reference) | 5 | 0.052 [0.031, 0.073] | | | | |
| grama_krum | 5 | 0.085 [0.066, 0.105] | 0.033 [0.001, 0.054] | 0.125 | 0.312 | 0.116 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack magnitude_poison, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.130 [0.089, 0.171] | 0.114 [0.076, 0.151] | 0.062 | 0.312 | 0.006 |
| grama_flame | 5 | 0.346 [0.323, 0.365] | 0.330 [0.308, 0.344] | 0.062 | 0.312 | <0.001 |
| grama_foolsgold | 5 | 0.053 [0.041, 0.066] | 0.037 [0.024, 0.051] | 0.062 | 0.312 | 0.009 |
| grama_freqfed | 5 | 0.351 [0.336, 0.368] | 0.335 [0.318, 0.356] | 0.062 | 0.312 | <0.001 |
| grama_hdbscan (reference) | 5 | 0.016 [0.010, 0.023] | | | | |
| grama_krum | 5 | 0.019 [0.010, 0.030] | 0.003 [-0.011, 0.015] | 0.715 | 0.715 | 0.709 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.1, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_flame | 3 | 0.256 [0.238, 0.271] | 0.108 [0.088, 0.138] | 0.250 | 0.500 | 0.019 |
| grama_hdbscan (reference) | 3 | 0.148 [0.134, 0.159] | | | | |
| grama_krum | 3 | 0.252 [0.230, 0.290] | 0.104 [0.084, 0.130] | 0.250 | 0.500 | 0.017 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.2, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 3 | 0.073 [0.046, 0.096] | -0.026 [-0.029, -0.021] | 0.250 | 1.000 | 0.010 |
| grama_flame | 3 | 0.202 [0.197, 0.208] | 0.102 [0.090, 0.125] | 0.250 | 1.000 | 0.012 |
| grama_foolsgold | 3 | 0.449 [0.246, 0.590] | 0.350 [0.171, 0.484] | 0.250 | 1.000 | 0.064 |
| grama_freqfed | 3 | 0.222 [0.217, 0.225] | 0.123 [0.100, 0.150] | 0.250 | 1.000 | 0.014 |
| grama_hdbscan (reference) | 3 | 0.099 [0.075, 0.117] | | | | |
| grama_hdbscan_eps1 | 3 | 0.235 [0.208, 0.287] | 0.135 [0.092, 0.180] | 0.250 | 1.000 | 0.034 |
| grama_hdbscan_eps4 | 3 | 0.047 [0.025, 0.067] | -0.052 [-0.057, -0.050] | 0.250 | 1.000 | 0.002 |
| grama_hdbscan_eps8 | 3 | 0.025 [0.017, 0.033] | -0.075 [-0.083, -0.058] | 0.250 | 1.000 | 0.012 |
| grama_hdbscan_last_layer | 3 | 0.093 [0.078, 0.108] | -0.007 [-0.029, 0.017] | 0.750 | 1.000 | 0.656 |
| grama_hdbscan_mcs2 | 3 | 0.077 [0.071, 0.082] | -0.022 [-0.046, 0.004] | 0.500 | 1.000 | 0.267 |
| grama_hdbscan_mcs5 | 3 | 0.108 [0.096, 0.119] | 0.008 [-0.008, 0.021] | 0.500 | 1.000 | 0.440 |
| grama_hdbscan_no_normalize | 3 | 0.043 [0.025, 0.054] | -0.057 [-0.062, -0.050] | 0.250 | 1.000 | 0.004 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | -0.099 [-0.117, -0.075] | 0.250 | 1.000 | 0.016 |
| grama_hdbscan_no_standardize | 3 | 0.123 [0.083, 0.158] | 0.023 [0.008, 0.042] | 0.250 | 1.000 | 0.137 |
| grama_hdbscan_pca | 3 | 0.084 [0.071, 0.100] | -0.015 [-0.025, -0.004] | 0.250 | 1.000 | 0.126 |
| grama_hdbscan_raw | 3 | 0.022 [0.008, 0.046] | -0.077 [-0.098, -0.062] | 0.250 | 1.000 | 0.019 |
| grama_krum | 3 | 0.204 [0.196, 0.212] | 0.105 [0.096, 0.121] | 0.250 | 1.000 | 0.006 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.3, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.066 [0.047, 0.085] | 0.002 [-0.029, 0.034] | 1.000 | 1.000 | 0.933 |
| grama_flame | 5 | 0.171 [0.143, 0.198] | 0.106 [0.058, 0.153] | 0.062 | 0.312 | 0.017 |
| grama_foolsgold | 5 | 0.286 [0.172, 0.401] | 0.222 [0.107, 0.336] | 0.062 | 0.312 | 0.031 |
| grama_freqfed | 5 | 0.174 [0.149, 0.196] | 0.110 [0.069, 0.149] | 0.062 | 0.312 | 0.011 |
| grama_hdbscan (reference) | 5 | 0.065 [0.044, 0.085] | | | | |
| grama_krum | 5 | 0.163 [0.130, 0.192] | 0.098 [0.079, 0.114] | 0.062 | 0.312 | <0.001 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, attack targeted_flip, fraction 0.4, alpha 0.5  (reference: grama_hdbscan)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| grama_deepsight | 5 | 0.132 [0.079, 0.181] | 0.064 [0.005, 0.123] | 0.312 | 1.000 | 0.137 |
| grama_flame | 5 | 0.184 [0.145, 0.209] | 0.116 [0.074, 0.159] | 0.062 | 1.000 | 0.009 |
| grama_foolsgold | 5 | 0.298 [0.230, 0.383] | 0.230 [0.146, 0.315] | 0.062 | 1.000 | 0.008 |
| grama_freqfed | 5 | 0.176 [0.130, 0.209] | 0.107 [0.062, 0.150] | 0.062 | 1.000 | 0.014 |
| grama_hdbscan (reference) | 5 | 0.068 [0.027, 0.119] | | | | |
| grama_hdbscan_eps1 | 3 | 0.167 [0.068, 0.362] | 0.097 [0.043, 0.198] | 0.250 | 1.000 | 0.193 |
| grama_hdbscan_eps4 | 3 | 0.024 [0.006, 0.056] | -0.045 [-0.107, -0.011] | 0.250 | 1.000 | 0.287 |
| grama_hdbscan_eps8 | 3 | 0.017 [0.000, 0.040] | -0.052 [-0.124, -0.016] | 0.250 | 1.000 | 0.281 |
| grama_hdbscan_last_layer | 3 | 0.123 [0.028, 0.277] | 0.054 [0.011, 0.113] | 0.250 | 1.000 | 0.218 |
| grama_hdbscan_mcs2 | 3 | 0.060 [0.022, 0.136] | -0.009 [-0.028, 0.006] | 0.750 | 1.000 | 0.450 |
| grama_hdbscan_mcs5 | 3 | 0.071 [0.011, 0.181] | 0.002 [-0.006, 0.017] | 1.000 | 1.000 | 0.818 |
| grama_hdbscan_no_normalize | 3 | 0.045 [0.040, 0.051] | -0.025 [-0.113, 0.023] | 1.000 | 1.000 | 0.632 |
| grama_hdbscan_no_rescale | 3 | 0.000 [0.000, 0.000] | -0.069 [-0.164, -0.017] | 0.250 | 1.000 | 0.281 |
| grama_hdbscan_no_standardize | 3 | 0.080 [0.006, 0.181] | 0.011 [-0.011, 0.027] | 0.500 | 1.000 | 0.445 |
| grama_hdbscan_pca | 3 | 0.028 [0.011, 0.051] | -0.041 [-0.113, -0.005] | 0.250 | 1.000 | 0.368 |
| grama_hdbscan_raw | 3 | 0.007 [0.000, 0.017] | -0.062 [-0.147, -0.017] | 0.250 | 1.000 | 0.284 |
| grama_krum | 5 | 0.200 [0.088, 0.319] | 0.131 [0.056, 0.207] | 0.062 | 1.000 | 0.045 |


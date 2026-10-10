# final.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source can_train_test, data_file cantt_set_01_b0e5a072.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.991 [0.990, 0.992] | 0.036 [0.026, 0.046] | 0.062 | 0.250 | 0.003 |
| gcn_gru_central | 5 | 0.926 [0.916, 0.936] | -0.029 [-0.041, -0.015] | 0.062 | 0.250 | 0.016 |
| gcn_ids_central | 5 | 0.916 [0.910, 0.922] | -0.039 [-0.051, -0.029] | 0.062 | 0.250 | 0.003 |
| grama_central (reference) | 5 | 0.955 [0.946, 0.965] | | | | |
| transformer_ids_central | 5 | 0.983 [0.975, 0.988] | 0.029 [0.020, 0.037] | 0.062 | 0.250 | 0.005 |

## data_source can_train_test, data_file cantt_set_02_1f30f4c2.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.942 [0.922, 0.958] | 0.081 [0.041, 0.129] | 0.062 | 0.250 | 0.029 |
| gcn_gru_central | 5 | 0.787 [0.755, 0.819] | -0.074 [-0.142, -0.006] | 0.188 | 0.375 | 0.129 |
| gcn_ids_central | 5 | 0.848 [0.832, 0.863] | -0.013 [-0.055, 0.029] | 0.812 | 0.812 | 0.631 |
| grama_central (reference) | 5 | 0.861 [0.820, 0.897] | | | | |
| transformer_ids_central | 5 | 0.926 [0.914, 0.942] | 0.065 [0.032, 0.096] | 0.062 | 0.250 | 0.023 |

## data_source can_train_test, data_file cantt_set_03_a39d5b2c.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.721 [0.602, 0.843] | -0.092 [-0.210, -0.012] | 0.125 | 0.500 | 0.197 |
| gcn_gru_central | 5 | 0.838 [0.739, 0.896] | 0.025 [-0.030, 0.119] | 0.812 | 1.000 | 0.610 |
| gcn_ids_central | 5 | 0.882 [0.875, 0.889] | 0.069 [-0.026, 0.165] | 0.812 | 1.000 | 0.288 |
| grama_central (reference) | 5 | 0.812 [0.711, 0.911] | | | | |
| transformer_ids_central | 5 | 0.832 [0.791, 0.873] | 0.020 [-0.091, 0.146] | 1.000 | 1.000 | 0.780 |

## data_source can_train_test, data_file cantt_set_04_8ab7bf20.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.946 [0.935, 0.956] | 0.111 [0.053, 0.169] | 0.062 | 0.250 | 0.031 |
| gcn_gru_central | 5 | 0.748 [0.708, 0.786] | -0.087 [-0.164, -0.027] | 0.062 | 0.250 | 0.092 |
| gcn_ids_central | 5 | 0.764 [0.722, 0.806] | -0.071 [-0.132, -0.005] | 0.125 | 0.250 | 0.109 |
| grama_central (reference) | 5 | 0.835 [0.774, 0.887] | | | | |
| transformer_ids_central | 5 | 0.900 [0.884, 0.910] | 0.065 [0.022, 0.108] | 0.125 | 0.250 | 0.062 |

## data_source real, data_file cic_iov2024_1427a6ad.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| gcn_gru_central | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| gcn_ids_central | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |
| grama_central (reference) | 3 | 0.999 [0.998, 1.000] | | | | |
| transformer_ids_central | 3 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.002] | 0.317 | 1.000 | 0.423 |

## data_source road, data_file road_0bc0ca64.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 10 | 0.736 [0.695, 0.777] | -0.223 [-0.263, -0.178] | 0.002 | 0.031* | <0.001 |
| cnn_bigru_fedavg | 5 | 0.477 [0.314, 0.635] | -0.473 [-0.641, -0.304] | 0.062 | 0.750 | 0.009 |
| gcn_gru_central | 10 | 0.499 [0.441, 0.552] | -0.460 [-0.523, -0.406] | 0.002 | 0.031* | <0.001 |
| gcn_gru_fedavg | 5 | 0.207 [0.187, 0.225] | -0.743 [-0.793, -0.698] | 0.062 | 0.750 | <0.001 |
| gcn_ids_central | 10 | 0.547 [0.513, 0.580] | -0.412 [-0.453, -0.369] | 0.002 | 0.031* | <0.001 |
| gcn_ids_fedavg | 5 | 0.177 [0.148, 0.208] | -0.773 [-0.832, -0.714] | 0.062 | 0.750 | <0.001 |
| grama_central (reference) | 10 | 0.959 [0.938, 0.978] | | | | |
| grama_central+cooccurrence_edges | 5 | 0.757 [0.613, 0.877] | -0.193 [-0.352, -0.056] | 0.062 | 0.750 | 0.085 |
| grama_central+gru_instead_of_mamba | 5 | 0.810 [0.711, 0.901] | -0.140 [-0.263, -0.021] | 0.125 | 0.750 | 0.109 |
| grama_central+mean_pool | 5 | 0.930 [0.909, 0.954] | -0.020 [-0.059, 0.017] | 0.438 | 1.000 | 0.437 |
| grama_central+no_id_embedding | 5 | 0.773 [0.757, 0.789] | -0.177 [-0.223, -0.131] | 0.062 | 0.750 | 0.003 |
| grama_central+no_residual | 5 | 0.977 [0.970, 0.984] | 0.027 [-0.010, 0.064] | 0.438 | 1.000 | 0.268 |
| grama_central+no_temporal | 5 | 0.964 [0.942, 0.987] | 0.015 [-0.018, 0.061] | 0.812 | 1.000 | 0.555 |
| grama_central+one_head | 5 | 0.972 [0.956, 0.988] | 0.023 [-0.003, 0.059] | 0.312 | 1.000 | 0.275 |
| grama_fedavg | 5 | 0.723 [0.580, 0.818] | -0.226 [-0.390, -0.114] | 0.062 | 0.750 | 0.049 |
| transformer_ids_central | 10 | 0.795 [0.757, 0.837] | -0.164 [-0.212, -0.112] | 0.004 | 0.051 | <0.001 |
| transformer_ids_fedavg | 5 | 0.747 [0.723, 0.766] | -0.202 [-0.259, -0.150] | 0.062 | 0.750 | 0.003 |


# tests.masquerade.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source road, data_file road_0bc0ca64.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 10 | 0.702 [0.655, 0.752] | -0.252 [-0.305, -0.196] | 0.002 | 0.031* | <0.001 |
| cnn_bigru_fedavg | 5 | 0.476 [0.349, 0.581] | -0.465 [-0.597, -0.333] | 0.062 | 0.750 | 0.004 |
| gcn_gru_central | 10 | 0.531 [0.474, 0.582] | -0.424 [-0.481, -0.375] | 0.002 | 0.031* | <0.001 |
| gcn_gru_fedavg | 5 | 0.230 [0.210, 0.246] | -0.711 [-0.764, -0.658] | 0.062 | 0.750 | <0.001 |
| gcn_ids_central | 10 | 0.567 [0.536, 0.600] | -0.388 [-0.426, -0.337] | 0.002 | 0.031* | <0.001 |
| gcn_ids_fedavg | 5 | 0.194 [0.156, 0.239] | -0.747 [-0.819, -0.674] | 0.062 | 0.750 | <0.001 |
| grama_central (reference) | 10 | 0.955 [0.929, 0.977] | | | | |
| grama_central+cooccurrence_edges | 5 | 0.728 [0.602, 0.849] | -0.212 [-0.361, -0.063] | 0.125 | 0.750 | 0.068 |
| grama_central+gru_instead_of_mamba | 5 | 0.809 [0.682, 0.918] | -0.132 [-0.285, 0.016] | 0.312 | 0.938 | 0.190 |
| grama_central+mean_pool | 5 | 0.930 [0.899, 0.961] | -0.010 [-0.041, 0.034] | 0.625 | 0.938 | 0.679 |
| grama_central+no_id_embedding | 5 | 0.762 [0.740, 0.784] | -0.178 [-0.231, -0.121] | 0.062 | 0.750 | 0.006 |
| grama_central+no_residual | 5 | 0.980 [0.976, 0.985] | 0.040 [-0.002, 0.081] | 0.188 | 0.938 | 0.175 |
| grama_central+no_temporal | 5 | 0.966 [0.945, 0.986] | 0.026 [-0.013, 0.080] | 0.438 | 0.938 | 0.407 |
| grama_central+one_head | 5 | 0.982 [0.959, 0.997] | 0.042 [0.001, 0.088] | 0.188 | 0.938 | 0.165 |
| grama_fedavg | 5 | 0.722 [0.623, 0.789] | -0.218 [-0.346, -0.121] | 0.062 | 0.750 | 0.025 |
| transformer_ids_central | 10 | 0.687 [0.637, 0.740] | -0.267 [-0.331, -0.201] | 0.002 | 0.031* | <0.001 |
| transformer_ids_fedavg | 5 | 0.583 [0.542, 0.624] | -0.357 [-0.439, -0.275] | 0.062 | 0.750 | 0.002 |


# tests.unknown_vehicle.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source can_train_test, data_file cantt_set_01_b0e5a072.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.245 [0.199, 0.338] | 0.045 [-0.004, 0.140] | 0.655 | 0.655 | 0.391 |
| gcn_gru_central | 5 | 0.232 [0.199, 0.277] | 0.032 [0.000, 0.074] | 0.109 | 0.435 | 0.200 |
| gcn_ids_central | 5 | 0.286 [0.201, 0.373] | 0.086 [0.002, 0.170] | 0.109 | 0.435 | 0.162 |
| grama_central (reference) | 5 | 0.200 [0.199, 0.203] | | | | |
| transformer_ids_central | 5 | 0.357 [0.245, 0.469] | 0.157 [0.045, 0.269] | 0.109 | 0.435 | 0.078 |

## data_source can_train_test, data_file cantt_set_02_1f30f4c2.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.191 [0.191, 0.191] | -0.063 [-0.189, 0.000] | 0.317 | 1.000 | 0.374 |
| gcn_gru_central | 5 | 0.191 [0.191, 0.191] | -0.063 [-0.189, 0.000] | 0.317 | 1.000 | 0.374 |
| gcn_ids_central | 5 | 0.191 [0.191, 0.191] | -0.063 [-0.189, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_central (reference) | 5 | 0.254 [0.191, 0.380] | | | | |
| transformer_ids_central | 5 | 0.191 [0.191, 0.191] | -0.063 [-0.189, 0.000] | 0.317 | 1.000 | 0.374 |

## data_source can_train_test, data_file cantt_set_03_a39d5b2c.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.372 [0.305, 0.492] | -0.019 [-0.138, 0.081] | 1.000 | 1.000 | 0.766 |
| gcn_gru_central | 5 | 0.350 [0.305, 0.423] | -0.041 [-0.136, 0.012] | 1.000 | 1.000 | 0.425 |
| gcn_ids_central | 5 | 0.305 [0.305, 0.305] | -0.086 [-0.194, 0.000] | 0.285 | 0.855 | 0.196 |
| grama_central (reference) | 5 | 0.391 [0.305, 0.499] | | | | |
| transformer_ids_central | 5 | 0.309 [0.294, 0.328] | -0.082 [-0.186, -0.005] | 0.068 | 0.272 | 0.188 |

## data_source can_train_test, data_file cantt_set_04_8ab7bf20.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.214 [0.214, 0.214] | -0.071 [-0.179, 0.001] | 0.285 | 1.000 | 0.246 |
| gcn_gru_central | 5 | 0.216 [0.214, 0.219] | -0.070 [-0.178, 0.004] | 0.465 | 1.000 | 0.259 |
| gcn_ids_central | 5 | 0.214 [0.214, 0.214] | -0.071 [-0.179, 0.001] | 0.273 | 1.000 | 0.245 |
| grama_central (reference) | 5 | 0.286 [0.214, 0.394] | | | | |
| transformer_ids_central | 5 | 0.214 [0.214, 0.214] | -0.071 [-0.179, 0.001] | 0.285 | 1.000 | 0.246 |


# tests.unknown_attack.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source can_train_test, data_file cantt_set_01_b0e5a072.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.478 [0.473, 0.483] | 0.019 [-0.023, 0.060] | 0.312 | 1.000 | 0.477 |
| gcn_gru_central | 5 | 0.475 [0.448, 0.507] | 0.016 [-0.013, 0.036] | 0.438 | 1.000 | 0.345 |
| gcn_ids_central | 5 | 0.453 [0.438, 0.466] | -0.006 [-0.034, 0.022] | 0.812 | 1.000 | 0.739 |
| grama_central (reference) | 5 | 0.459 [0.420, 0.500] | | | | |
| transformer_ids_central | 5 | 0.492 [0.452, 0.537] | 0.033 [-0.040, 0.106] | 0.625 | 1.000 | 0.471 |

## data_source can_train_test, data_file cantt_set_02_1f30f4c2.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.470 [0.462, 0.483] | -0.114 [-0.318, 0.004] | 0.625 | 0.875 | 0.319 |
| gcn_gru_central | 5 | 0.915 [0.862, 0.958] | 0.331 [0.139, 0.453] | 0.125 | 0.500 | 0.025 |
| gcn_ids_central | 5 | 0.678 [0.558, 0.802] | 0.094 [-0.013, 0.196] | 0.188 | 0.562 | 0.191 |
| grama_central (reference) | 5 | 0.584 [0.465, 0.785] | | | | |
| transformer_ids_central | 5 | 0.558 [0.457, 0.756] | -0.027 [-0.325, 0.282] | 0.438 | 0.875 | 0.876 |

## data_source can_train_test, data_file cantt_set_03_a39d5b2c.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.471 [0.442, 0.499] | -0.093 [-0.161, -0.039] | 0.062 | 0.250 | 0.066 |
| gcn_gru_central | 5 | 0.443 [0.441, 0.445] | -0.121 [-0.172, -0.094] | 0.062 | 0.250 | 0.009 |
| gcn_ids_central | 5 | 0.544 [0.537, 0.554] | -0.020 [-0.064, 0.005] | 0.812 | 0.812 | 0.417 |
| grama_central (reference) | 5 | 0.564 [0.537, 0.617] | | | | |
| transformer_ids_central | 5 | 0.511 [0.483, 0.531] | -0.053 [-0.101, -0.015] | 0.062 | 0.250 | 0.091 |

## data_source can_train_test, data_file cantt_set_04_8ab7bf20.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.906 [0.896, 0.917] | 0.015 [-0.012, 0.041] | 0.625 | 0.938 | 0.393 |
| gcn_gru_central | 5 | 0.902 [0.890, 0.916] | 0.010 [-0.017, 0.037] | 0.438 | 0.938 | 0.568 |
| gcn_ids_central | 5 | 0.919 [0.916, 0.922] | 0.027 [0.008, 0.046] | 0.125 | 0.500 | 0.069 |
| grama_central (reference) | 5 | 0.892 [0.873, 0.911] | | | | |
| transformer_ids_central | 5 | 0.905 [0.888, 0.919] | 0.014 [-0.004, 0.035] | 0.312 | 0.938 | 0.299 |


# tests.unknown_vehicle_and_attack.f1_macro: mean with 95% bootstrap interval, difference to the reference, paired tests

Differences are method minus reference, paired on the seed. `*` marks a Holm-adjusted Wilcoxon p below 0.05. At n = 5 the smallest possible Wilcoxon p is 0.0625, so no `*` can appear; read the interval of the difference.

## data_source can_train_test, data_file cantt_set_01_b0e5a072.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.475 [0.263, 0.686] | 0.116 [-0.232, 0.429] | 0.812 | 1.000 | 0.589 |
| gcn_gru_central | 5 | 0.346 [0.185, 0.508] | -0.013 [-0.097, 0.067] | 0.438 | 1.000 | 0.792 |
| gcn_ids_central | 5 | 0.465 [0.306, 0.607] | 0.106 [-0.034, 0.277] | 0.625 | 1.000 | 0.303 |
| grama_central (reference) | 5 | 0.359 [0.162, 0.581] | | | | |
| transformer_ids_central | 5 | 0.427 [0.226, 0.629] | 0.068 [-0.273, 0.350] | 0.438 | 1.000 | 0.729 |

## data_source can_train_test, data_file cantt_set_02_1f30f4c2.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.139 [0.139, 0.139] | -0.062 [-0.186, 0.000] | 0.317 | 1.000 | 0.374 |
| gcn_gru_central | 5 | 0.139 [0.139, 0.139] | -0.062 [-0.186, 0.000] | 0.317 | 1.000 | 0.374 |
| gcn_ids_central | 5 | 0.139 [0.139, 0.139] | -0.062 [-0.186, 0.000] | 0.317 | 1.000 | 0.374 |
| grama_central (reference) | 5 | 0.201 [0.139, 0.325] | | | | |
| transformer_ids_central | 5 | 0.139 [0.139, 0.139] | -0.062 [-0.186, 0.000] | 0.317 | 1.000 | 0.374 |

## data_source can_train_test, data_file cantt_set_03_a39d5b2c.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.333 [0.281, 0.436] | -0.006 [-0.086, 0.068] | 1.000 | 1.000 | 0.892 |
| gcn_gru_central | 5 | 0.331 [0.281, 0.431] | -0.008 [-0.086, 0.063] | 1.000 | 1.000 | 0.858 |
| gcn_ids_central | 5 | 0.281 [0.281, 0.281] | -0.058 [-0.116, 0.000] | 0.285 | 0.855 | 0.179 |
| grama_central (reference) | 5 | 0.339 [0.281, 0.397] | | | | |
| transformer_ids_central | 5 | 0.280 [0.277, 0.281] | -0.059 [-0.117, -0.001] | 0.144 | 0.577 | 0.167 |

## data_source can_train_test, data_file cantt_set_04_8ab7bf20.pt, alpha 0.5  (reference: grama_central)

| Method | n | Mean [95% CI] | Difference [95% CI] | Wilcoxon p | Holm p | t-test p |
|---|---|---|---|---|---|---|
| cnn_bigru_central | 5 | 0.374 [0.374, 0.374] | -0.004 [-0.016, 0.004] | 0.715 | 1.000 | 0.564 |
| gcn_gru_central | 5 | 0.367 [0.356, 0.374] | -0.011 [-0.022, 0.000] | 0.144 | 0.577 | 0.168 |
| gcn_ids_central | 5 | 0.374 [0.374, 0.374] | -0.004 [-0.016, 0.004] | 0.715 | 1.000 | 0.563 |
| grama_central (reference) | 5 | 0.378 [0.371, 0.390] | | | | |
| transformer_ids_central | 5 | 0.374 [0.374, 0.374] | -0.004 [-0.016, 0.004] | 0.715 | 1.000 | 0.564 |


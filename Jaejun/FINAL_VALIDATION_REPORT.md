# FINAL PERFORMANCE AUDIT

| module            |      auc |   pr_auc |    brier |       ece |   accuracy |   sensitivity |   specificity |   precision |       f1 |   calibration_intercept |   calibration_slope |
|:------------------|---------:|---------:|---------:|----------:|-----------:|--------------:|--------------:|------------:|---------:|------------------------:|--------------------:|
| habitual_mini_ffq | 0.87664  | 0.75043  | 0.105712 | 0.025422  |   0.779911 |      0.832065 |      0.760863 |    0.62309  | 0.664764 |               0.252052  |            1.07671  |
| lifestyle_service | 0.664521 | 0.620465 | 0.190603 | 0.0231817 |   0.640749 |      0.607031 |      0.629572 |    0.593568 | 0.587614 |              -0.0434601 |            0.860338 |

## Subgroup summary

| module            | subgroup_type   | subgroup   |      auc |   pr_auc |     brier |
|:------------------|:----------------|:-----------|---------:|---------:|----------:|
| habitual_mini_ffq | age             | 19-29      | 0.892085 | 0.765588 | 0.103656  |
| habitual_mini_ffq | age             | 30-39      | 0.873145 | 0.714507 | 0.101455  |
| habitual_mini_ffq | age             | 40-49      | 0.879712 | 0.753674 | 0.103758  |
| habitual_mini_ffq | age             | 50-64      | 0.864472 | 0.740686 | 0.111396  |
| habitual_mini_ffq | sex             | female     | 0.8636   | 0.734256 | 0.114027  |
| habitual_mini_ffq | sex             | male       | 0.887709 | 0.766332 | 0.0925364 |
| lifestyle_service | age             | 19-29      | 0.62787  | 0.666663 | 0.187164  |
| lifestyle_service | age             | 30-49      | 0.640342 | 0.604285 | 0.18861   |
| lifestyle_service | age             | 50-64      | 0.63868  | 0.555545 | 0.193907  |
| lifestyle_service | age             | 65+        | 0.664009 | 0.614003 | 0.190496  |
| lifestyle_service | sex             | female     | 0.64851  | 0.63122  | 0.197629  |
| lifestyle_service | sex             | male       | 0.640275 | 0.561302 | 0.181242  |
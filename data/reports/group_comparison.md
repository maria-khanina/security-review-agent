### All five policies

| Variant | Recall at 2 false alarms per document, mean over the policies (95% interval) | v1 to v3 | v4 | v5 | v6 | v7 | Own decisions: recall / precision / false alarms per document | Prompt tokens |
|---|---|---|---|---|---|---|---|---|
| A raw | 0.53 (0.47 to 0.58) | 0.31 | 0.58 | 0.65 | 0.44 | 0.69 | 0.51 / 0.55 / 2.56 | 14,031 |
| A + layer without wording | 0.61 (0.57 to 0.66) | 0.27 | 0.65 | 0.75 | 0.59 | 0.79 | 0.58 / 0.47 / 4.02 | 14,031 |
| A + layer, wording per requirement | 0.62 (0.57 to 0.65) | 0.22 | 0.64 | 0.73 | 0.65 | 0.85 | 0.59 / 0.46 / 4.36 | 14,031 |
| A layer only, no model call | 0.44 (0.38 to 0.50) | 0.14 | 0.45 | 0.34 | 0.56 | 0.70 | 0.39 / 0.35 / 4.38 | 0 |
| A cascade, 40% of the pairs | 0.56 (0.50 to 0.61) | 0.22 | 0.64 | 0.51 | 0.60 | 0.83 | 0.48 / 0.44 / 3.72 | 5,612 |
| B raw | 0.54 (0.50 to 0.57) | 0.40 | 0.60 | 0.56 | 0.44 | 0.69 | 0.46 / 0.58 / 2.01 | 16,742 |
| B + layer without wording | 0.58 (0.54 to 0.63) | 0.33 | 0.66 | 0.57 | 0.51 | 0.84 | 0.61 / 0.46 / 4.43 | 16,742 |
| B + layer, wording per requirement | 0.57 (0.54 to 0.62) | 0.23 | 0.71 | 0.55 | 0.48 | 0.89 | 0.60 / 0.42 / 5.03 | 16,742 |
| C raw | 0.55 (0.49 to 0.60) | 0.34 | 0.55 | 0.74 | 0.45 | 0.68 | 0.74 / 0.53 / 4.10 | 14,381 |
| C + layer without wording | 0.64 (0.60 to 0.69) | 0.34 | 0.67 | 0.80 | 0.63 | 0.78 | 0.56 / 0.55 / 2.87 | 14,381 |
| C + layer, wording per requirement | 0.65 (0.59 to 0.68) | 0.26 | 0.69 | 0.82 | 0.66 | 0.85 | 0.60 / 0.50 / 3.69 | 14,381 |
| D raw | 0.51 (0.47 to 0.57) | 0.43 | 0.48 | 0.58 | 0.38 | 0.66 | 0.61 / 0.55 / 3.11 | 17,092 |
| D + layer without wording | 0.62 (0.57 to 0.66) | 0.29 | 0.72 | 0.66 | 0.58 | 0.85 | 0.57 / 0.49 / 3.70 | 17,092 |
| D + layer, wording per requirement | 0.62 (0.58 to 0.65) | 0.23 | 0.71 | 0.66 | 0.64 | 0.84 | 0.58 / 0.46 / 4.28 | 17,092 |
| D cascade, 40% of the pairs | 0.54 (0.50 to 0.59) | 0.24 | 0.63 | 0.45 | 0.57 | 0.83 | 0.49 / 0.46 / 3.50 | 6,837 |

Best mean recall: C + layer, wording per requirement

| Variant | Difference to the best | 95% interval |
|---|---|---|
| A raw | -0.109 | -0.162 to -0.053 |
| A + layer without wording | -0.020 | -0.057 to +0.016 |
| A + layer, wording per requirement | -0.022 | -0.054 to +0.016 |
| A layer only, no model call | -0.200 | -0.250 to -0.137 |
| A cascade, 40% of the pairs | -0.074 | -0.123 to -0.026 |
| B raw | -0.101 | -0.154 to -0.045 |
| B + layer without wording | -0.052 | -0.088 to -0.015 |
| B + layer, wording per requirement | -0.058 | -0.099 to -0.018 |
| C raw | -0.094 | -0.147 to -0.034 |
| C + layer without wording | +0.012 | -0.014 to +0.038 |
| D raw | -0.119 | -0.178 to -0.058 |
| D + layer without wording | -0.019 | -0.067 to +0.027 |
| D + layer, wording per requirement | -0.022 | -0.066 to +0.022 |
| D cascade, 40% of the pairs | -0.092 | -0.140 to -0.036 |

### Policies with similar verdict shares

| Variant | Recall at 2 false alarms per document, mean over the policies (95% interval) | v1 to v3 | v4 | v5 | v6 | v7 | Own decisions: recall / precision / false alarms per document | Prompt tokens |
|---|---|---|---|---|---|---|---|---|
| A raw | 0.52 (0.46 to 0.57) | 0.31 | 0.58 | 0.65 | 0.44 | 0.69 | 0.51 / 0.55 / 2.56 | 14,031 |
| A + layer without wording | 0.60 (0.55 to 0.65) | 0.27 | 0.65 | 0.75 | 0.59 | 0.79 | 0.58 / 0.47 / 4.02 | 14,031 |
| A + layer, wording per requirement | 0.61 (0.56 to 0.64) | 0.22 | 0.64 | 0.73 | 0.65 | 0.85 | 0.59 / 0.46 / 4.36 | 14,031 |
| A layer only, no model call | 0.44 (0.37 to 0.51) | 0.14 | 0.45 | 0.34 | 0.56 | 0.70 | 0.39 / 0.35 / 4.38 | 0 |
| A cascade, 40% of the pairs | 0.54 (0.49 to 0.60) | 0.22 | 0.64 | 0.51 | 0.60 | 0.83 | 0.48 / 0.44 / 3.72 | 5,612 |
| B raw | 0.52 (0.48 to 0.56) | 0.40 | 0.60 | 0.56 | 0.44 | 0.69 | 0.46 / 0.58 / 2.01 | 16,742 |
| B + layer without wording | 0.56 (0.51 to 0.60) | 0.33 | 0.66 | 0.57 | 0.51 | 0.84 | 0.61 / 0.46 / 4.43 | 16,742 |
| B + layer, wording per requirement | 0.54 (0.50 to 0.59) | 0.23 | 0.71 | 0.55 | 0.48 | 0.89 | 0.60 / 0.42 / 5.03 | 16,742 |
| C raw | 0.55 (0.49 to 0.60) | 0.34 | 0.55 | 0.74 | 0.45 | 0.68 | 0.74 / 0.53 / 4.10 | 14,381 |
| C + layer without wording | 0.64 (0.59 to 0.69) | 0.34 | 0.67 | 0.80 | 0.63 | 0.78 | 0.56 / 0.55 / 2.87 | 14,381 |
| C + layer, wording per requirement | 0.65 (0.58 to 0.67) | 0.26 | 0.69 | 0.82 | 0.66 | 0.85 | 0.60 / 0.50 / 3.69 | 14,381 |
| D raw | 0.51 (0.47 to 0.58) | 0.43 | 0.48 | 0.58 | 0.38 | 0.66 | 0.61 / 0.55 / 3.11 | 17,092 |
| D + layer without wording | 0.59 (0.54 to 0.64) | 0.29 | 0.72 | 0.66 | 0.58 | 0.85 | 0.57 / 0.49 / 3.70 | 17,092 |
| D + layer, wording per requirement | 0.59 (0.55 to 0.63) | 0.23 | 0.71 | 0.66 | 0.64 | 0.84 | 0.58 / 0.46 / 4.28 | 17,092 |
| D cascade, 40% of the pairs | 0.52 (0.47 to 0.58) | 0.24 | 0.63 | 0.45 | 0.57 | 0.83 | 0.49 / 0.46 / 3.50 | 6,837 |

Best mean recall: C + layer, wording per requirement

| Variant | Difference to the best | 95% interval |
|---|---|---|
| A raw | -0.110 | -0.172 to -0.054 |
| A + layer without wording | -0.024 | -0.065 to +0.020 |
| A + layer, wording per requirement | -0.025 | -0.059 to +0.016 |
| A layer only, no model call | -0.193 | -0.257 to -0.123 |
| A cascade, 40% of the pairs | -0.082 | -0.134 to -0.020 |
| B raw | -0.108 | -0.167 to -0.050 |
| B + layer without wording | -0.063 | -0.101 to -0.027 |
| B + layer, wording per requirement | -0.082 | -0.127 to -0.032 |
| C raw | -0.083 | -0.146 to -0.015 |
| C + layer without wording | +0.012 | -0.021 to +0.040 |
| D raw | -0.103 | -0.169 to -0.032 |
| D + layer without wording | -0.032 | -0.083 to +0.017 |
| D + layer, wording per requirement | -0.033 | -0.083 to +0.016 |
| D cascade, 40% of the pairs | -0.105 | -0.158 to -0.038 |

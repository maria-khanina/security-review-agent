### v4

| Variant | Recall at 2 false alarms per document (95% interval) | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Own decisions: recall | Own decisions: precision | Own decisions: false alarms per document | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.58 (0.44 to 0.65) | 0.24 / 0.34 / 0.58 / 0.66 | 0.64 | 0.49 | 2.96 | 14.0 | 14,031 |
| A + layer without wording | 0.58 (0.51 to 0.66) | 0.42 / 0.49 / 0.58 / 0.67 | 0.58 | 0.59 | 1.79 | 14.0 | 14,031 |
| A + layer, wording per requirement | 0.58 (0.52 to 0.65) | 0.41 / 0.47 / 0.58 / 0.63 | 0.57 | 0.62 | 1.54 | 14.0 | 14,031 |
| A layer only, no model call | 0.49 (0.36 to 0.65) | 0.32 / 0.33 / 0.49 / 0.66 | 0.62 | 0.50 | 2.79 | 0.0 | 0 |
| A cascade, 40% of the pairs | 0.64 (0.58 to 0.72) | 0.37 / 0.55 / 0.64 / 0.69 | 0.65 | 0.61 | 1.83 | 5.6 | 5,612 |
| B raw | 0.60 (0.49 to 0.69) | 0.24 / 0.43 / 0.60 / 0.65 | 0.61 | 0.54 | 2.29 | 14.0 | 16,742 |
| B + layer without wording | 0.63 (0.55 to 0.74) | 0.44 / 0.50 / 0.63 / 0.78 | 0.60 | 0.65 | 1.46 | 14.0 | 16,742 |
| B + layer, wording per requirement | 0.63 (0.55 to 0.71) | 0.43 / 0.52 / 0.63 / 0.75 | 0.58 | 0.66 | 1.33 | 14.0 | 16,742 |
| C raw | 0.55 (0.38 to 0.67) | 0.25 / 0.34 / 0.55 / 0.70 | 0.74 | 0.44 | 4.21 | 14.0 | 14,381 |
| C + layer without wording | 0.60 (0.51 to 0.70) | 0.44 / 0.52 / 0.60 / 0.71 | 0.60 | 0.60 | 1.79 | 14.0 | 14,381 |
| C + layer, wording per requirement | 0.59 (0.49 to 0.70) | 0.40 / 0.50 / 0.59 / 0.70 | 0.59 | 0.61 | 1.71 | 14.0 | 14,381 |
| D raw | 0.48 (0.41 to 0.60) | 0.21 / 0.39 / 0.48 / 0.64 | 0.67 | 0.44 | 3.83 | 14.0 | 17,092 |
| D + layer without wording | 0.62 (0.54 to 0.72) | 0.41 / 0.51 / 0.62 / 0.77 | 0.65 | 0.58 | 2.04 | 14.0 | 17,092 |
| D + layer, wording per requirement | 0.61 (0.49 to 0.72) | 0.39 / 0.43 / 0.61 / 0.72 | 0.63 | 0.60 | 1.88 | 14.0 | 17,092 |
| D cascade, 40% of the pairs | 0.67 (0.59 to 0.77) | 0.42 / 0.46 / 0.67 / 0.74 | 0.70 | 0.60 | 2.08 | 5.6 | 6,837 |

Best recall at the primary budget: D cascade, 40% of the pairs
Cheapest variant not distinguishable from it: A cascade, 40% of the pairs

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.116 | -0.259 to +0.009 |
| A + layer without wording | -0.101 | -0.200 to -0.005 |
| A + layer, wording per requirement | -0.098 | -0.191 to -0.004 |
| A layer only, no model call | -0.193 | -0.306 to -0.053 |
| A cascade, 40% of the pairs | -0.028 | -0.097 to +0.038 |
| B raw | -0.081 | -0.190 to +0.038 |
| B + layer without wording | -0.038 | -0.145 to +0.085 |
| B + layer, wording per requirement | -0.047 | -0.154 to +0.067 |
| C raw | -0.146 | -0.309 to +0.031 |
| C + layer without wording | -0.076 | -0.182 to +0.034 |
| C + layer, wording per requirement | -0.084 | -0.203 to +0.028 |
| D raw | -0.189 | -0.314 to -0.056 |
| D + layer without wording | -0.051 | -0.124 to +0.030 |
| D + layer, wording per requirement | -0.064 | -0.144 to +0.034 |

### v5

| Variant | Recall at 2 false alarms per document (95% interval) | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Own decisions: recall | Own decisions: precision | Own decisions: false alarms per document | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.65 (0.46 to 0.79) | 0.25 / 0.42 / 0.65 / 0.75 | 0.68 | 0.60 | 2.10 | 14.0 | 14,031 |
| A + layer without wording | 0.75 (0.63 to 0.82) | 0.21 / 0.32 / 0.75 / 0.79 | 0.65 | 0.68 | 1.37 | 14.0 | 14,031 |
| A + layer, wording per requirement | 0.75 (0.63 to 0.82) | 0.23 / 0.40 / 0.75 / 0.82 | 0.65 | 0.68 | 1.37 | 14.0 | 14,031 |
| A layer only, no model call | 0.32 (0.24 to 0.49) | 0.22 / 0.26 / 0.32 / 0.60 | 0.26 | 0.56 | 0.93 | 0.0 | 0 |
| A cascade, 40% of the pairs | 0.56 (0.47 to 0.64) | 0.15 / 0.30 / 0.56 / 0.60 | 0.49 | 0.61 | 1.40 | 5.6 | 5,612 |
| B raw | 0.56 (0.43 to 0.64) | 0.29 / 0.38 / 0.56 / 0.62 | 0.48 | 0.57 | 1.67 | 14.0 | 16,742 |
| B + layer without wording | 0.59 (0.51 to 0.67) | 0.22 / 0.46 / 0.59 / 0.71 | 0.49 | 0.64 | 1.27 | 14.0 | 16,742 |
| B + layer, wording per requirement | 0.58 (0.48 to 0.67) | 0.24 / 0.46 / 0.58 / 0.74 | 0.48 | 0.65 | 1.17 | 14.0 | 16,742 |
| C raw | 0.74 (0.50 to 0.85) | 0.18 / 0.32 / 0.74 / 0.89 | 0.84 | 0.60 | 2.53 | 14.0 | 14,381 |
| C + layer without wording | 0.75 (0.65 to 0.85) | 0.24 / 0.46 / 0.75 / 0.87 | 0.69 | 0.64 | 1.73 | 14.0 | 14,381 |
| C + layer, wording per requirement | 0.75 (0.65 to 0.85) | 0.26 / 0.42 / 0.75 / 0.87 | 0.68 | 0.64 | 1.77 | 14.0 | 14,381 |
| D raw | 0.58 (0.48 to 0.76) | 0.26 / 0.40 / 0.58 / 0.76 | 0.65 | 0.57 | 2.23 | 14.0 | 17,092 |
| D + layer without wording | 0.69 (0.64 to 0.76) | 0.18 / 0.37 / 0.69 / 0.79 | 0.60 | 0.68 | 1.27 | 14.0 | 17,092 |
| D + layer, wording per requirement | 0.68 (0.62 to 0.75) | 0.24 / 0.38 / 0.68 / 0.80 | 0.59 | 0.68 | 1.27 | 14.0 | 17,092 |
| D cascade, 40% of the pairs | 0.55 (0.49 to 0.64) | 0.18 / 0.29 / 0.55 / 0.73 | 0.47 | 0.62 | 1.30 | 5.6 | 6,837 |

Best recall at the primary budget: A + layer without wording
Cheapest variant not distinguishable from it: A + layer without wording

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.092 | -0.242 to +0.025 |
| A + layer, wording per requirement | +0.000 | -0.021 to +0.023 |
| A layer only, no model call | -0.407 | -0.510 to -0.285 |
| A cascade, 40% of the pairs | -0.182 | -0.247 to -0.105 |
| B raw | -0.194 | -0.299 to -0.105 |
| B + layer without wording | -0.148 | -0.236 to -0.066 |
| B + layer, wording per requirement | -0.159 | -0.252 to -0.079 |
| C raw | -0.044 | -0.219 to +0.114 |
| C + layer without wording | +0.012 | -0.075 to +0.094 |
| C + layer, wording per requirement | +0.013 | -0.091 to +0.096 |
| D raw | -0.137 | -0.265 to +0.024 |
| D + layer without wording | -0.043 | -0.134 to +0.059 |
| D + layer, wording per requirement | -0.051 | -0.142 to +0.041 |
| D cascade, 40% of the pairs | -0.176 | -0.278 to -0.065 |

### v4 and v5 together

| Variant | Recall at 2 false alarms per document (95% interval) | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Own decisions: recall | Own decisions: precision | Own decisions: false alarms per document | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.61 (0.49 to 0.69) | 0.24 / 0.38 / 0.61 / 0.71 | 0.67 | 0.55 | 2.48 | 14.0 | 14,031 |
| A + layer without wording | 0.66 (0.58 to 0.74) | 0.25 / 0.52 / 0.66 / 0.75 | 0.62 | 0.64 | 1.56 | 14.0 | 14,031 |
| A + layer, wording per requirement | 0.68 (0.60 to 0.74) | 0.31 / 0.51 / 0.68 / 0.74 | 0.62 | 0.66 | 1.44 | 14.0 | 14,031 |
| A layer only, no model call | 0.42 (0.36 to 0.50) | 0.17 / 0.28 / 0.42 / 0.63 | 0.42 | 0.52 | 1.76 | 0.0 | 0 |
| A cascade, 40% of the pairs | 0.60 (0.52 to 0.64) | 0.18 / 0.40 / 0.60 / 0.67 | 0.56 | 0.61 | 1.59 | 5.6 | 5,612 |
| B raw | 0.54 (0.49 to 0.62) | 0.26 / 0.40 / 0.54 / 0.63 | 0.54 | 0.55 | 1.94 | 14.0 | 16,742 |
| B + layer without wording | 0.61 (0.55 to 0.67) | 0.31 / 0.48 / 0.61 / 0.75 | 0.54 | 0.64 | 1.35 | 14.0 | 16,742 |
| B + layer, wording per requirement | 0.60 (0.53 to 0.66) | 0.33 / 0.47 / 0.60 / 0.72 | 0.52 | 0.65 | 1.24 | 14.0 | 16,742 |
| C raw | 0.59 (0.49 to 0.71) | 0.21 / 0.32 / 0.59 / 0.79 | 0.79 | 0.52 | 3.28 | 14.0 | 14,381 |
| C + layer without wording | 0.68 (0.61 to 0.76) | 0.32 / 0.52 / 0.68 / 0.79 | 0.65 | 0.62 | 1.76 | 14.0 | 14,381 |
| C + layer, wording per requirement | 0.67 (0.60 to 0.77) | 0.31 / 0.50 / 0.67 / 0.79 | 0.64 | 0.62 | 1.74 | 14.0 | 14,381 |
| D raw | 0.52 (0.46 to 0.60) | 0.23 / 0.40 / 0.52 / 0.66 | 0.66 | 0.50 | 2.94 | 14.0 | 17,092 |
| D + layer without wording | 0.67 (0.58 to 0.72) | 0.29 / 0.45 / 0.67 / 0.79 | 0.62 | 0.63 | 1.61 | 14.0 | 17,092 |
| D + layer, wording per requirement | 0.66 (0.58 to 0.72) | 0.32 / 0.42 / 0.66 / 0.75 | 0.61 | 0.64 | 1.54 | 14.0 | 17,092 |
| D cascade, 40% of the pairs | 0.61 (0.54 to 0.66) | 0.26 / 0.39 / 0.61 / 0.73 | 0.57 | 0.61 | 1.65 | 5.6 | 6,837 |

Best recall at the primary budget: A + layer, wording per requirement
Cheapest variant not distinguishable from it: D cascade, 40% of the pairs

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.067 | -0.159 to +0.006 |
| A + layer without wording | -0.006 | -0.038 to +0.014 |
| A layer only, no model call | -0.240 | -0.344 to -0.139 |
| A cascade, 40% of the pairs | -0.077 | -0.148 to -0.014 |
| B raw | -0.119 | -0.204 to -0.033 |
| B + layer without wording | -0.055 | -0.123 to +0.011 |
| B + layer, wording per requirement | -0.069 | -0.133 to +0.004 |
| C raw | -0.080 | -0.175 to +0.041 |
| C + layer without wording | +0.012 | -0.044 to +0.070 |
| C + layer, wording per requirement | +0.012 | -0.048 to +0.075 |
| D raw | -0.139 | -0.223 to -0.061 |
| D + layer without wording | -0.008 | -0.065 to +0.050 |
| D + layer, wording per requirement | -0.011 | -0.074 to +0.049 |
| D cascade, 40% of the pairs | -0.061 | -0.155 to +0.031 |

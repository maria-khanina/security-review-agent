### v5

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Recall at 2 (95% interval) | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.57 | 0.79 | 1.10 | 0.37 / 0.52 / 0.65 / 0.70 | 0.65 (0.60 to 0.75) | 14.0 | 11,908 |
| A + layer without wording | 0.78 | 0.83 | 1.20 | 0.52 / 0.70 / 0.83 / 1.00 | 0.83 (0.80 to 1.00) | 14.0 | 11,908 |
| A + layer, wording per requirement | 0.78 | 0.78 | 1.63 | 0.42 / 0.71 / 0.85 / 1.00 | 0.85 (0.76 to 1.00) | 14.0 | 11,908 |
| B + layer, wording per requirement | 0.65 | 0.80 | 1.23 | 0.48 / 0.60 / 0.82 / 1.00 | 0.82 (0.69 to 1.00) | 14.0 | 14,625 |
| D + layer without wording | 0.70 | 0.83 | 1.03 | 0.57 / 0.70 / 0.90 / 1.00 | 0.90 (0.80 to 1.00) | 14.0 | 14,975 |
| D raw | 0.69 | 0.81 | 1.17 | 0.40 / 0.62 / 0.77 / 0.82 | 0.77 (0.73 to 0.83) | 14.0 | 14,975 |
| layer only, no model call | 0.60 | 0.71 | 1.83 | 0.41 / 0.42 / 0.65 / 1.00 | 0.65 (0.54 to 1.00) | 0.0 | 0 |
| cascade, 40% of the pairs | 0.60 | 0.81 | 1.07 | 0.43 / 0.60 / 0.91 / 1.00 | 0.91 (0.77 to 1.00) | 5.6 | 5,990 |

Best by the rule: cascade, 40% of the pairs

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.223 | -0.317 to -0.090 |
| A + layer without wording | -0.051 | -0.106 to +0.068 |
| A + layer, wording per requirement | -0.041 | -0.101 to +0.050 |
| B + layer, wording per requirement | -0.096 | -0.181 to +0.002 |
| D + layer without wording | -0.015 | -0.059 to +0.034 |
| D raw | -0.113 | -0.202 to +0.009 |
| layer only, no model call | -0.222 | -0.336 to +0.000 |

### v4 and v5 together

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Recall at 2 (95% interval) | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.60 | 0.75 | 1.35 | 0.34 / 0.47 / 0.66 / 0.69 | 0.66 (0.61 to 0.73) | 14.0 | 11,908 |
| A + layer without wording | 0.78 | 0.78 | 1.56 | 0.43 / 0.64 / 0.86 / 0.91 | 0.86 (0.75 to 0.89) | 14.0 | 11,908 |
| A + layer, wording per requirement | 0.80 | 0.71 | 2.19 | 0.55 / 0.65 / 0.79 / 0.91 | 0.79 (0.74 to 0.86) | 14.0 | 11,908 |
| B + layer, wording per requirement | 0.69 | 0.76 | 1.54 | 0.45 / 0.59 / 0.77 / 0.87 | 0.77 (0.68 to 0.81) | 14.0 | 14,625 |
| D + layer without wording | 0.71 | 0.78 | 1.41 | 0.43 / 0.61 / 0.81 / 0.91 | 0.81 (0.75 to 0.86) | 14.0 | 14,975 |
| D raw | 0.64 | 0.74 | 1.52 | 0.30 / 0.49 / 0.68 / 0.75 | 0.68 (0.62 to 0.74) | 14.0 | 14,975 |
| layer only, no model call | 0.68 | 0.66 | 2.43 | 0.27 / 0.49 / 0.59 / 0.74 | 0.59 (0.55 to 0.67) | 0.0 | 0 |
| cascade, 40% of the pairs | 0.69 | 0.76 | 1.50 | 0.25 / 0.45 / 0.75 / 0.87 | 0.75 (0.70 to 0.84) | 5.6 | 5,990 |

Best by the rule: A + layer without wording

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.177 | -0.232 to -0.094 |
| A + layer, wording per requirement | -0.042 | -0.095 to +0.019 |
| B + layer, wording per requirement | -0.084 | -0.127 to -0.022 |
| D + layer without wording | -0.027 | -0.076 to +0.051 |
| D raw | -0.159 | -0.223 to -0.078 |
| layer only, no model call | -0.240 | -0.304 to -0.158 |
| cascade, 40% of the pairs | -0.078 | -0.131 to -0.001 |

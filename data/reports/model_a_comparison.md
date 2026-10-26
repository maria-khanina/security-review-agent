### v4

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Recall at 2 (95% interval) | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.60 | 0.53 | 2.38 | 0.22 / 0.42 / 0.60 / 0.66 | 0.60 (0.49 to 0.67) | 14.0 | 13,009 |
| A + layer without wording | 0.56 | 0.55 | 2.04 | 0.45 / 0.47 / 0.56 / 0.67 | 0.56 (0.46 to 0.70) | 14.0 | 13,009 |
| A + layer, wording per requirement | 0.55 | 0.56 | 1.92 | 0.41 / 0.45 / 0.57 / 0.63 | 0.57 (0.47 to 0.65) | 14.0 | 13,009 |
| layer only, no model call | 0.62 | 0.50 | 2.79 | 0.32 / 0.34 / 0.49 / 0.66 | 0.49 (0.35 to 0.63) | 0.0 | 0 |
| cascade, 40% of the pairs | 0.63 | 0.58 | 2.00 | 0.35 / 0.53 / 0.64 / 0.73 | 0.64 (0.56 to 0.73) | 5.6 | 5,204 |

No finalist reaches the minimum precision.

### v5

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Recall at 2 (95% interval) | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.62 | 0.59 | 1.97 | 0.29 / 0.40 / 0.65 / 0.71 | 0.65 (0.45 to 0.79) | 14.0 | 13,009 |
| A + layer without wording | 0.64 | 0.67 | 1.40 | 0.20 / 0.32 / 0.74 / 0.81 | 0.74 (0.64 to 0.80) | 14.0 | 13,009 |
| A + layer, wording per requirement | 0.63 | 0.68 | 1.37 | 0.24 / 0.32 / 0.74 / 0.81 | 0.74 (0.64 to 0.80) | 14.0 | 13,009 |
| layer only, no model call | 0.26 | 0.56 | 0.93 | 0.22 / 0.26 / 0.30 / 0.59 | 0.30 (0.22 to 0.48) | 0.0 | 0 |
| cascade, 40% of the pairs | 0.48 | 0.61 | 1.40 | 0.13 / 0.27 / 0.56 / 0.68 | 0.56 (0.48 to 0.65) | 5.6 | 5,204 |

Best by the rule: A + layer without wording

| Variant | Difference of the recall at 2 against the best | 95% interval |
|---|---|---|
| A raw | -0.088 | -0.242 to +0.015 |
| A + layer, wording per requirement | +0.000 | -0.015 to +0.016 |
| layer only, no model call | -0.416 | -0.510 to -0.287 |
| cascade, 40% of the pairs | -0.163 | -0.225 to -0.076 |

### v4 and v5 together

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Recall at 2 (95% interval) | Calls | Prompt tokens |
|---|---|---|---|---|---|---|---|
| A raw | 0.62 | 0.56 | 2.15 | 0.26 / 0.40 / 0.60 / 0.70 | 0.60 (0.51 to 0.71) | 14.0 | 13,009 |
| A + layer without wording | 0.60 | 0.62 | 1.69 | 0.26 / 0.47 / 0.65 / 0.76 | 0.65 (0.57 to 0.74) | 14.0 | 13,009 |
| A + layer, wording per requirement | 0.60 | 0.62 | 1.61 | 0.33 / 0.43 / 0.67 / 0.73 | 0.67 (0.59 to 0.72) | 14.0 | 13,009 |
| layer only, no model call | 0.42 | 0.52 | 1.76 | 0.17 / 0.28 / 0.42 / 0.62 | 0.42 (0.36 to 0.49) | 0.0 | 0 |
| cascade, 40% of the pairs | 0.55 | 0.59 | 1.67 | 0.19 / 0.40 / 0.60 / 0.67 | 0.60 (0.53 to 0.65) | 5.6 | 5,204 |

No finalist reaches the minimum precision.

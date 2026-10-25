| Variant | Shown recall (95% interval) | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Accuracy | Tolerant accuracy | Calls | Prompt tokens | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| A short reason, no overview: raw | 0.65 (0.59 to 0.71) | 0.71 | 1.67 | 0.27 / 0.43 / 0.67 / 0.72 | 0.643 | 0.721 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer without the wording | 0.80 (0.75 to 0.84) | 0.71 | 2.00 | 0.32 / 0.41 / 0.80 / 0.93 | 0.641 | 0.721 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer independent of the policy | 0.87 (0.84 to 0.91) | 0.54 | 4.58 | 0.39 / 0.44 / 0.57 / 0.71 | 0.578 | 0.622 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer, all features (first wording) | 0.95 (0.91 to 0.97) | 0.51 | 5.71 | 0.16 / 0.32 / 0.61 / 0.83 | 0.505 | 0.565 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer, all features (wording per requirement) | 0.82 (0.77 to 0.85) | 0.64 | 2.88 | 0.58 / 0.62 / 0.82 / 0.89 | 0.609 | 0.684 | 16.0 | 13,963 | 18 |
| B short reason, overview: raw | 0.56 (0.48 to 0.62) | 0.67 | 1.67 | 0.22 / 0.34 / 0.60 / 0.68 | 0.646 | 0.706 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer without the wording | 0.80 (0.76 to 0.85) | 0.67 | 2.42 | 0.22 / 0.51 / 0.71 / 0.91 | 0.635 | 0.707 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer independent of the policy | 0.71 (0.65 to 0.76) | 0.60 | 2.92 | 0.28 / 0.34 / 0.60 / 0.68 | 0.651 | 0.680 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer, all features (first wording) | 0.86 (0.81 to 0.91) | 0.52 | 4.96 | 0.16 / 0.36 / 0.48 / 0.77 | 0.518 | 0.578 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer, all features (wording per requirement) | 0.75 (0.69 to 0.81) | 0.71 | 1.92 | 0.43 / 0.51 / 0.77 / 0.86 | 0.661 | 0.725 | 16.0 | 16,970 | 19 |
| C reasoning, no overview: raw | 0.66 (0.60 to 0.72) | 0.58 | 2.92 | 0.04 / 0.21 / 0.55 / 0.67 | 0.622 | 0.660 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer without the wording | 0.68 (0.63 to 0.74) | 0.67 | 2.04 | 0.25 / 0.39 / 0.66 / 0.83 | 0.651 | 0.704 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer independent of the policy | 0.68 (0.61 to 0.74) | 0.51 | 3.96 | 0.29 / 0.39 / 0.47 / 0.56 | 0.565 | 0.600 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer, all features (first wording) | 0.85 (0.81 to 0.88) | 0.51 | 5.12 | 0.14 / 0.30 / 0.50 / 0.67 | 0.552 | 0.589 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer, all features (wording per requirement) | 0.72 (0.65 to 0.78) | 0.67 | 2.21 | 0.32 / 0.45 / 0.70 / 0.78 | 0.682 | 0.721 | 16.0 | 14,363 | 25 |
| D reasoning, overview: raw | 0.57 (0.51 to 0.62) | 0.64 | 1.96 | 0.22 / 0.36 / 0.57 / 0.64 | 0.664 | 0.688 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer without the wording | 0.74 (0.68 to 0.79) | 0.71 | 1.88 | 0.32 / 0.44 / 0.74 / 0.87 | 0.664 | 0.723 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer independent of the policy | 0.71 (0.65 to 0.77) | 0.58 | 3.17 | 0.39 / 0.45 / 0.57 / 0.68 | 0.648 | 0.669 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer, all features (first wording) | 0.84 (0.82 to 0.87) | 0.51 | 4.96 | 0.21 / 0.30 / 0.60 / 0.74 | 0.518 | 0.574 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer, all features (wording per requirement) | 0.73 (0.69 to 0.77) | 0.66 | 2.29 | 0.51 / 0.58 / 0.78 / 0.86 | 0.648 | 0.701 | 16.0 | 17,370 | 25 |
| E reasoning, architecture card: raw | 0.72 (0.66 to 0.79) | 0.56 | 3.54 | 0.09 / 0.36 / 0.46 / 0.70 | 0.612 | 0.645 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer without the wording | 0.72 (0.65 to 0.78) | 0.63 | 2.54 | 0.29 / 0.54 / 0.66 / 0.80 | 0.622 | 0.681 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer independent of the policy | 0.80 (0.75 to 0.84) | 0.59 | 3.42 | 0.38 / 0.45 / 0.51 / 0.62 | 0.648 | 0.681 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer, all features (first wording) | 0.82 (0.77 to 0.88) | 0.51 | 4.92 | 0.20 / 0.41 / 0.51 / 0.75 | 0.518 | 0.573 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer, all features (wording per requirement) | 0.73 (0.65 to 0.80) | 0.73 | 1.67 | 0.53 / 0.59 / 0.75 / 0.81 | 0.690 | 0.745 | 16.0 | 16,973 | 26 |
| prior only, no model call | 0.80 (0.74 to 0.87) | 0.61 | 3.17 | 0.14 / 0.36 / 0.60 / 0.79 | 0.560 | 0.646 | 0.0 | 0 | 0 |
| cascade, 40% of the pairs sent to the model | 0.83 (0.77 to 0.89) | 0.72 | 2.04 | 0.23 / 0.45 / 0.82 / 0.90 | 0.638 | 0.724 | 6.4 | 6,948 | 10 |
| cascade, 60% of the pairs sent to the model | 0.81 (0.76 to 0.86) | 0.71 | 2.04 | 0.25 / 0.32 / 0.80 / 0.89 | 0.654 | 0.727 | 9.6 | 10,422 | 15 |
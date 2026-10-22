### Paired pass rates

| comparison (A vs B) | set | pairs | A pass | B pass | both pass | both fail | A only | B only | exact McNemar p | A−B (paired bootstrap 95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| INF-ORIG vs INF-NORM (primary 1: leak value, informed) | primary30 | 30 | 20 | 17 | 13 | 6 | 7 | 4 | 0.5488 | +0.100 (-0.100 to +0.300) |
| INF-ORIG vs INF-NORM (primary 1: leak value, informed) | all | 73 | 50 | 45 | 36 | 14 | 14 | 9 | 0.4049 | +0.069 (-0.055 to +0.192) |
| INF-ORIG vs INF-NORM (primary 1: leak value, informed) | all_stratum_strong | 37 | 23 | 21 | 17 | 10 | 6 | 4 | 0.7539 | +0.054 (-0.108 to +0.216) |
| INF-ORIG vs INF-NORM (primary 1: leak value, informed) | all_stratum_random | 36 | 27 | 24 | 19 | 4 | 8 | 5 | 0.5811 | +0.083 (-0.111 to +0.278) |
| INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day) | primary30 | 30 | 20 | 21 | 17 | 6 | 3 | 4 | 1.0 | -0.033 (-0.200 to +0.133) |
| INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day) | all | 73 | 50 | 50 | 42 | 15 | 8 | 8 | 1.0 | +0.000 (-0.110 to +0.110) |
| INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day) | all_stratum_strong | 37 | 23 | 23 | 19 | 10 | 4 | 4 | 1.0 | +0.000 (-0.135 to +0.135) |
| INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day) | all_stratum_random | 36 | 27 | 27 | 23 | 5 | 4 | 4 | 1.0 | +0.000 (-0.167 to +0.139) |
| INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day) | primary30 | 30 | 17 | 20 | 13 | 6 | 4 | 7 | 0.5488 | -0.100 (-0.300 to +0.133) |
| INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day) | all | 73 | 45 | 47 | 35 | 16 | 10 | 12 | 0.8318 | -0.027 (-0.151 to +0.096) |
| INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day) | all_stratum_strong | 37 | 21 | 22 | 16 | 10 | 5 | 6 | 1.0 | -0.027 (-0.189 to +0.135) |
| INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day) | all_stratum_random | 36 | 24 | 25 | 19 | 6 | 5 | 6 | 1.0 | -0.028 (-0.222 to +0.139) |
| Step-B ORIG vs NORM (reference, uninformed) | primary30 | 30 | 21 | 20 | 17 | 6 | 4 | 3 | 1.0 | +0.033 (-0.133 to +0.200) |
| Step-B ORIG vs NORM (reference, uninformed) | all | 73 | 50 | 47 | 41 | 17 | 9 | 6 | 0.6072 | +0.041 (-0.055 to +0.151) |
| Step-B ORIG vs NORM (reference, uninformed) | all_stratum_strong | 37 | 23 | 22 | 18 | 10 | 5 | 4 | 1.0 | +0.027 (-0.135 to +0.189) |
| Step-B ORIG vs NORM (reference, uninformed) | all_stratum_random | 36 | 27 | 25 | 23 | 7 | 4 | 2 | 0.6875 | +0.056 (-0.083 to +0.194) |

**Secondary metrics — INF-ORIG vs INF-NORM (primary 1: leak value, informed), primary30** (A = INF-ORIG, B = INF-NORM; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 13 | 28 | 23 | 26.85 | 24.77 | 2.077 (-5.846 to 9.846) | 0 (-1 to 6) |
| steps (fail = 40) | 30 | 36.5 | 40 | 30.23 | 31.33 | -1.1 (-6.4 to 4.4) | 0 (-4 to 1) |
| effective steps (both passed) | 13 | 24 | 23 | 24.46 | 24.77 | -0.3077 (-7.385 to 5.846) | 0 (-1 to 6) |
| prompt tokens / run | 30 | 254,401 | 180,760 | 399,016 | 338,571 | 60,446 (-64,770 to 205,516) | 30,738 (-10,896 to 97,368) |
| completion tokens / run | 30 | 24,333 | 14,550 | 26,311 | 25,272 | 1,039 (-9,086 to 10,801) | 5,258 (-466 to 12,565) |
| cached prompt tokens / run | 30 | 227,712 | 164,672 | 372,919 | 315,712 | 57,207 (-59,520 to 194,461) | 29,440 (-9,856 to 96,384) |
| cost / run ($) | 30 | 0.02738 | 0.01985 | 0.0365 | 0.0335 | 0.003 (-0.0108 to 0.0164) | 0.0064 (-0.0001 to 0.0127) |
| cost / run, both passed ($) | 13 | 0.03088 | 0.01394 | 0.0347 | 0.0353 | -0.0006 (-0.0277 to 0.0245) | 0.0076 (-0 to 0.0161) |
| wall time / run (s) | 30 | 169.6 | 138.6 | 218.3 | 206.7 | 11.58 (-50.52 to 73.09) | 27.45 (-12.25 to 74.9) |
| files opened before first edit | 30 | 5 | 6 | 7.667 | 6.967 | 0.7 (-0.5333 to 2.067) | 0 (-1 to 1.5) |
| first-edit step (none = 41) | 30 | 15 | 17.5 | 17.43 | 18.1 | -0.6667 (-4.8 to 3.268) | 0 (-3 to 2.5) |
| late-cluster file opened before first edit (share) | 30 | 1 | 1 | 0.9667 | 1 | -0.0333 (-0.1 to 0) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 30 | 1 | 1 | 0.9333 | 0.9333 | 0 (-0.1 to 0.1) | 0 (0 to 0) |
| time-based command before first edit (share) | 30 | 0 | 0 | 0.3 | 0.2667 | 0.0333 (-0.1333 to 0.2) | 0 (0 to 0) |

**Secondary metrics — INF-ORIG vs INF-NORM (primary 1: leak value, informed), all** (A = INF-ORIG, B = INF-NORM; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 36 | 26 | 20.5 | 24.47 | 23.14 | 1.333 (-2.167 to 4.972) | 0.5 (-1.5 to 2) |
| steps (fail = 40) | 73 | 33 | 36 | 29.63 | 29.68 | -0.0548 (-3.027 to 2.863) | 0 (0 to 0) |
| effective steps (both passed) | 36 | 23 | 20.5 | 23.36 | 23 | 0.3611 (-2.806 to 3.5) | 0 (-2.5 to 2.5) |
| prompt tokens / run | 73 | 282,194 | 240,613 | 423,051 | 324,884 | 98,167 (-5,841 to 226,160) | 4,048 (-12,902 to 41,030) |
| completion tokens / run | 73 | 18,751 | 12,391 | 24,153 | 21,977 | 2,175 (-5,821 to 9,269) | 769 (-31 to 5,403) |
| cached prompt tokens / run | 73 | 251,392 | 218,752 | 396,423 | 303,285 | 93,138 (-4,484 to 214,183) | 3,456 (-12,032 to 40,320) |
| cost / run ($) | 73 | 0.01769 | 0.01384 | 0.026 | 0.023 | 0.003 (-0.0044 to 0.01) | 0.0008 (-0 to 0.0058) |
| cost / run, both passed ($) | 36 | 0.01658 | 0.01048 | 0.0232 | 0.0195 | 0.0037 (-0.0072 to 0.0137) | 0.0009 (-0.0001 to 0.0077) |
| wall time / run (s) | 73 | 165.9 | 138.3 | 195.6 | 190.6 | 5.049 (-35.49 to 43.24) | 19.9 (-3.2 to 31) |
| files opened before first edit | 73 | 5 | 6 | 7.986 | 7.26 | 0.726 (-0.137 to 1.657) | 1 (0 to 1) |
| first-edit step (none = 41) | 73 | 15 | 14 | 18.53 | 17.41 | 1.123 (-0.9452 to 3.11) | 0 (0 to 2) |
| late-cluster file opened before first edit (share) | 73 | 1 | 1 | 0.9726 | 0.9863 | -0.0137 (-0.0411 to 0) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 73 | 1 | 1 | 0.8493 | 0.8767 | -0.0274 (-0.0822 to 0.0274) | 0 (0 to 0) |
| time-based command before first edit (share) | 73 | 0 | 0 | 0.3699 | 0.3288 | 0.0411 (-0.0959 to 0.1644) | 0 (0 to 0) |

**Secondary metrics — INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day), primary30** (A = INF-ORIG, B = ORIG; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 17 | 25 | 31 | 25.12 | 27.29 | -2.176 (-6.824 to 2.412) | 0 (-11 to 3) |
| steps (fail = 40) | 30 | 36.5 | 35 | 30.23 | 30.73 | -0.5 (-4.567 to 3.633) | 0 (-1 to 0.5) |
| effective steps (both passed) | 17 | 25 | 31 | 25.12 | 26.88 | -1.765 (-6.294 to 2.647) | 0 (-9 to 3) |
| prompt tokens / run | 30 | 254,401 | 243,252 | 399,016 | 381,318 | 17,699 (-146,026 to 186,615) | -14,056 (-93,979 to 114,016) |
| completion tokens / run | 30 | 24,333 | 17,219 | 26,311 | 22,009 | 4,302 (-4,848 to 13,144) | 8.5 (-4,368 to 10,252) |
| cached prompt tokens / run | 30 | 227,712 | 224,832 | 372,919 | 358,711 | 14,208 (-142,554 to 174,857) | -14,272 (-88,896 to 105,472) |
| cost / run ($) | 30 | 0.02738 | 0.01353 | 0.0365 | 0.0175 | 0.019 (0.0076 to 0.0309) | 0.0098 (0.0003 to 0.0239) |
| cost / run, both passed ($) | 17 | 0.02852 | 0.01591 | 0.0323 | 0.021 | 0.0113 (-0.0027 to 0.0265) | 0.0039 (-0.0006 to 0.0235) |
| wall time / run (s) | 30 | 169.6 | 152.5 | 218.3 | 185.6 | 32.67 (-14.68 to 78.58) | 20.75 (-20.65 to 71.35) |
| files opened before first edit | 30 | 5 | 5 | 7.667 | 6.833 | 0.8333 (-0.5333 to 2.367) | 1 (-1 to 1.5) |
| first-edit step (none = 41) | 30 | 15 | 14 | 17.43 | 15.4 | 2.033 (-1.001 to 5.4) | 0.5 (-2 to 2) |
| late-cluster file opened before first edit (share) | 30 | 1 | 1 | 0.9667 | 0.9667 | 0 (-0.1 to 0.1) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 30 | 1 | 1 | 0.9333 | 0.9667 | -0.0333 (-0.1 to 0) | 0 (0 to 0) |
| time-based command before first edit (share) | 30 | 0 | 0 | 0.3 | 0 | 0.3 (0.1333 to 0.4667) | 0 (0 to 0) |

**Secondary metrics — INF-ORIG vs Step-B ORIG (primary 2: value of the hint; cross-day), all** (A = INF-ORIG, B = ORIG; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 42 | 26.5 | 25 | 24.67 | 25.62 | -0.9524 (-4.524 to 2.429) | -0.5 (-3.5 to 2) |
| steps (fail = 40) | 73 | 33 | 35 | 29.63 | 29.96 | -0.3288 (-3.165 to 2.493) | 0 (0 to 0) |
| effective steps (both passed) | 42 | 26.5 | 21 | 24.45 | 23.26 | 1.19 (-1.619 to 3.976) | 0 (-2 to 2.5) |
| prompt tokens / run | 73 | 282,194 | 268,734 | 423,051 | 338,165 | 84,886 (-31,475 to 225,784) | -17,450 (-45,182 to 16,309) |
| completion tokens / run | 73 | 18,751 | 11,109 | 24,153 | 21,696 | 2,456 (-6,293 to 10,126) | -99 (-1,225 to 4,010) |
| cached prompt tokens / run | 73 | 251,392 | 250,752 | 396,423 | 316,332 | 80,091 (-30,163 to 213,727) | -15,233 (-39,939 to 15,616) |
| cost / run ($) | 73 | 0.01769 | 0.0128 | 0.026 | 0.0209 | 0.0051 (-0.0035 to 0.0132) | -0.0003 (-0.0025 to 0.0059) |
| cost / run, both passed ($) | 42 | 0.01871 | 0.01194 | 0.0231 | 0.0214 | 0.0017 (-0.0091 to 0.0119) | -0.0003 (-0.0036 to 0.005) |
| wall time / run (s) | 73 | 165.9 | 151.8 | 195.6 | 186.4 | 9.266 (-32.43 to 48.72) | -0.9 (-17.5 to 24.3) |
| files opened before first edit | 73 | 5 | 6 | 7.986 | 7.411 | 0.5753 (-0.1233 to 1.343) | 1 (-1 to 1) |
| first-edit step (none = 41) | 73 | 15 | 14 | 18.53 | 16.88 | 1.657 (-0.274 to 3.699) | 0 (-1 to 1) |
| late-cluster file opened before first edit (share) | 73 | 1 | 1 | 0.9726 | 0.9726 | 0 (-0.0411 to 0.0411) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 73 | 1 | 1 | 0.8493 | 0.8904 | -0.0411 (-0.0959 to 0) | 0 (0 to 0) |
| time-based command before first edit (share) | 73 | 0 | 0 | 0.3699 | 0.0137 | 0.3562 (0.2466 to 0.4658) | 0 (0 to 0) |

**Secondary metrics — INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day), primary30** (A = INF-NORM, B = NORM; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 13 | 19 | 23 | 24.38 | 25.38 | -1 (-5.538 to 3.923) | -2 (-5 to 0) |
| steps (fail = 40) | 30 | 40 | 30.5 | 31.33 | 29.93 | 1.4 (-3 to 5.733) | 0 (-2 to 0) |
| effective steps (both passed) | 13 | 19 | 21 | 24.38 | 24.46 | -0.0769 (-4.846 to 5) | -2 (-4 to 2) |
| prompt tokens / run | 30 | 180,760 | 268,451 | 338,571 | 314,367 | 24,204 (-64,996 to 122,595) | -17,023 (-52,020 to 39,972) |
| completion tokens / run | 30 | 14,550 | 11,836 | 25,272 | 20,444 | 4,828 (-2,342 to 13,102) | 118 (-1,958 to 8,700) |
| cached prompt tokens / run | 30 | 164,672 | 245,952 | 315,712 | 294,293 | 21,419 (-62,742 to 112,961) | -12,352 (-49,280 to 39,232) |
| cost / run ($) | 30 | 0.01985 | 0.01043 | 0.0335 | 0.016 | 0.0176 (0.0073 to 0.0295) | 0.0074 (0.0004 to 0.0188) |
| cost / run, both passed ($) | 13 | 0.02442 | 0.00904 | 0.0396 | 0.014 | 0.0256 (0.0063 to 0.0501) | 0.0149 (0.0011 to 0.0253) |
| wall time / run (s) | 30 | 138.6 | 129.1 | 206.7 | 170.4 | 36.28 (-10.35 to 85.68) | -0.55 (-15.35 to 48.85) |
| files opened before first edit | 30 | 6 | 5.5 | 6.967 | 7.367 | -0.4 (-1.901 to 0.8667) | 0 (-1 to 1) |
| first-edit step (none = 41) | 30 | 17.5 | 15.5 | 18.1 | 16.57 | 1.533 (-1.067 to 4.167) | 0.5 (-1.5 to 3) |
| late-cluster file opened before first edit (share) | 30 | 1 | 1 | 1 | 1 | 0 (0 to 0) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 30 | 1 | 1 | 0.9333 | 0.9667 | -0.0333 (-0.1 to 0) | 0 (0 to 0) |
| time-based command before first edit (share) | 30 | 0 | 0 | 0.2667 | 0 | 0.2667 (0.1 to 0.4333) | 0 (0 to 0) |

**Secondary metrics — INF-NORM vs Step-B NORM (secondary: hint without leak; cross-day), all** (A = INF-NORM, B = NORM; paired A−B with bootstrap 95% CI)

| metric | n | median A | median B | mean A | mean B | mean diff (CI) | median diff (CI) |
|---|---|---|---|---|---|---|---|
| steps (both passed) | 35 | 19 | 23 | 23.43 | 24.03 | -0.6 (-3.314 to 2.143) | -1 (-3 to 1) |
| steps (fail = 40) | 73 | 36 | 36 | 29.68 | 30.25 | -0.5616 (-3.151 to 2) | 0 (0 to 0) |
| effective steps (both passed) | 35 | 19 | 21 | 23.29 | 23.37 | -0.0857 (-2.743 to 2.601) | -1 (-2 to 2) |
| prompt tokens / run | 73 | 240,613 | 258,691 | 324,884 | 305,194 | 19,689 (-29,245 to 71,402) | 2,408 (-37,031 to 26,980) |
| completion tokens / run | 73 | 12,391 | 11,958 | 21,977 | 18,433 | 3,545 (-1,755 to 9,806) | 163 (-1,837 to 772) |
| cached prompt tokens / run | 73 | 218,752 | 239,104 | 303,285 | 285,093 | 18,192 (-27,865 to 66,452) | 384 (-21,120 to 25,728) |
| cost / run ($) | 73 | 0.01384 | 0.01415 | 0.023 | 0.0183 | 0.0047 (-0.0007 to 0.011) | -0.0013 (-0.0036 to 0.0007) |
| cost / run, both passed ($) | 35 | 0.009794 | 0.01397 | 0.021 | 0.0164 | 0.0046 (-0.004 to 0.0156) | -0.0017 (-0.0075 to -0.0001) |
| wall time / run (s) | 73 | 138.3 | 124.7 | 190.6 | 159.5 | 31.1 (4.843 to 59.8) | 4.2 (-0.4 to 26.6) |
| files opened before first edit | 73 | 6 | 5 | 7.26 | 7.466 | -0.2055 (-1.096 to 0.6301) | 0 (0 to 1) |
| first-edit step (none = 41) | 73 | 14 | 15 | 17.41 | 17 | 0.411 (-1.219 to 2.014) | 0 (-1 to 1) |
| late-cluster file opened before first edit (share) | 73 | 1 | 1 | 0.9863 | 0.9863 | 0 (0 to 0) | 0 (0 to 0) |
| final diff touches late-cluster file (share) | 73 | 1 | 1 | 0.8767 | 0.8767 | 0 (-0.0411 to 0.0411) | 0 (0 to 0) |
| time-based command before first edit (share) | 73 | 0 | 0 | 0.3288 | 0 | 0.3288 (0.2192 to 0.4384) | 0 (0 to 0) |

### Per-condition summary (all pairs of each comparison)

| condition | set | n | pass | total cost $ | cost per solved $ | median steps (solved) | ran time cmd | … before first edit | time cmd in reply text (attempted) | `ls -l`-type only | late file opened pre-edit | final touches late | submitted | stop reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| INF-ORIG | primary30 | 30 | 20 | 1.0956 | 0.0548 | 26.5 | 9 | 9 | 14 | 10 | 29 | 28 | 22 | {'step_cap': 8, 'submitted': 22} |
| INF-NORM | primary30 | 30 | 17 | 1.0065 | 0.0592 | 23.0 | 8 | 8 | 9 | 9 | 30 | 28 | 24 | {'run_cost_cap': 1, 'step_cap': 5, 'submitted': 24} |
| INF-ORIG | all | 73 | 50 | 1.8992 | 0.038 | 26.5 | 27 | 27 | 33 | 27 | 71 | 62 | 54 | {'step_cap': 19, 'submitted': 54} |
| INF-NORM | all | 73 | 45 | 1.6791 | 0.0373 | 20.0 | 25 | 24 | 27 | 22 | 72 | 64 | 58 | {'run_cost_cap': 1, 'step_cap': 14, 'submitted': 58} |
| ORIG | primary30 | 30 | 21 | 0.5249 | 0.025 | 26.0 | 0 | 0 | 0 | 4 | 29 | 29 | 25 | {'step_cap': 5, 'submitted': 25} |
| ORIG | all | 73 | 50 | 1.5285 | 0.0306 | 23.5 | 1 | 1 | 1 | 14 | 71 | 65 | 55 | {'run_cost_cap': 1, 'step_cap': 17, 'submitted': 55} |
| NORM | primary30 | 30 | 20 | 0.48 | 0.024 | 23.5 | 0 | 0 | 0 | 3 | 30 | 29 | 23 | {'step_cap': 7, 'submitted': 23} |
| NORM | all | 73 | 47 | 1.3327 | 0.0284 | 24.0 | 0 | 0 | 0 | 11 | 72 | 64 | 55 | {'step_cap': 18, 'submitted': 55} |

### Observational: INF-ORIG runs with vs without a time-based command before the first edit

| set | INF-ORIG ran time cmd pre-edit | n tasks | INF-ORIG pass | INF-NORM pass (same tasks) | Step-B ORIG pass (same tasks) |
|---|---|---|---|---|---|
| primary30 | True | 9 | 6 | 6 | 6 |
| primary30 | False | 21 | 14 | 11 | 15 |
| all | True | 27 | 20 | 17 | 19 |
| all | False | 46 | 30 | 28 | 31 |

### Post-hoc descriptive (Amendment 2): did the first executed time-based command show a late-cluster file?

| condition | runs with an executed time cmd | output names ≥ 1 late-cluster file (anywhere) | … within first 10 output lines | shown file later opened before first edit |
|---|---|---|---|---|
| INF-ORIG | 27 | 17 | 11 | 15 |
| INF-NORM | 25 | 15 | 6 | 14 |

### Kind of executed time-based command (descriptive)

| condition | runs with any | recursive/file-level `find -newer/-mtime/-mmin` | … before first edit | only `ls -t`-type (one directory level) |
|---|---|---|---|---|
| INF-ORIG | 27 | 4 | 4 | 23 |
| INF-NORM | 25 | 5 | 4 | 20 |

### Keyword audit of INF-* commands (`results/informed_cmd_audit.json`)

| condition | commands | broad keyword hits | classified targeted | `ls -l`-type only | neither | runs with a hit | git-history hunting runs |
|---|---|---|---|---|---|---|---|
| INF-NORM | 1700 | 73 | 25 | 32 | 16 | 50 | 24 |
| INF-ORIG | 1779 | 87 | 27 | 36 | 24 | 55 | 25 |

**Spend** (`results/spend_informed.jsonl`): $3.5783 over 3746 calls; by kind {'smoke': 2e-05, 'INF-NORM': 1.67906, 'INF-ORIG': 1.89919}; cache-hit share of prompt tokens 0.9355.

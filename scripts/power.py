"""Power / minimum detectable effect for the paired design, given the observed discordance rate.
Model: each pair is discordant with prob q (observed); a discordant pair favours ORIG with prob pi.
Effect = q*(2*pi-1). Power = P(exact two-sided McNemar p < 0.05). Exact via binomial sums."""
import json
# Published copy: data paths made configurable (scripts/cupel_paths.py) and the Step-B helpers imported from
# scripts/analysis_common.py instead of the unpublished orchestrator. Analysis logic unchanged.
from cupel_paths import CUPEL_ROOT, CUPEL_PHASE1
from math import comb


def mcnemar_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def power(n, q, pi):
    tot = 0.0
    for d in range(n + 1):
        pd = comb(n, d) * q ** d * (1 - q) ** (n - d)
        for b in range(d + 1):
            if mcnemar_p(b, d - b) < 0.05:
                tot += pd * comb(d, b) * pi ** b * (1 - pi) ** (d - b)
    return tot


A = json.load(open(CUPEL_ROOT + "/results/stepB_analysis.json"))
out = {}
for key in ("primary", "all_pairs"):
    p = A[key]
    n = p["n_pairs"]; d = p["b_ORIGonly"] + p["c_NORMonly"]; q = d / n
    # smallest one-sided split significant at the observed number of discordant pairs
    need = next((b for b in range(d + 1) if mcnemar_p(b, d - b) < 0.05 and b >= d - b), None)
    mde = None
    for i in range(50, 101):
        pi = i / 100
        if power(n, q, pi) >= 0.8:
            mde = {"pi": pi, "effect_pp": round(100 * q * (2 * pi - 1), 1)}
            break
    out[key] = {"n_pairs": n, "discordant": d, "q": round(q, 3),
                "min_split_significant_at_observed_d": f"{need}:{d-need}" if need is not None else None,
                "pass_diff_needed_at_observed_d_pp": round(100 * (2 * need - d) / n, 1) if need is not None else None,
                "effect_for_80pct_power": mde}
json.dump(out, open(CUPEL_ROOT + "/results/power.json", "w"), indent=1)
print(json.dumps(out, indent=1))

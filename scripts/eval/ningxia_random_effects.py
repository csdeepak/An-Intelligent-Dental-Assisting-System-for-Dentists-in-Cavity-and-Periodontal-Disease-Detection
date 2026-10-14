#!/usr/bin/env python
"""Random-effects pooling of the four Ningxia hospitals' lesion-detector-minus-constant differences.

Post hoc sensitivity analysis, 15 Oct 2026 (RESULTS_LOG 2026-10-15), not pre-registered. The
registered figure is the pooled cluster bootstrap in outputs/stage1_switch/stage1_switch_results.json
(+9.28 pp), which treats the four hospitals as fixed. This asks what the same per-hospital
differences say about a hospital not in the sample (Snell, Riley et al., J Clin Epidemiol 2016).

Arithmetic on the saved per-hospital deltas only: no image is read and no model is run. Each
hospital's standard error is approximated from its 95% percentile bootstrap interval as
width / (2 x 1.96). DerSimonian-Laird between-hospital variance; the prediction interval uses a t
distribution on k - 2 degrees of freedom.

    python scripts/eval/ningxia_random_effects.py
"""

import json
import math
from pathlib import Path

from scipy import stats

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "outputs/stage1_switch/stage1_switch_results.json"
OUT = REPO / "outputs/stage1_switch/F_ningxia_random_effects.json"
KEY = "arm3c: lesion-detector_minus_constant-molars"
SITES = ("test1", "test2", "test3", "test4")


def dersimonian_laird(y, se):
    """-> dict with the fixed and random-effects means, Q, I^2, tau, the CI and prediction interval."""
    k, w = len(y), [1 / s ** 2 for s in se]
    fixed = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    q = sum(wi * (yi - fixed) ** 2 for wi, yi in zip(w, y))
    tau2 = max(0.0, (q - (k - 1)) / (sum(w) - sum(wi ** 2 for wi in w) / sum(w)))
    wr = [1 / (s ** 2 + tau2) for s in se]
    mean = sum(wi * yi for wi, yi in zip(wr, y)) / sum(wr)
    se_mean = math.sqrt(1 / sum(wr))
    half_pi = stats.t.ppf(0.975, k - 2) * math.sqrt(tau2 + se_mean ** 2)
    return {"k": k, "fixed_mean_pp": fixed, "q": q, "q_p": 1 - stats.chi2.cdf(q, k - 1),
            "i2_pct": max(0.0, (q - (k - 1)) / q) * 100 if q > 0 else 0.0, "tau_pp": math.sqrt(tau2),
            "mean_pp": mean, "ci95_pp": [mean - 1.96 * se_mean, mean + 1.96 * se_mean],
            "prediction_interval_pp": [mean - half_pi, mean + half_pi]}


def main():
    res = json.loads(SRC.read_text())["F_ningxia_caries_lesion_agreement"]
    deltas = {s: res[s]["deltas"][KEY] for s in SITES}
    y = [deltas[s]["delta_pp"] for s in SITES]
    se = [(deltas[s]["ci95_pp"][1] - deltas[s]["ci95_pp"][0]) / (2 * 1.96) for s in SITES]
    out = {"source": str(SRC.relative_to(REPO)), "comparison": KEY,
           "method": "DerSimonian-Laird random effects; per-site SE = 95% percentile CI width / 3.92; "
                     "prediction interval t(k-2). Post hoc sensitivity analysis, not pre-registered.",
           "per_site": {s: {"delta_pp": deltas[s]["delta_pp"], "ci95_pp": deltas[s]["ci95_pp"]} for s in SITES},
           "registered_pooled": res["pooled"]["deltas"][KEY],
           **{k: (round(v, 4 if k == "q_p" else 2) if isinstance(v, float)
                  else [round(x, 2) for x in v] if isinstance(v, list) else v)
              for k, v in dersimonian_laird(y, se).items()}}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("mean_pp", "ci95_pp", "i2_pct", "tau_pp", "prediction_interval_pp")}))


if __name__ == "__main__":
    # Self-check against a hand-worked case: identical sites -> tau 0, mean = the common value.
    chk = dersimonian_laird([2.0, 2.0, 2.0], [1.0, 1.0, 1.0])
    assert chk["tau_pp"] == 0.0 and abs(chk["mean_pp"] - 2.0) < 1e-12 and chk["i2_pct"] == 0.0
    main()

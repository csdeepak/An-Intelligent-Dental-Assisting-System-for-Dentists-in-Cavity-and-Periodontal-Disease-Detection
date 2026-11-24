#!/usr/bin/env python
"""HKSJ interval and tau^2 uncertainty beside the DerSimonian-Laird pooling of the Ningxia sites.

Post hoc, 2 Nov 2026 (review round 1, item 4; RESULTS_LOG 2026-11-02d). With four sites the
DerSimonian-Laird interval is known to be too narrow; the Hartung-Knapp-Sidik-Jonkman interval
(IntHout, Ioannidis & Borm, BMC Med Res Methodol 2014) rescales the standard error by the observed
dispersion and uses a t distribution on k - 1 degrees of freedom. The truncated variant floors the
rescaling factor at 1, so HKSJ is never narrower than DL. The between-site variance gets a Q-profile
95% interval (Viechtbauer, Stat Med 2007).

Same inputs as scripts/eval/ningxia_random_effects.py (whose output this script does not touch):
the saved per-site deltas, each site's SE approximated as its 95% percentile bootstrap interval
width / 3.92. No image is read and no model is run.

    python scripts/eval/ningxia_random_effects_hksj.py
"""

import json
import math
import sys
from pathlib import Path

from scipy import optimize, stats

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))
from ningxia_random_effects import KEY, SITES, SRC, dersimonian_laird  # noqa: E402

OUT = REPO / "outputs/stage1_switch/F_ningxia_random_effects_hksj.json"


def generalised_q(y, v, tau2):
    w = [1 / (vi + tau2) for vi in v]
    mu = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    return sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y))


def q_profile_tau2(y, v, level=0.95):
    """Viechtbauer's Q-profile interval for tau^2: the tau^2 at which Q(tau^2) meets the chi^2 quantiles."""
    k, a = len(y), (1 - level) / 2
    hi_q, lo_q = float(stats.chi2.ppf(1 - a, k - 1)), float(stats.chi2.ppf(a, k - 1))
    big = 1e6 * max(v) + 1e3 * max(abs(t) for t in y) ** 2

    def solve(target):
        if generalised_q(y, v, 0.0) <= target:
            return 0.0
        return optimize.brentq(lambda t: generalised_q(y, v, t) - target, 0.0, big, xtol=1e-10)

    return solve(hi_q), solve(lo_q)


def hksj(y, v, tau2):
    k = len(y)
    w = [1 / (vi + tau2) for vi in v]
    mu = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y)) / (k - 1)
    t = float(stats.t.ppf(0.975, k - 1))
    se, se_trunc = math.sqrt(q / sum(w)), math.sqrt(max(1.0, q) / sum(w))
    return {"mean_pp": mu, "scale_q": q, "se_pp": se,
            "ci95_pp": [mu - t * se, mu + t * se],
            "ci95_truncated_pp": [mu - t * se_trunc, mu + t * se_trunc],
            "excludes_zero": mu - t * se > 0 or mu + t * se < 0,
            "excludes_zero_truncated": mu - t * se_trunc > 0 or mu + t * se_trunc < 0}


def main():
    res = json.loads(SRC.read_text())["F_ningxia_caries_lesion_agreement"]
    deltas = {s: res[s]["deltas"][KEY] for s in SITES}
    y = [deltas[s]["delta_pp"] for s in SITES]
    se = [(deltas[s]["ci95_pp"][1] - deltas[s]["ci95_pp"][0]) / (2 * 1.96) for s in SITES]
    v = [s ** 2 for s in se]
    dl = dersimonian_laird(y, se)
    tau2 = dl["tau_pp"] ** 2
    hk = hksj(y, v, tau2)
    lo, hi = q_profile_tau2(y, v)
    # I^2 bounds from the tau^2 bounds, with the typical within-site variance of Higgins & Thompson.
    k, w = len(y), [1 / vi for vi in v]
    s2 = (k - 1) * sum(w) / (sum(w) ** 2 - sum(wi ** 2 for wi in w))
    i2 = lambda t2: 100 * t2 / (t2 + s2)  # noqa: E731
    t_pi = float(stats.t.ppf(0.975, k - 2))
    out = {
        "source": SRC.relative_to(REPO).as_posix(), "comparison": KEY,
        "method": "per-site SE = 95% percentile CI width / 3.92 (as ningxia_random_effects.py); "
                  "DL tau^2; HKSJ CI with t(k-1), plain and truncated (scale floored at 1); "
                  "Q-profile 95% CI for tau^2; I^2 bounds via the Higgins-Thompson typical "
                  "within-site variance. Post hoc, not pre-registered.",
        "k": k,
        "dl": {"mean_pp": round(dl["mean_pp"], 2), "ci95_pp": [round(x, 2) for x in dl["ci95_pp"]],
               "tau_pp": round(dl["tau_pp"], 2), "i2_pct": round(dl["i2_pct"], 1),
               "prediction_interval_pp": [round(x, 2) for x in dl["prediction_interval_pp"]]},
        "hksj": {kk: (round(vv, 3) if isinstance(vv, float) else
                      [round(x, 2) for x in vv] if isinstance(vv, list) else vv)
                 for kk, vv in hk.items()},
        "hksj_prediction_interval_pp": [round(hk["mean_pp"] - t_pi * math.sqrt(tau2 + hk["se_pp"] ** 2), 2),
                                        round(hk["mean_pp"] + t_pi * math.sqrt(tau2 + hk["se_pp"] ** 2), 2)],
        "tau_pp_qprofile_ci95": [round(math.sqrt(lo), 2), round(math.sqrt(hi), 2)],
        "i2_pct_ci95": [round(i2(lo), 1), round(i2(hi), 1)],
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    # Self-checks. Identical sites: Q = 0, HKSJ scale 0 (plain interval collapses), truncated = DL.
    h = hksj([2.0, 2.0, 2.0], [1.0, 1.0, 1.0], 0.0)
    assert h["scale_q"] == 0.0 and abs(h["mean_pp"] - 2.0) < 1e-12
    assert q_profile_tau2([2.0, 2.0, 2.0], [1.0, 1.0, 1.0]) == (0.0, 0.0)
    # Q-profile root really solves Q(tau^2) = chi^2 quantile on a dispersed example.
    yy, vv = [0.0, 10.0, 20.0, 5.0], [4.0, 4.0, 9.0, 9.0]
    lo_, hi_ = q_profile_tau2(yy, vv)
    assert abs(generalised_q(yy, vv, hi_) - stats.chi2.ppf(0.025, 3)) < 1e-6 and lo_ < hi_
    main()

import numpy as np


def lifetime_pd(pd_12m, years_remaining):
    """Extend a 12-month PD to a lifetime PD: 1 - (1 - PD)^n."""
    return 1 - (1 - pd_12m) ** years_remaining


def select_pd(stage, pd_12m, pd_lifetime):
    """IFRS 9 rule: Stage 1 uses 12-month PD; Stage 2 and 3 use lifetime PD."""
    return np.where(np.asarray(stage) == 'Stage 1', pd_12m, pd_lifetime)


def calculate_ecl(pd_used, lgd, ead):
    """Expected credit loss = PD x LGD x EAD."""
    return pd_used * lgd * ead


def apply_scenario(pd_used, multiplier):
    """Scale PD by a scenario multiplier, capped at 100% since PD is a probability."""
    return np.clip(pd_used * multiplier, 0, 1)


def weighted_ecl(ecl_by_scenario, probabilities):
    """Probability-weighted ECL across scenarios. Probabilities must sum to 1."""
    if abs(sum(probabilities.values()) - 1.0) > 1e-9:
        raise ValueError("Scenario probabilities must sum to 1.")
    return sum(ecl_by_scenario[s] * p for s, p in probabilities.items())
import pytest
from ecl_engine import lifetime_pd, select_pd, calculate_ecl, apply_scenario, weighted_ecl


def test_lifetime_pd_one_year_equals_12m_pd():
    assert lifetime_pd(0.10, 1) == pytest.approx(0.10)


def test_lifetime_pd_three_years():
    assert lifetime_pd(0.10, 3) == pytest.approx(1 - 0.9 ** 3)


def test_lifetime_pd_never_below_12m_pd():
    assert lifetime_pd(0.05, 4) >= 0.05


def test_select_pd_stage_1_uses_12m():
    assert select_pd(['Stage 1'], 0.05, 0.20)[0] == pytest.approx(0.05)


def test_select_pd_stage_2_uses_lifetime():
    assert select_pd(['Stage 2'], 0.05, 0.20)[0] == pytest.approx(0.20)


def test_calculate_ecl():
    assert calculate_ecl(0.10, 0.50, 1000) == pytest.approx(50.0)


def test_scenario_multiplier_scales_pd():
    assert apply_scenario(0.10, 1.5) == pytest.approx(0.15)


def test_scenario_pd_capped_at_one():
    assert apply_scenario(0.60, 2.5) == pytest.approx(1.0)


def test_weighted_ecl():
    ecl = {'Base': 1000, 'Adverse': 1500, 'Severe': 2500}
    probs = {'Base': 0.60, 'Adverse': 0.30, 'Severe': 0.10}
    assert weighted_ecl(ecl, probs) == pytest.approx(1300)


def test_weighted_ecl_rejects_bad_probabilities():
    ecl = {'Base': 1000, 'Adverse': 1500, 'Severe': 2500}
    with pytest.raises(ValueError):
        weighted_ecl(ecl, {'Base': 0.5, 'Adverse': 0.3, 'Severe': 0.3})
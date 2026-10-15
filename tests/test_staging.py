from staging import assign_stage


def make_row(dpd=0, score_change=0, watchlist=0):
    return {'days_past_due': dpd, 'credit_score_change': score_change, 'watchlist_flag': watchlist}


def test_clean_loan_is_stage_1():
    assert assign_stage(make_row()) == 'Stage 1'


def test_29_dpd_is_still_stage_1():
    assert assign_stage(make_row(dpd=29)) == 'Stage 1'


def test_30_dpd_is_stage_2():
    assert assign_stage(make_row(dpd=30)) == 'Stage 2'


def test_89_dpd_is_stage_2():
    assert assign_stage(make_row(dpd=89)) == 'Stage 2'


def test_90_dpd_is_stage_3():
    assert assign_stage(make_row(dpd=90)) == 'Stage 3'


def test_score_drop_of_30_is_stage_2():
    assert assign_stage(make_row(score_change=-30)) == 'Stage 2'


def test_watchlist_is_stage_2():
    assert assign_stage(make_row(watchlist=1)) == 'Stage 2'


def test_stage_3_takes_priority_over_stage_2():
    assert assign_stage(make_row(dpd=95, score_change=-40, watchlist=1)) == 'Stage 3'
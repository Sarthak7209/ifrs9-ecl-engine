import pandas as pd


def assign_stage(row):
    """
    Assigns IFRS 9 stage to a loan based on days past due,
    credit score deterioration, and watchlist status.
    Rules are evaluated in order of severity: Stage 3 first,
    then Stage 2, defaulting to Stage 1.
    """
    if row['days_past_due'] >= 90:
        return 'Stage 3'
    elif (row['days_past_due'] >= 30) or (row['credit_score_change'] <= -30) or (row['watchlist_flag'] == 1):
        return 'Stage 2'
    else:
        return 'Stage 1'


def apply_staging(df):
    """Applies assign_stage to every row of a DataFrame and returns it with a new 'stage' column."""
    df = df.copy()
    df['stage'] = df.apply(assign_stage, axis=1)
    return df
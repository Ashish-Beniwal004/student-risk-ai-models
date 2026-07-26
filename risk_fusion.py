def compute_final_risk_score(dropout_score, wellbeing_score, depression_score,
                               weights=None):
    """
    Combines the three independent model scores (each 0-100) into
    one unified risk score (0-100).

    Any score can be None if that model didn't produce output for
    this student (e.g. missing data) — weights are renormalized
    across whatever scores ARE available.
    """
    if weights is None:
        weights = {'dropout': 0.4, 'wellbeing': 0.3, 'depression': 0.3}

    scores = {
        'dropout': dropout_score,
        'wellbeing': wellbeing_score,
        'depression': depression_score
    }

    # Keep only the scores that actually exist
    available = {k: v for k, v in scores.items() if v is not None}

    if not available:
        raise ValueError("No model scores available to compute risk score.")

    # Renormalize weights so they sum to 1 across available scores only
    total_weight = sum(weights[k] for k in available)
    final_score = sum(available[k] * (weights[k] / total_weight) for k in available)

    return round(final_score, 2)
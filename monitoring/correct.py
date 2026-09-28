"""Bias-corrected failure prevalence for a monitoring period."""

from __future__ import annotations

from typing import Any, Sequence


def corrected_mode_prevalence(
    sample_preds: Sequence[int],
    test_labels: Sequence[int],
    test_preds: Sequence[int],
    confidence: float = 0.95,
    bootstrap_iterations: int = 20000,
    seed: int | None = 7,
) -> dict[str, Any]:
    """Bias-corrected live prevalence for one mode from sampled verdicts.

    The contract, precisely:

      1. ``raw`` is the uncorrected flag rate: ``mean(sample_preds)``.
      2. Compute the frozen judge's failure sensitivity and pass specificity
         from ``test_labels`` and ``test_preds``. Both use the monitoring
         convention that 1 means a failure is present. Failure sensitivity is
         the flagged fraction of human-labeled failures. Pass specificity is
         the unflagged fraction of human-labeled passes.
      3. Compute the Rogan-Gladen point estimate, then resample the held-out
         records and sampled predictions to obtain a percentile-bootstrap
         interval. Use a seeded NumPy generator so the committed result is
         reproducible.
      4. Resample the monitoring predictions and the paired held-out records
         independently with replacement. Keep their original sample sizes.
         Discard a draw if the correction cannot be computed. Clamp each
         retained estimate to [0, 1], then take the percentile interval.
         Raise ``ValueError`` if no replicate is valid.

    Args:
        sample_preds: the judge's 0/1 verdicts over the UNIFORM BASE sample
            only (never the risk strata; they are biased toward failure by
            design).
        test_labels: human labels for the frozen Homework 5 judge's test
            split.
        test_preds: the frozen judge's predictions on that test split.
        confidence: interval confidence level.
        bootstrap_iterations: number of percentile-bootstrap replicates.
        seed: numpy seed for a reproducible interval; None leaves the RNG
            untouched.

    Returns:
        {"raw", "corrected", "ci_low", "ci_high", "confidence",
         "failure_sensitivity", "pass_specificity", "n_sample"}
        with "corrected" clamped to [0, 1] and rates rounded to 4 places.

    Raises:
        ValueError: if an input is empty, the held-out inputs have different
            lengths, a value is not 0 or 1, a class is absent, the judge is
            missing a usable correction, or no bootstrap replicate is valid.
    """
    import numpy as np

    arrays = [np.asarray(values, dtype=float) for values in
              (sample_preds, test_labels, test_preds)]
    if any(a.ndim != 1 or not a.size or not np.isin(a, [0, 1]).all() for a in arrays):
        raise ValueError("inputs must be nonempty one-dimensional binary sequences")
    sample, labels, predictions = arrays
    if labels.size != predictions.size:
        raise ValueError("held-out labels and predictions must have equal lengths")
    if not 0 < confidence < 1 or not isinstance(bootstrap_iterations, int) or bootstrap_iterations < 1:
        raise ValueError("invalid confidence or bootstrap iteration count")

    def rates(y, p):
        positive, negative = y == 1, y == 0
        if not positive.any() or not negative.any():
            return None
        sensitivity = float(p[positive].mean())
        specificity = float((1 - p[negative]).mean())
        denominator = sensitivity + specificity - 1
        if abs(denominator) < 1e-12:
            return None
        return sensitivity, specificity, denominator

    measured = rates(labels, predictions)
    if measured is None:
        raise ValueError("both classes and a nonzero correction denominator are required")
    sensitivity, specificity, denominator = measured
    raw = float(sample.mean())
    corrected = float(np.clip((raw + specificity - 1) / denominator, 0, 1))
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(bootstrap_iterations):
        test_indices = rng.integers(0, labels.size, labels.size)
        sample_indices = rng.integers(0, sample.size, sample.size)
        bootstrap_rates = rates(labels[test_indices], predictions[test_indices])
        if bootstrap_rates is None:
            continue
        _, sp, denom = bootstrap_rates
        estimates.append(float(np.clip((sample[sample_indices].mean() + sp - 1) / denom, 0, 1)))
    if not estimates:
        raise ValueError("no valid bootstrap replicates")
    low, high = np.quantile(estimates, [(1 - confidence) / 2, (1 + confidence) / 2])
    return {"raw": round(raw, 4), "corrected": round(corrected, 4),
            "ci_low": round(float(low), 4), "ci_high": round(float(high), 4),
            "confidence": confidence, "failure_sensitivity": round(sensitivity, 4),
            "pass_specificity": round(specificity, 4), "n_sample": int(sample.size)}

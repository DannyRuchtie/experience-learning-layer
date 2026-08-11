from __future__ import annotations

import pytest

from ell.statistics import empirical_quantile


def test_empirical_quantile_uses_nearest_rank_without_interpolation() -> None:
    values = [0.4, 0.1, 0.3, 0.2, 0.5]
    assert empirical_quantile(values, 0.5) == 0.3
    assert empirical_quantile(values, 0.95) == 0.5
    assert empirical_quantile(values, 0.999) == 0.5


def test_empirical_quantile_rejects_empty_or_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="at least one"):
        empirical_quantile([], 0.95)
    with pytest.raises(ValueError, match="probability"):
        empirical_quantile([0.1], 0.0)

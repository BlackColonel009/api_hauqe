from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.services.veille_service import WatchService


def test_certification_alert_days_are_sorted_and_deduplicated():
    assert WatchService.normalize_certification_expiration_alert_days(
        [30, 120, 0, 30]
    ) == [120, 30, 0]


def test_certification_alert_days_require_day_j():
    with pytest.raises(HTTPException) as exc:
        WatchService.normalize_certification_expiration_alert_days([90, 30])

    assert exc.value.status_code == 422
    assert "jour J" in str(exc.value.detail)


def test_certification_thresholds_keep_critical_expiration():
    thresholds = WatchService.certification_expiration_thresholds([120, 45, 0])

    assert [item["days"] for item in thresholds] == [120, 45, 0]
    assert thresholds[-1]["niveau"] == 4
    assert thresholds[-1]["code"] == "CERT_J0"

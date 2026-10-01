from datetime import date
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook

from app.services import bnec_report_service as reports


@pytest.mark.parametrize(
    ("kind", "year", "month", "quarter", "start", "end", "label"),
    [
        ("MENSUEL", 2028, 2, None, "2028-02-01", "2028-02-29", "02/2028"),
        ("TRIMESTRIEL", 2026, None, 3, "2026-07-01", "2026-09-30", "T3 2026"),
        ("ANNUEL", 2027, None, None, "2027-01-01", "2027-12-31", "2027"),
    ],
)
def test_period_bounds(kind, year, month, quarter, start, end, label):
    actual = reports.validate_period(kind, year, month, quarter)
    assert (actual[0].isoformat(), actual[1].isoformat(), actual[2]) == (start, end, label)


@pytest.mark.parametrize("args", [("MENSUEL", 2026, None, None), ("TRIMESTRIEL", 2026, None, 5), ("ANNUEL", 1999, None, None)])
def test_invalid_period_rejected(args):
    with pytest.raises(HTTPException) as exc:
        reports.validate_period(*args)
    assert exc.value.status_code == 422


def test_report_rows_explain_indicators_without_technical_keys():
    rows = reports.readable_rows({
        "generated_at": "now", "period": {"label": "09/2026"},
        "kpis": [
            {"key": "submitted_collection_forms", "label": "Fiches soumises", "value": 4,
             "previous_value": 2, "delta": 2},
            {"key": "integrations_completed", "label": "Intégrations BNEC", "value": 1},
        ],
        "verification": {"opened": 3, "closed": 2},
    }, "MENSUEL", "09/2026")
    assert "4 fiche(s) de collecte" in rows[0][1]
    assert any(label == "Chiffres à retenir — Fiches soumises" and "mois précédent : 2" in value
               and "Fiches de collecte soumises" in value for label, value in rows)
    assert ("Vérification documentaire — Dossiers de vérification clôturés",
            "2. Vérifications terminées pendant la période.") in rows
    assert not any("submitted_forms" in label or "Indicateurs clés 1" in label
                   or "generated_at" in label for label, _ in rows)


def test_annual_preview_marks_partial_year_and_missing_infc():
    data = {
        "kpis": [
            {"key": "new_certifications", "label": "Nouvelles certifications", "value": 6},
            {"key": "integrations_completed", "label": "Intégrations BNEC", "value": 6},
        ],
        "quarterly_certifications": [
            {"period": "2026-T3", "value": 6}, {"period": "2026-T4", "value": 0},
        ],
        "quarterly_infc": [
            {"period": "2026-T2", "value": None},
            {"period": "2026-T3", "value": "91.70"},
            {"period": "2026-T4", "value": None},
        ],
    }
    rows = reports.readable_rows(data, "ANNUEL", "2026", as_of=date(2026, 10, 1))
    assert "Bilan provisoire arrêté au 01/10/2026" in rows[0][1]
    assert ("INFC moyen — 2026-T2", "Aucun résultat INFC validé pour ce trimestre.") in rows
    assert any(label == "Certifications enregistrées — 2026-T4" and "trimestre en cours" in value
               for label, value in rows)
    rows_before_fourth_quarter = reports.readable_rows(data, "ANNUEL", "2026", as_of=date(2026, 9, 30))
    assert not any("2026-T4" in label for label, _ in rows_before_fourth_quarter)


def test_three_formats_contain_same_server_result():
    rows = [("Nouvelles certifications", "12"), ("INFC moyen", "82,50")]
    csv_data = reports.render_csv("Bilan mensuel BNEC", "09/2026", rows).decode("utf-8-sig")
    assert "09/2026" in csv_data and "Nouvelles certifications;12" in csv_data
    workbook = load_workbook(BytesIO(reports.render_xlsx("Bilan mensuel BNEC", "09/2026", rows)))
    assert workbook.active["A5"].value == "Nouvelles certifications"
    assert workbook.active["B5"].value == "12"
    pdf_data = reports.render_pdf("Bilan mensuel BNEC", "09/2026", rows)
    assert pdf_data.startswith(b"%PDF-") and len(pdf_data) > 1000


@pytest.mark.asyncio
async def test_build_uses_corresponding_server_dashboard(monkeypatch):
    called = []

    class Dashboard:
        def model_dump(self, *, mode):
            assert mode == "json"
            return {"kpis": [{"key": "submitted_collection_forms", "label": "Fiches soumises", "value": 3},
                             {"key": "integrations_completed", "label": "Intégrations BNEC", "value": 1}]}

    async def tactical(db, *, year, month):
        called.append((year, month))
        return Dashboard()

    monkeypatch.setattr(reports.DashboardService, "tactical", tactical)
    result = await reports.BnecReportService.build(None, kind="MENSUEL", year=2026, month=9, quarter=None)
    assert called == [(2026, 9)]
    assert result["start"] == "2026-09-01"
    assert any(label == "Chiffres à retenir — Fiches soumises" and value.startswith("3.")
               for label, value in result["rows"])


@pytest.mark.asyncio
async def test_generate_archives_file_and_metadata(monkeypatch, tmp_path):
    class Session:
        def __init__(self):
            self.added = []
            self.committed = False

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            for value in self.added:
                if value.id is None:
                    value.id = uuid4()

        async def commit(self):
            self.committed = True

        async def refresh(self, value):
            pass

        async def rollback(self):
            pass

    async def build(*args, **kwargs):
        return {"title": "Bilan mensuel BNEC", "period_label": "09/2026", "start": "2026-09-01", "end": "2026-09-30", "rows": [("Fiches soumises", "3")]}

    async def audit(*args, **kwargs):
        pass

    monkeypatch.setattr(reports.BnecReportService, "build", build)
    monkeypatch.setattr(reports, "storage_root", lambda: tmp_path)
    monkeypatch.setattr(reports, "write_audit_event", audit)
    monkeypatch.setattr(reports.GovernanceService, "report_response", lambda value: value)
    session = Session()
    result = await reports.BnecReportService.generate(
        session, kind="MENSUEL", year=2026, month=9, quarter=None, format="CSV",
        actor=SimpleNamespace(user=SimpleNamespace(id=uuid4())),
        request=SimpleNamespace(client=SimpleNamespace(host="127.0.0.1")),
    )
    assert session.committed
    assert result.statut == "GENERE" and result.periode_debut == "2026-09-01"
    assert result.document_id == session.added[0].id
    assert session.added[0].ressource_id == result.id
    assert len(list(tmp_path.glob("*.csv"))) == 1

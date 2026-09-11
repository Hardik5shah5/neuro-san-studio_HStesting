import json

from apps.neuro_san_status.status_dashboard import parse_process_lines
from apps.neuro_san_status.status_dashboard import read_latest_corep_finrep_result
from apps.neuro_san_status.status_dashboard import summarize_runtime_status


def test_parse_process_lines_filters_runtime_processes():
    sample = [
        " 1234  1 python python -m neuro_san_studio run",
        " 3936 3921 python /venv/bin/python -u -m uvicorn nsflow.backend.main:app --host localhost --port 4173",
        " 3939 3921 python /venv/bin/python -u -m neuro_san_studio.runner.neuro_san_server_wrapper --http_port 8080",
        " 5000 1 python something_else",
    ]

    parsed = parse_process_lines(sample)

    assert len(parsed) == 3
    assert any("python -m neuro_san_studio run" in line for line in parsed)
    assert any("nsflow.backend.main" in line for line in parsed)
    assert any("neuro_san_server_wrapper" in line for line in parsed)


def test_summarize_runtime_status_reports_running_when_targets_present():
    sample = [
        " 1234  1 python python -m neuro_san_studio run",
        " 3936 3921 python /venv/bin/python -u -m uvicorn nsflow.backend.main:app --host localhost --port 4173",
    ]

    status = summarize_runtime_status(sample)

    assert status["status"] == "RUNNING"
    assert status["server_command_active"] is True
    assert status["nsflow_client_active"] is True
    assert status["server_component_active"] is False


def test_read_latest_corep_finrep_result_parses_controller_response(tmp_path, monkeypatch):
    log = tmp_path / "nsflow.log"
    response = {
        "message": {
            "type": "AI",
            "text": "# Summary\n**Run ID:** `DEMO-001`  \n**Reporting Date (As-Of):** `2026-08-31`  \n**Entity Scope:** `DEMO_BANK`  \n**Overall Run Release Status:** **`BLOCKED` / SUBMISSION PROHIBITED**\n\n---\n\n**GATE-01** | **PASS**\n**GATE-02** | **FAIL**\nBRK-20260831-001",
        }
    }
    log.write_text(f"industry/corep_finrep_stp Streaming response sent: {json.dumps(response)}\n")
    monkeypatch.setattr("apps.neuro_san_status.status_dashboard.LOGS_DIR", tmp_path)

    result = read_latest_corep_finrep_result()

    assert result["available"] is True
    assert result["runId"] == "DEMO-001"
    assert result["status"] == "BLOCKED"
    assert result["submission"] == "Prohibited"

"""Project-native runtime status dashboard for Neuro SAN Studio."""

from __future__ import annotations

import json
import re
import socket
import subprocess
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List

from flask import Flask
from flask import jsonify
from flask import render_template_string

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "logs"

app = Flask(__name__)


@app.after_request
def allow_react_output_origin(response):
    """Allow the separate Vite output page to read the live result API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def parse_process_lines(lines: Iterable[str]) -> List[str]:
    """Return only the process lines relevant to the current Neuro SAN runtime."""
    filtered: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(token in stripped for token in ["python -m neuro_san_studio run", "nsflow.backend.main", "neuro_san_server_wrapper"]):
            filtered.append(stripped)
    return filtered


def summarize_runtime_status(process_lines: Iterable[str] | None = None) -> Dict[str, bool | str]:
    """Build a compact diagnostic summary for the Neuro SAN runtime."""
    process_lines = list(process_lines) if process_lines is not None else get_process_lines()
    parsed = parse_process_lines(process_lines)
    server_command_active = any("python -m neuro_san_studio run" in line for line in parsed)
    nsflow_client_active = any("nsflow.backend.main" in line for line in parsed)
    server_component_active = any("neuro_san_server_wrapper" in line for line in parsed)
    status = "RUNNING" if server_command_active or nsflow_client_active or server_component_active else "STOPPED"
    return {
        "status": status,
        "server_command_active": server_command_active,
        "nsflow_client_active": nsflow_client_active,
        "server_component_active": server_component_active,
    }


def get_process_lines() -> List[str]:
    """Query the current process table for the active runtime processes."""
    result = subprocess.run(
        ["ps", "-eo", "pid,ppid,comm,args", "--no-headers"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.splitlines()


def port_is_open(host: str, port: int) -> bool:
    """Check whether a TCP port is accepting connections."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def read_recent_log(path: Path, lines: int = 40) -> str:
    """Return the most recent N lines from a log file."""
    if not path.exists():
        return "No log file found yet."
    content = path.read_text(errors="replace").splitlines()
    if not content:
        return "Log file is empty."
    return "\n".join(content[-lines:])


def read_latest_corep_finrep_result() -> Dict[str, object]:
    """Extract the latest controller response for the React output view."""
    log_path = LOGS_DIR / "nsflow.log"
    if not log_path.exists():
        return {"available": False, "message": "No nsflow log is available yet."}

    response_text = None
    for line in reversed(log_path.read_text(errors="replace").splitlines()):
        if "Streaming response sent:" not in line or "industry/corep_finrep_stp" not in line:
            continue
        payload = line.split("Streaming response sent:", 1)[1].strip()
        try:
            response_text = json.loads(payload)["message"]["text"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        break

    if not response_text:
        return {"available": False, "message": "No completed COREP/FINREP response found yet."}

    def match(pattern: str, default: str) -> str:
        result = re.search(pattern, response_text, re.IGNORECASE)
        return result.group(1).strip() if result else default

    gate_rows = re.findall(r"(GATE-\d+).*?\|\s*\*\*(PASS|FAIL)\*\*", response_text)
    break_ids = sorted(set(re.findall(r"BRK-\d{8}-\d{3}", response_text)))
    status = match(r"Overall Run Release Status:.*?`([^`]+)`", "UNKNOWN")
    submission = "Prohibited" if "SUBMISSION PROHIBITED" in response_text else status.title()
    return {
        "available": True,
        "runId": match(r"Run ID:\*\*\s*`([^`]+)", "Unknown"),
        "reportDate": match(r"Reporting Date \(As-Of\):\*\*\s*`([^`]+)", "Unknown"),
        "entity": match(r"Entity Scope:\*\*\s*`([^`]+)", "Unknown"),
        "status": status,
        "submission": submission,
        "controlsPassed": f"{sum(result == 'PASS' for _, result in gate_rows)}/{len(gate_rows)}" if gate_rows else "Unknown",
        "breaksOpen": len(break_ids),
        "controls": [{"id": gate_id, "result": result, "description": "Release gate evaluated by the controller."} for gate_id, result in gate_rows],
        "approvals": [
            {"label": "Maker-checker decision", "value": "Rejected" if "REJECTED" in response_text else "Approved"},
            {"label": "Submission release", "value": "Blocked" if "SUBMISSION PROHIBITED" in response_text else "Approved"},
        ],
        "response": response_text,
    }


@app.route("/")
def index():
    """Render the runtime dashboard."""
    runtime = summarize_runtime_status()
    status = runtime["status"]
    status_color = "green" if status == "RUNNING" else "red"
    process_lines = parse_process_lines(get_process_lines())
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8" />
            <title>Neuro SAN Studio Status</title>
            <style>
                body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
                h1 { margin-bottom: 8px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }
                .card { background: #111827; border: 1px solid #334155; border-radius: 10px; padding: 16px; }
                .ok { color: #4ade80; font-weight: bold; }
                .bad { color: #f87171; font-weight: bold; }
                pre { background: #020817; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; overflow: auto; white-space: pre-wrap; }
                .meta { color: #94a3b8; }
            </style>
        </head>
        <body>
            <h1>Neuro SAN Studio Status</h1>
            <p class="meta">Project-native runtime dashboard for the current Neuro SAN session.</p>
            <div class="grid">
                <div class="card">
                    <div class="meta">Overall status</div>
                    <div style="color: {{ status_color }}; font-size: 2rem; font-weight: bold;">{{ status }}</div>
                </div>
                <div class="card">
                    <div class="meta">Server command</div>
                    <div class="{{ 'ok' if runtime['server_command_active'] else 'bad' }}">{{ 'Active' if runtime['server_command_active'] else 'Inactive' }}</div>
                </div>
                <div class="card">
                    <div class="meta">NSFlow client</div>
                    <div class="{{ 'ok' if runtime['nsflow_client_active'] else 'bad' }}">{{ 'Active' if runtime['nsflow_client_active'] else 'Inactive' }}</div>
                </div>
                <div class="card">
                    <div class="meta">Server component</div>
                    <div class="{{ 'ok' if runtime['server_component_active'] else 'bad' }}">{{ 'Active' if runtime['server_component_active'] else 'Inactive' }}</div>
                </div>
            </div>

            <h2>Runtime checks</h2>
            <ul>
                <li>main launch command: <span class="{{ 'ok' if runtime['server_command_active'] else 'bad' }}">{{ '✅ running' if runtime['server_command_active'] else '❌ not running' }}</span></li>
                <li>nsflow client: <span class="{{ 'ok' if runtime['nsflow_client_active'] else 'bad' }}">{{ '✅ running' if runtime['nsflow_client_active'] else '❌ not running' }}</span></li>
                <li>neuro-san server wrapper: <span class="{{ 'ok' if runtime['server_component_active'] else 'bad' }}">{{ '✅ running' if runtime['server_component_active'] else '❌ not running' }}</span></li>
                <li>HTTP port 8080: <span class="{{ 'ok' if port_is_open('127.0.0.1', 8080) else 'bad' }}">{{ '✅ open' if port_is_open('127.0.0.1', 8080) else '❌ closed' }}</span></li>
                <li>NSFlow port 4173: <span class="{{ 'ok' if port_is_open('127.0.0.1', 4173) else 'bad' }}">{{ '✅ open' if port_is_open('127.0.0.1', 4173) else '❌ closed' }}</span></li>
            </ul>

            <div class="grid">
                <div class="card">
                    <h3>Server log</h3>
                    <pre>{{ read_recent_log(LOGS_DIR / 'server.log') }}</pre>
                </div>
                <div class="card">
                    <h3>NSFlow log</h3>
                    <pre>{{ read_recent_log(LOGS_DIR / 'nsflow.log') }}</pre>
                </div>
            </div>

            <h2>Process list</h2>
            <pre>{{ '\n'.join(process_lines) if process_lines else 'No matching Neuro SAN or NSFlow processes were found.' }}</pre>
        </body>
        </html>
        """,
        status=status,
        status_color=status_color,
        runtime=runtime,
        LOGS_DIR=LOGS_DIR,
        process_lines=process_lines,
        port_is_open=port_is_open,
        read_recent_log=read_recent_log,
    )


@app.route("/api/status")
def status_api():
    """Return the runtime status as JSON for UI integrations."""
    return jsonify(summarize_runtime_status())


@app.route("/api/corep-finrep")
def corep_finrep_api():
    """Return the latest completed COREP/FINREP controller response."""
    return jsonify(read_latest_corep_finrep_result())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8502, debug=False)

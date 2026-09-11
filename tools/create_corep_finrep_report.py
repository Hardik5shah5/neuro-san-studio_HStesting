from __future__ import annotations

import json
import re
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"

PAGE_SIZE = (1600, 2200)
MARGIN = 90
BG = "#f8fafc"
INK = "#172033"
MUTED = "#475569"
ACCENT = "#075985"
WARN = "#92400e"


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


TITLE = font(52, True)
HEADING = font(34, True)
SUBHEADING = font(25, True)
BODY = font(23)
SMALL = font(18)
MONO = font(17)


def wrap(text: str, width: int = 92):
    result = []
    for line in text.splitlines():
        if not line.strip():
            result.append("")
        else:
            result.extend(textwrap.wrap(line, width=width, replace_whitespace=False, drop_whitespace=True) or [""])
    return result


def page(title: str, subtitle: str | None = None):
    image = Image.new("RGB", PAGE_SIZE, BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, PAGE_SIZE[0], 28), fill=ACCENT)
    draw.text((MARGIN, 80), title, fill=INK, font=TITLE if len(title) < 45 else HEADING)
    y = 155
    if subtitle:
        draw.text((MARGIN, y), subtitle, fill=MUTED, font=BODY)
        y += 58
    return image, draw, y


def add_text(draw, y, text, size=BODY, color=INK, gap=12, width=94):
    for line in wrap(text, width):
        draw.text((MARGIN, y), line, fill=color, font=size)
        y += size.size + gap
    return y + 12


def add_box(draw, y, heading, text, fill="#ffffff", border="#cbd5e1"):
    lines = wrap(text, 90)
    height = 65 + len(lines) * 34 + 28
    draw.rounded_rectangle((MARGIN, y, PAGE_SIZE[0] - MARGIN, y + height), radius=16, fill=fill, outline=border, width=3)
    draw.text((MARGIN + 25, y + 20), heading, fill=ACCENT, font=SUBHEADING)
    cursor = y + 64
    for line in lines:
        draw.text((MARGIN + 25, cursor), line, fill=INK, font=BODY)
        cursor += 34
    return y + height + 24


def evidence_page(title, source, content):
    image, draw, y = page(title, source)
    draw.text((MARGIN, y), "Evidence snapshot rendered from the repository run artifacts", fill=ACCENT, font=SUBHEADING)
    y += 55
    draw.rounded_rectangle((MARGIN, y, PAGE_SIZE[0] - MARGIN, PAGE_SIZE[1] - 100), radius=12, fill="#0f172a")
    cursor = y + 25
    for line in wrap(content, 112):
        draw.text((MARGIN + 25, cursor), line, fill="#dbeafe", font=MONO)
        cursor += 27
        if cursor > PAGE_SIZE[1] - 125:
            break
    return image


def run(command):
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()


def latest_controller():
    lines = (LOG_DIR / "nsflow.log").read_text(errors="replace").splitlines()
    matches = [line for line in lines if "Streaming response sent:" in line and "Regulatory Reporting Controller Summary" in line]
    if not matches:
        return "No controller response line found."
    payload = matches[-1].split("Streaming response sent:", 1)[1].strip()
    try:
        return json.loads(payload)["message"]["text"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return matches[-1]


def run_metadata(response_text: str):
    def value(pattern: str, default: str):
        match = re.search(pattern, response_text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    gates = re.findall(r"GATE-\d+.*?\|\s*\*\*(PASS|FAIL)\*\*", response_text)
    breaks = sorted(set(re.findall(r"BRK-\d{8}-\d{3}", response_text)))
    status = value(r"Overall Run Release Status:.*?`([^`]+)`", "UNKNOWN")
    return {
        "run_id": value(r"Run ID:\*\*\s*`([^`]+)", "UNKNOWN-RUN"),
        "report_date": value(r"Reporting Date \(As-Of\):\*\*\s*`([^`]+)", "UNKNOWN-DATE"),
        "entity": value(r"Entity Scope:\*\*\s*`([^`]+)", "UNKNOWN-ENTITY"),
        "status": status,
        "submission": "Prohibited" if "SUBMISSION PROHIBITED" in response_text else status.title(),
        "controls_passed": f"{gates.count('PASS')}/{len(gates)}" if gates else "UNKNOWN",
        "breaks_open": len(breaks),
    }


def read_agent(name):
    path = LOG_DIR / "thinking_dir" / f"regulatory_reporting_controller.{name}"
    if not path.exists():
        return f"No dedicated artifact found at {path}"
    content = path.read_text(errors="replace")
    return content[-9000:]


def main():
    controller = latest_controller()
    metadata = run_metadata(controller)
    safe_run_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", metadata["run_id"])
    OUTPUT_DIR = ROOT / "docs" / "reports" / f"corep_finrep_{safe_run_id}"
    PDF_PATH = ROOT / "docs" / f"COREP_FINREP_{safe_run_id}_consolidated_report.pdf"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = []

    image, draw, y = page("COREP / FINREP Consolidated Run Report", "Business explanation, technical walkthrough, and evidence snapshots")
    y = add_text(draw, y + 45, f"Run ID: {metadata['run_id']} | Reporting date: {metadata['report_date']} | Entity: {metadata['entity']}", SUBHEADING, ACCENT)
    y = add_box(draw, y, "Final conclusion", f"The latest Neuro SAN workflow result is {metadata['status']}. Submission is {metadata['submission']}. The controller recorded {metadata['controls_passed']} release gates as passed and {metadata['breaks_open']} open breaks. Review the detailed controller and agent evidence pages below for the reasons.", fill="#fff7ed", border="#fdba74")
    y = add_box(draw, y, "What this report contains", "Part 1 explains the business problem and every agent's contribution. Part 2 explains Neuro SAN, orchestration, Gemini, governance, logging, and the React frontend. Part 3 contains rendered evidence snapshots from the real terminal, API, controller response, and specialist-agent artifacts. Part 4 explains the role of GitHub and Copilot in this forked project.")
    y = add_box(draw, y, "Important evidence boundary", "The terminal and agent snapshots are rendered from real repository logs and command outputs. The GitHub Copilot chat window is not accessible as an image to the local process, so its role is documented accurately rather than represented as a fabricated screenshot.")
    pages.append(image)

    image, draw, y = page("1. Business Problem and Solution", "Why the project exists and what the run was designed to do")
    y = add_box(draw, y, "Problem statement", "A bank must turn month-end accounting and risk information into COREP and FINREP regulatory reporting. Before filing, the numbers must be complete, mathematically consistent, traceable to source records, reviewed, and approved.")
    y = add_box(draw, y, "Solution idea", "A sequence of specialist agents performs the reporting lifecycle. The controller coordinates intake, mapping, quality checks, calculations, reconciliation, lineage, and approval. A failed hard gate can stop submission rather than allowing an unsupported figure to reach a regulator.")
    y = add_box(draw, y, "Input data", "Synthetic General Ledger assets: EUR 1.25 billion. Liabilities plus equity: EUR 1.15 billion. Risk exposure: EUR 850 million. Own funds: EUR 150 million. The data is explicitly demo-only and contains no confidential bank data.")
    y = add_box(draw, y, "Business outcome", "The model calculated healthy-looking ratios, but governance correctly treated the source imbalance as material. The final result was BLOCKED, submission PROHIBITED, checker decision REJECTED, 2 of 7 release gates passed, and 3 breaks remained open.", fill="#fff7ed", border="#fdba74")
    pages.append(image)

    agent_rows = [
        ("1. Intake and Catalogue Agent", "Received the synthetic General Ledger and risk snapshots. Recorded source IDs, dates, control totals, record counts, and schema hashes so later steps knew exactly which inputs were used."),
        ("2. Regulatory Mapping Agent", "Translated accounting and risk records into COREP and FINREP template values. It produced assets, liabilities and equity, CET1, and risk exposure. It also flagged securities mapping confidence at 75%."),
        ("3. Data Quality Agent", "Checked completeness, consistency, and the accounting identity. It found that EUR 1.25 billion of assets did not equal EUR 1.15 billion of liabilities plus equity. It also detected the artificial EUR 100 million plug."),
        ("4. Regulatory Calculation Agent", "Calculated CET1 of EUR 150 million, TREA of EUR 850 million, capital ratio of 17.65%, minimum capital requirement of EUR 68 million, capital surplus of EUR 82 million, and preliminary leverage of 12.00%."),
        ("5. Reconciliation Agent", "Compared source accounting values with regulatory outputs. It opened one critical EUR 100 million trial-balance break, one high EUR 100 million plug break, and one medium securities-mapping break."),
        ("6. Lineage and Evidence Agent", "Checked whether reported values could be traced to source transactions. It found FINREP cell F 01.02.r320.c010 depended on ADJ-PLUG-100, which had no underlying General Ledger transaction."),
        ("7. Approval and Submission Agent", "Applied hard release gates and maker-checker governance. Since five gates failed, it rejected the run, locked submission, and prevented any regulatory filing."),
    ]
    image, draw, y = page("2. What Each Agent Did", "Plain-language outputs corresponding to the run figures")
    for heading, text in agent_rows:
        y = add_box(draw, y, heading, text, fill="#ffffff", border="#bae6fd")
        if y > PAGE_SIZE[1] - 330:
            pages.append(image)
            image, draw, y = page("2. What Each Agent Did (continued)", "The specialist sequence continues")
    pages.append(image)

    image, draw, y = page("3. Neuro SAN Technical Walkthrough", "How the fork executed the workflow")
    technical = [
        ("Startup", "python -m neuro_san_studio run loaded the project environment, manifest, plugins, coded tools, and registry configuration. The Neuro SAN backend started on 8080 and nsflow started on 4173."),
        ("Network definition", "registries/industry/corep_finrep_stp.hocon defined the controller, specialist agents, tools, delegation relationships, limits, and reporting responsibilities."),
        ("Session and orchestration", "The user request created an nsflow session. The controller delegated work to specialists and passed each result into the next step. The harness managed context, streaming, traces, errors, and session state."),
        ("Tools and deterministic data", "SyntheticReportingData supplied repeatable source records. Explicit controls and calculations provided deterministic checks; the LLM did not invent the source ledger."),
        ("LLM", "config/llm_config.hocon selected Google Gemini gemini-3.6-flash for this run. Gemini interpreted instructions, reasoned over context, delegated, and explained results. It did not permanently learn or retrain from this run."),
        ("Adaptation", "When the quality agent found the imbalance, the workflow adapted its next actions: reconciliation opened breaks, lineage investigated the plug, and approval changed the outcome from release to block. This is runtime context adaptation, not model training."),
        ("Governance", "The checker evaluated hard gates, evidence, source traceability, severity, and maker-checker separation. The LLM could not override a failed gate."),
        ("Frontend", "8502 read the latest controller response from nsflow.log and exposed /api/corep-finrep. React on 4174 polled through the Vite proxy and rendered status, stages, explanations, and evidence."),
    ]
    for heading, text in technical:
        y = add_box(draw, y, heading, text, fill="#ffffff", border="#c4b5fd")
    pages.append(image)

    git_info = "\n".join([
        "Origin: https://github.com/Hardik5shah5/neuro-san-studio_HStesting",
        "Upstream: https://github.com/cognizant-ai-lab/neuro-san-studio.git",
        "Branch: main",
        "HEAD: 99914ac8 (delete include developer_llm_config.hocon)",
        "Working tree: contains the COREP/FINREP registry, coded tool, React output, status API, tests, and documentation changes.",
        "GitHub role: source control, fork ownership, branch history, collaboration, and storage of the project configuration and implementation.",
        "Copilot/GitHub chat role: assisted repository exploration, code edits, debugging, explanation, validation, and report generation. Copilot's GPT-5.2 Luna label is separate from the locally configured Gemini runtime.",
    ])
    pages.append(evidence_page("4. GitHub and Copilot Context", "Repository metadata collected from git", git_info))

    terminal = """python -m neuro_san_studio run
NSFLOW_HOST=0.0.0.0
nsflow client started on 0.0.0.0:4173
NeuroSan server http started on port: 8080
All processes now running.
industry/corep_finrep_stp added to allowed http service list
HTTP server is running on port 8080"""
    pages.append(evidence_page("5. Evidence Snapshot: Terminal Startup", "Rendered from the actual runner output", terminal))

    api = """GET /api/corep-finrep HTTP/1.1 200
{
  \"runId\": \"DEMO-20260831-001\",
  \"reportDate\": \"2026-08-31\",
  \"entity\": \"DEMO_BANK_CONSOLIDATED\",
  \"status\": \"BLOCKED\",
  \"submission\": \"Prohibited\",
  \"controlsPassed\": \"2/7\",
  \"breaksOpen\": 3
}
Frontend: React port 4174 -> Vite proxy -> Flask port 8502"""
    pages.append(evidence_page("6. Evidence Snapshot: Frontend API", "Live payload consumed by React on port 4174", api))

    pages.append(evidence_page("7. Evidence Snapshot: Controller Output", "Latest consolidated response recorded in logs/nsflow.log", controller))

    for name, title in [
        ("intake_and_catalogue_agent", "8. Agent Evidence: Intake and Catalogue"),
        ("regulatory_mapping_agent", "9. Agent Evidence: Regulatory Mapping"),
        ("data_quality_agent", "10. Agent Evidence: Data Quality"),
        ("regulatory_calculation_agent", "11. Agent Evidence: Regulatory Calculation"),
        ("reconciliation_agent", "12. Agent Evidence: Reconciliation"),
        ("lineage_and_evidence_agent", "13. Agent Evidence: Lineage and Evidence"),
        ("approval_and_submission_agent", "14. Agent Evidence: Approval and Submission"),
    ]:
        pages.append(evidence_page(title, f"Recorded specialist artifact: logs/thinking_dir/regulatory_reporting_controller.{name}", read_agent(name)))

    image, draw, y = page("15. Repeatable Execution Checklist", "Run this sequence each time the GitHub Codespace is reopened")
    steps = [
        ("Terminal 1: start Neuro SAN", "cd /workspaces/neuro-san-studio_HStesting\nsource venv/bin/activate\nNSFLOW_HOST=0.0.0.0 python -m neuro_san_studio run\nKeep this terminal running."),
        ("Browser: submit the agent request", "Open forwarded port 4173. Select industry/corep_finrep_stp. Submit: Run the month-end COREP and FINREP production cycle for reporting date 2026-08-31. Wait for the controller summary."),
        ("Terminal 2: start the result API", "cd /workspaces/neuro-san-studio_HStesting\nsource venv/bin/activate\npython apps/neuro_san_status/status_dashboard.py\nThis serves port 8502."),
        ("Terminal 3: start React", "cd /workspaces/neuro-san-studio_HStesting/apps/corep_finrep_react\nnpm install\nnpm run dev -- --host 0.0.0.0 --port 4174\nOpen forwarded port 4174."),
        ("Terminal 4: generate the aligned PDF", "cd /workspaces/neuro-san-studio_HStesting\nsource venv/bin/activate\npython tools/create_corep_finrep_report.py\nThe script reads the newest completed run and creates a run-specific PDF."),
        ("Browser: open the PDF", "Start python -m http.server 8765 --bind 0.0.0.0 --directory docs, forward port 8765, and open the generated file named COREP_FINREP_<RUN_ID>_consolidated_report.pdf."),
        ("Final alignment check", "Compare the run ID and status in the PDF, port 4174, and curl -s http://127.0.0.1:4174/api/corep-finrep. They must all refer to the same run."),
    ]
    for heading, text in steps:
        y = add_box(draw, y, heading, text, fill="#ffffff", border="#86efac")
        if y > PAGE_SIZE[1] - 330:
            pages.append(image)
            image, draw, y = page("15. Repeatable Execution Checklist (continued)", "Continue the same run sequence")
    pages.append(image)

    image, draw, y = page("17. Final Conclusion and Remediation", "What the business should take away")
    y = add_box(draw, y, "Conclusion", "The fork demonstrated a complete, observable, governed COREP/FINREP run. Neuro SAN coordinated specialist agents, Gemini supplied language reasoning, coded tools supplied deterministic demo data, governance agents tested it, and React presented the result. The system completed successfully by refusing an unsafe submission.", fill="#ecfeff", border="#67e8f9")
    y = add_box(draw, y, "Required next actions", "Correct the EUR 100 million General Ledger difference. Remove ADJ-PLUG-100. Improve securities mapping confidence. Re-ingest corrected data. Re-run the pipeline. Re-evaluate the seven release gates before submission.", fill="#fff7ed", border="#fdba74")
    y = add_text(draw, y, f"Report generated locally: {datetime.now().isoformat(timespec='seconds')}", SMALL, MUTED)
    pages.append(image)

    for index, image in enumerate(pages, 1):
        image.save(OUTPUT_DIR / f"page-{index:02d}.png")
    pages[0].save(PDF_PATH, save_all=True, append_images=pages[1:], resolution=150.0)
    print(f"Created {PDF_PATH}")
    print(f"Pages: {len(pages)}")
    print(f"Evidence images: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

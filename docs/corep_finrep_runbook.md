# COREP/FINREP Repeatable Runbook

This is the complete sequence for running the fork again and generating a PDF aligned to that run.

## 1. Open the Codespace

Open the GitHub fork:

```text
https://github.com/Hardik5shah5/neuro-san-studio_HStesting
```

Open a terminal in the repository root:

```bash
cd /workspaces/neuro-san-studio_HStesting
source venv/bin/activate
```

## 2. Start Neuro SAN

In Terminal 1, keep this command running:

```bash
NSFLOW_HOST=0.0.0.0 python -m neuro_san_studio run
```

Wait until the terminal reports that nsflow is running on port `4173` and the Neuro SAN server is running on port `8080`.

## 3. Submit the reporting request

Open the forwarded port `4173`, select `industry/corep_finrep_stp`, and submit:

```text
Run the month-end COREP and FINREP production cycle for reporting date 2026-08-31.
```

Wait until the controller summary appears. Do not submit the same request twice.

## 4. Start the result API

In Terminal 2:

```bash
cd /workspaces/neuro-san-studio_HStesting
source venv/bin/activate
python apps/neuro_san_status/status_dashboard.py
```

This serves the runtime dashboard and the latest result API on port `8502`.

## 5. Start the React result page

In Terminal 3:

```bash
cd /workspaces/neuro-san-studio_HStesting/apps/corep_finrep_react
npm install
npm run dev -- --host 0.0.0.0 --port 4174
```

Open port `4174` and refresh after the controller response is complete. The page should show the current run ID and live result status.

## 6. Generate the run-specific PDF

After the run has completed, in Terminal 4 run:

```bash
cd /workspaces/neuro-san-studio_HStesting
source venv/bin/activate
python tools/create_corep_finrep_report.py
```

The generator reads the newest completed controller response from `logs/nsflow.log`, reads the specialist artifacts from `logs/thinking_dir`, and creates a run-specific PDF:

```text
docs/COREP_FINREP_<RUN_ID>_consolidated_report.pdf
```

It also creates matching evidence images under:

```text
docs/reports/corep_finrep_<RUN_ID>/
```

This prevents a later run from silently overwriting the prior run's report.

## 7. Open the PDF

VS Code cannot preview PDFs as text. Serve the `docs` directory in Terminal 5:

```bash
cd /workspaces/neuro-san-studio_HStesting
python -m http.server 8765 --bind 0.0.0.0 --directory docs
```

Open the forwarded port `8765`, then select the run-specific PDF. Alternatively, use a browser URL such as:

```text
http://localhost:8765/COREP_FINREP_<RUN_ID>_consolidated_report.pdf
```

## 8. Validate alignment before sharing

Check that the PDF run ID matches the React page and API:

```bash
curl -s http://127.0.0.1:4174/api/corep-finrep
```

The run ID, reporting date, status, submission decision, gate count, and break count must match the PDF title page.

## Important notes

- `4173` executes and streams the agent run.
- `8080` is the Neuro SAN backend.
- `8502` exposes runtime status and the latest completed result.
- `4174` displays the result in React.
- `8765` serves saved PDF files in a browser.
- The current project uses synthetic demo data and the active `config/llm_config.hocon` model configuration.
- If the Gemini API quota is exhausted, the run will stop at the model call and no valid business result should be reported.
import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect, useState } from 'react';
import { finrepOutput } from './data/corepFinrepData';

function StatCard({ label, value, tone = 'normal' }) {
  return (
    <div style={{
      background: '#111827',
      border: '1px solid #334155',
      borderRadius: 12,
      padding: 18,
      minHeight: 110,
    }}>
      <div style={{ color: '#94a3b8', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
      <div style={{
        marginTop: 12,
        fontSize: 28,
        fontWeight: 700,
        color: tone === 'success' ? '#4ade80' : tone === 'warning' ? '#fbbf24' : '#e2e8f0',
      }}>
        {value}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section style={{ marginTop: 24, background: '#0f172a', border: '1px solid #1e293b', borderRadius: 14, padding: 20 }}>
      <h2 style={{ margin: '0 0 16px', fontSize: 22 }}>{title}</h2>
      {children}
    </section>
  );
}

function reportSections(response) {
  const sections = [];
  let current = { title: 'Controller response', lines: [] };
  response.split('\n').forEach((line) => {
    const heading = line.match(/^#{2,3}\s+(.+)/);
    if (heading) {
      if (current.lines.length) sections.push(current);
      current = { title: heading[1].replaceAll('**', ''), lines: [] };
      return;
    }
    current.lines.push(line);
  });
  if (current.lines.some((line) => line.trim())) sections.push(current);
  return sections;
}

const gateDescriptions = {
  'GATE-01': 'The reporting scope and regulatory taxonomy were accepted for this run.',
  'GATE-02': 'The source data was not complete and balanced: the General Ledger was short by EUR 100 million.',
  'GATE-03': 'The deterministic accounting checks failed because the trial balance was out of balance and a plug was used.',
  'GATE-04': 'The reconciliation could not be cleared because critical and high-severity breaks remained open.',
  'GATE-05': 'At least one reported value could not be traced to a real source transaction.',
  'GATE-06': 'The material exceptions did not have an acceptable executive or risk-owner sign-off.',
  'GATE-07': 'The evidence files and cryptographic hashes were sealed for audit purposes.',
};

function App() {
  const [output, setOutput] = useState(finrepOutput);
  const [liveState, setLiveState] = useState('Connecting to 8502...');

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const response = await fetch('/api/corep-finrep');
        const live = await response.json();
        if (!active || !live.available) return;
        setOutput((current) => ({
          ...current,
          runStatus: { ...current.runStatus, reportDate: live.reportDate, entity: live.entity, runId: live.runId, status: live.status, submission: live.submission, summary: live.response },
          metrics: { controlsPassed: live.controlsPassed, breaksOpen: live.breaksOpen },
          controls: (live.controls || current.controls).map((item) => ({
            ...item,
            description: gateDescriptions[item.id] || item.description,
          })),
          approvals: live.approvals || current.approvals,
        }));
        setLiveState(`Live result from 4173 via 8502 | ${live.runId}`);
      } catch {
        setLiveState('Waiting for the status API on port 8502');
      }
    };
    load();
    const timer = window.setInterval(load, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const { runStatus, controls, reconciliation, approvals, lineages, metrics } = output;
  const detailSections = runStatus.summary.startsWith('#') ? reportSections(runStatus.summary) : [];
  const isBlocked = runStatus.status === 'BLOCKED' || runStatus.submission === 'Prohibited';

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #020817 0%, #0f172a 100%)',
      color: '#e2e8f0',
      padding: '32px 24px 48px',
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <header style={{ marginBottom: 20 }}>
          <div style={{ color: '#7dd3fc', letterSpacing: 2, fontSize: 12, textTransform: 'uppercase' }}>Neuro SAN Output</div>
          <h1 style={{ margin: '10px 0 6px', fontSize: 38 }}>COREP / FINREP Final Output</h1>
          <div style={{ color: '#cbd5e1', fontSize: 16 }}>{runStatus.reportDate} • {runStatus.entity}</div>
          <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 8 }}>{liveState}</div>
          <button
            type="button"
            onClick={() => window.print()}
            style={{
              marginTop: 16,
              border: '1px solid #38bdf8',
              borderRadius: 8,
              background: '#082f49',
              color: '#e0f2fe',
              padding: '10px 14px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Download Business Report PDF
          </button>
          <button
            type="button"
            onClick={() => window.print()}
            style={{
              marginTop: 16,
              marginLeft: 10,
              border: '1px solid #a78bfa',
              borderRadius: 8,
              background: '#2e1065',
              color: '#ede9fe',
              padding: '10px 14px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Download Technical Walkthrough PDF
          </button>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
          <StatCard label="Run Status" value={runStatus.status} tone={runStatus.status === 'Approved' ? 'success' : 'warning'} />
          <StatCard label="Submission" value={runStatus.submission} tone={isBlocked ? 'warning' : 'success'} />
          <StatCard label="Controls" value={metrics.controlsPassed} />
          <StatCard label="Breaks" value={metrics.breaksOpen} tone={metrics.breaksOpen === 0 ? 'success' : 'warning'} />
        </div>

        <Section title="Executive Summary">
          <p style={{ margin: 0, lineHeight: 1.7, color: '#dbeafe' }}>
            {isBlocked
              ? 'The month-end cycle executed all reporting stages, but submission was blocked by unresolved controls and reconciliation breaks.'
              : runStatus.summary}
          </p>
          {runStatus.runId && <p style={{ margin: '14px 0 0', color: '#94a3b8' }}>Run ID: {runStatus.runId}</p>}
        </Section>

        <Section title="Execution Details">
          <div style={{ display: 'grid', gap: 12 }}>
            {[
              ['1. Intake and catalogue', 'Source snapshots were ingested and catalogued.'],
              ['2. Regulatory mapping', 'The source records were translated into the official COREP and FINREP reporting rows.'],
              ['3. Data quality controls', 'The agents checked whether the source data was complete, consistent, and mathematically balanced.'],
              ['4. Regulatory calculations', 'The agents calculated capital, risk exposure, capital ratios, leverage, and FINREP totals.'],
              ['5. Reconciliation', 'The agents compared accounting values with regulatory values and recorded every unexplained difference.'],
              ['6. Lineage and evidence', 'The agents checked whether every reported number could be traced back to an original source record and sealed the audit evidence.'],
              ['7. Approval and submission', isBlocked ? 'The checker rejected the run because material issues remained unresolved, so the regulatory submission was locked.' : 'The checker approved the run and released it for regulatory submission.'],
            ].map(([title, detail]) => (
              <div key={title} style={{ borderLeft: `4px solid ${isBlocked && title.startsWith('7.') ? '#fbbf24' : '#38bdf8'}`, background: '#0b1220', padding: '12px 16px' }}>
                <strong>{title}</strong>
                <div style={{ color: '#cbd5e1', marginTop: 5 }}>{detail}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Controls and Quality Gates">
          <div style={{ display: 'grid', gap: 12 }}>
            {controls.map((item) => (
              <div key={item.id} style={{ border: '1px solid #1e293b', borderRadius: 10, padding: 14, background: '#0b1220' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <strong>{item.id}</strong>
                  <span style={{ color: item.result === 'PASS' ? '#4ade80' : '#fbbf24', fontWeight: 700 }}>{item.result}</span>
                </div>
                <div style={{ color: '#cbd5e1', marginTop: 6 }}>{item.description}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="What the Results Mean">
          <div style={{ lineHeight: 1.75, color: '#dbeafe' }}>
            <p style={{ marginTop: 0 }}>The project successfully ran the complete reporting workflow. It collected the synthetic bank data, translated it into regulatory COREP and FINREP figures, checked the figures, and passed the results through an approval gate.</p>
            <p>The calculated capital ratio of <strong>17.65%</strong> and leverage ratio of <strong>12.00%</strong> look sufficient on their own. However, the underlying General Ledger does not balance: assets are <strong>EUR 1.25 billion</strong>, while liabilities plus equity are only <strong>EUR 1.15 billion</strong>.</p>
            <p style={{ marginBottom: 0 }}>Because the missing <strong>EUR 100 million</strong> was replaced with an artificial balancing plug rather than a real source transaction, the agents correctly marked the report as blocked and prohibited submission.</p>
          </div>
        </Section>

        <Section title="Business Explanation of This Run">
          <div style={{ display: 'grid', gap: 18, lineHeight: 1.75, color: '#dbeafe' }}>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>1. Problem statement</h3>
              <p style={{ margin: 0 }}>The bank needs to prepare its month-end regulatory COREP and FINREP submission for 31 August 2026. The source information must be converted into regulatory figures, checked for accuracy, traced to evidence, approved by a checker, and released only when the accounting data is reliable.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>2. Solution idea</h3>
              <p style={{ margin: 0 }}>The project uses a sequence of specialist agents. Each agent performs one controlled part of the reporting process and passes its result to the next agent. This creates an auditable workflow: collect the data, map it, test it, calculate the regulatory values, reconcile differences, prove the source lineage, and approve or reject the filing.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>3. What the agents found</h3>
              <p style={{ margin: 0 }}>The intake agent received General Ledger assets of EUR 1.25 billion and risk data showing EUR 850 million of exposure and EUR 150 million of own funds. The mapping agent converted these inputs into COREP and FINREP values, but reported only 75% confidence for the securities mapping. The data-quality agent then found that the General Ledger assets of EUR 1.25 billion did not equal liabilities plus equity of EUR 1.15 billion, leaving a EUR 100 million difference.</p>
              <p>The calculation agent still calculated a CET1 ratio of 17.65%, a total capital ratio of 17.65%, and a preliminary leverage ratio of 12.00%. These figures appear healthy, but they cannot be treated as submission-ready while the source accounting identity is broken.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>4. Why the reconciliation and lineage agents matter</h3>
              <p style={{ margin: 0 }}>The reconciliation agent identified three open breaks: a critical EUR 100 million General Ledger imbalance, a high-severity EUR 100 million balancing plug, and a medium-severity securities mapping issue. The lineage agent found that FINREP cell F 01.02.r320.c010 depended on artificial adjustment ADJ-PLUG-100 instead of a real source transaction. This means the number could not be independently supported by the bank's books.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>5. Final business decision</h3>
              <p style={{ margin: 0 }}>The approval agent acted as the checker and rejected the run. Two of seven release gates passed and five failed. The filing was therefore marked BLOCKED and submission was prohibited. This is the intended control outcome: the system stopped an unreliable regulatory report instead of allowing an unsupported number to be sent to the regulator.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#7dd3fc' }}>6. Conclusion and next action</h3>
              <p style={{ margin: 0 }}>The project successfully demonstrated the complete regulatory reporting control process. The immediate business action is to correct the EUR 100 million General Ledger difference, remove ADJ-PLUG-100, improve the securities mapping above the required confidence threshold, reload the corrected source data, and run the process again. Only after the breaks are cleared should the checker release the report for submission.</p>
            </article>
          </div>
        </Section>

        <Section title="Technical Walkthrough: How This Fork Executed the Project">
          <div style={{ display: 'grid', gap: 18, lineHeight: 1.75, color: '#dbeafe' }}>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>1. Project startup</h3>
              <p style={{ margin: 0 }}>The project was started with <code>python -m neuro_san_studio run</code>. The Neuro SAN Studio runner loaded the project environment, the registry manifest, the coded tools, and the configured plugins. It then started the Neuro SAN backend on port 8080 and the nsflow execution interface on port 4173.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>2. Network configuration</h3>
              <p style={{ margin: 0 }}>The workflow was defined in the HOCON network file <code>registries/industry/corep_finrep_stp.hocon</code>. That file describes the controller and the specialist agents, their responsibilities, and the order in which work is delegated. Neuro SAN read this configuration and registered the network as <code>industry/corep_finrep_stp</code>.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>3. Request and session creation</h3>
              <p style={{ margin: 0 }}>The user submitted the month-end request in nsflow on port 4173. nsflow created a session, connected to the Neuro SAN service on port 8080, and opened the streaming channels used for chat, progress, logs, and agent trace information.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>4. Orchestration and harnessing</h3>
              <p style={{ margin: 0 }}>The regulatory reporting controller acted as the coordinator. It interpreted the request, called the intake agent, and then passed each completed result to the next specialist. The harness managed session state, agent invocation, streaming responses, trace information, and error handling. This is why the agents appeared to run step by step instead of as unrelated programs.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>5. Data and coded-tool execution</h3>
              <p style={{ margin: 0 }}>The intake agent called the coded tool <code>SyntheticReportingData</code> from <code>coded_tools/industry/corep_finrep_stp</code>. The tool returned deterministic demo records for the General Ledger and risk system. It also attached source IDs, reporting date, control totals, schema hashes, and expected controls so later agents could test and trace the data.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>6. Google API and model usage</h3>
              <p style={{ margin: 0 }}>The configured language model was Google Gemini <code>gemini-3.6-flash</code>. The agent network sent each agent's instructions and the relevant workflow context to the Google model through the Neuro SAN LLM configuration. Gemini interpreted the task and returned structured decisions, calculations, warnings, and explanations. The API key was read from the project environment and was not placed in the report or browser page.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>7. What the LLM did and did not do</h3>
              <p style={{ margin: 0 }}>Gemini provided language understanding, reasoning, delegation choices, and explanations for the agents. The deterministic coded tool supplied the synthetic records, while the governance checks compared results against explicit rules. This means the LLM did not invent the source ledger values and did not have authority to override a failed release gate. The current run demonstrates runtime reasoning and orchestration; it does not train or permanently update the Gemini model.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>8. Agentic adaptation when an event occurs</h3>
              <p style={{ margin: 0 }}>An agentic system adapts during a run by observing new evidence, changing the next action, and passing the updated context to the next agent. For example, when the data-quality agent found the EUR 100 million imbalance, the workflow did not continue as if the data were clean. The reconciliation agent opened a material break, the lineage agent checked the unsupported plug, and the approval agent changed the final action from release to block.</p>
              <p>If a new event occurs, such as a missing source file, a changed taxonomy, a low-confidence mapping, or an API failure, the controller can route the event to the relevant specialist, request a re-check, carry the exception forward, or stop the workflow. The agents therefore adapt their next decision from the evidence and messages produced by earlier steps. This is runtime self-adaptation through context and tool results, not unsupervised learning or permanent model retraining.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>9. Governance and control enforcement</h3>
              <p style={{ margin: 0 }}>Governance was enforced by the data-quality, reconciliation, lineage, and approval agents. The final checker did not rely only on the model's narrative. It evaluated hard release gates, required evidence, source traceability, material breaks, and maker-checker separation. Because five of seven gates failed, the submission was locked and no filing was released.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>10. Logs and audit evidence</h3>
              <p style={{ margin: 0 }}>Neuro SAN recorded the streamed controller response in <code>logs/nsflow.log</code> and wrote agent thinking and trace files under <code>logs/thinking_dir</code>. Those records allowed the result API to identify the latest completed COREP/FINREP response without rerunning the agents.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>11. How the result reached the frontend</h3>
              <p style={{ margin: 0 }}>The Flask service on port 8502 read the latest controller response from the nsflow log and exposed it at <code>/api/corep-finrep</code>. The React application on port 4174 polled that endpoint every five seconds through its Vite proxy. React converted the response into status cards, execution stages, gate panels, business explanations, and detailed technical sections.</p>
            </article>
            <article>
              <h3 style={{ margin: '0 0 6px', color: '#c4b5fd' }}>12. Final output and PDF</h3>
              <p style={{ margin: 0 }}>The browser displayed the consolidated result for run <code>DEMO-20260831-001</code>. The Download Technical Walkthrough PDF button uses the browser print engine to save the rendered technical explanation as a PDF. The saved document therefore contains both the technical sequence and the actual figures and decisions produced by this run.</p>
            </article>
          </div>
        </Section>

        <Section title="Reconciliation">
          <div style={{ display: 'grid', gap: 12 }}>
            {reconciliation.map((item) => (
              <div key={item.name} style={{ border: '1px solid #1e293b', borderRadius: 10, padding: 14, background: '#0b1220' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <strong>{item.name}</strong>
                  <span style={{ color: item.status === 'CLEAR' ? '#4ade80' : '#fbbf24', fontWeight: 700 }}>{item.status}</span>
                </div>
                <div style={{ color: '#cbd5e1', marginTop: 6 }}>{item.detail}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Lineage and Evidence">
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.9, color: '#dbeafe' }}>
            {lineages.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Section>

        <Section title="Approval Gate">
          <div style={{ display: 'grid', gap: 10 }}>
            {approvals.map((item) => (
              <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', border: '1px solid #1e293b', borderRadius: 10, padding: 12, background: '#0b1220' }}>
                <span>{item.label}</span>
                <strong style={{ color: item.value === 'Approved' ? '#4ade80' : '#fbbf24' }}>{item.value}</strong>
              </div>
            ))}
          </div>
        </Section>

        {detailSections.length > 0 && (
          <Section title="Detailed Controller Report">
            <div style={{ display: 'grid', gap: 18 }}>
              {detailSections.map((section) => (
                <article key={section.title} style={{ borderTop: '1px solid #334155', paddingTop: 14 }}>
                  <h3 style={{ margin: '0 0 8px', color: '#7dd3fc' }}>{section.title}</h3>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', font: 'inherit', lineHeight: 1.65, color: '#cbd5e1' }}>
                    {section.lines.join('\n').trim()}
                  </pre>
                </article>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

from __future__ import annotations


def render_index() -> str:
    """
    Returns the HTML shell for the DBL Boundary Service UI.

    Left: connection and prompt input.
    Right: insights panel placeholder.
    """
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>DBL Boundary Service</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {
          margin: 0;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #0b1120;
          color: #e5e7eb;
        }
        .root {
          display: grid;
          grid-template-columns: 1.1fr 1.4fr;
          height: 100vh;
        }
        .left {
          padding: 24px;
          border-right: 1px solid #1f2937;
          background: radial-gradient(circle at top left, #111827, #020617);
        }
        .right {
          padding: 24px;
          background: radial-gradient(circle at top right, #020617, #020617);
        }
        h1 {
          font-size: 20px;
          margin: 0 0 4px 0;
        }
        h2 {
          font-size: 14px;
          margin: 16px 0 8px 0;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #9ca3af;
        }
        p {
          font-size: 13px;
          color: #9ca3af;
          margin: 0 0 12px 0;
        }
        label {
          display: block;
          font-size: 12px;
          margin-bottom: 4px;
          color: #d1d5db;
        }
        input, textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 8px 10px;
          border-radius: 8px;
          border: 1px solid #374151;
          background: #020617;
          color: #e5e7eb;
          font-size: 13px;
          outline: none;
        }
        input:focus, textarea:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.6);
        }
        textarea {
          resize: vertical;
          min-height: 120px;
          max-height: 260px;
        }
        .row {
          margin-bottom: 12px;
        }
        .button-row {
          margin-top: 8px;
          display: flex;
          gap: 8px;
        }
        button {
          border-radius: 9999px;
          border: none;
          padding: 8px 16px;
          font-size: 13px;
          cursor: pointer;
          background: linear-gradient(135deg, #4f46e5, #06b6d4);
          color: #f9fafb;
        }
        button.secondary {
          background: #111827;
          color: #e5e7eb;
          border: 1px solid #374151;
        }
        .tagline {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 16px;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 8px;
          border-radius: 9999px;
          border: 1px solid #1f2937;
          background: rgba(15, 23, 42, 0.9);
          font-size: 11px;
          color: #9ca3af;
          margin-bottom: 10px;
        }
        .badge-dot {
          width: 7px;
          height: 7px;
          border-radius: 9999px;
          background: #22c55e;
        }
        .panel {
          border-radius: 12px;
          border: 1px solid #1f2937;
          padding: 14px 14px;
          background: rgba(15, 23, 42, 0.9);
          height: calc(100vh - 48px);
          box-sizing: border-box;
          overflow: auto;
        }
        .panel h3 {
          margin: 0 0 6px 0;
          font-size: 14px;
        }
        .panel p {
          font-size: 12px;
        }
        .pill-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
        }
        .pill {
          font-size: 11px;
          padding: 3px 8px;
          border-radius: 9999px;
          border: 1px solid #1f2937;
          color: #9ca3af;
        }
        .insight-section {
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #1f2937;
        }
        .insight-section h4 {
          font-size: 12px;
          color: #9ca3af;
          margin: 0 0 6px 0;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .insight-section pre {
          font-size: 11px;
          background: #020617;
          padding: 8px;
          border-radius: 6px;
          overflow-x: auto;
          margin: 0;
          white-space: pre-wrap;
          word-break: break-word;
        }
        .outcome-allow { color: #22c55e; }
        .outcome-modify { color: #f59e0b; }
        .outcome-block { color: #ef4444; }
      </style>
      <script>
      document.addEventListener("DOMContentLoaded", () => {
        const keyInput = document.getElementById("apiKey");
        const promptInput = document.getElementById("prompt");
        const runBtn = document.getElementById("runBtn");
        const dryRunBtn = document.getElementById("dryRunBtn");
        const insightsPanel = document.getElementById("insightsPanel");

        // Enable dry run by default (no API key needed)
        dryRunBtn.disabled = false;

        keyInput.addEventListener("input", async () => {
          const value = keyInput.value.trim();
          if (value.length > 10) {
            try {
              const res = await fetch("/set-key", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: value })
              });
              if (res.ok) {
                runBtn.disabled = false;
              }
            } catch (err) {
              console.error("Failed to set API key", err);
            }
          } else {
            runBtn.disabled = true;
          }
        });

        async function executeRun(dryRun) {
          const prompt = promptInput.value.trim();
          if (!prompt) {
            alert("Please enter a prompt");
            return;
          }

          insightsPanel.innerHTML = '<p style="color: #6b7280;">Running...</p>';

          try {
            const res = await fetch("/run", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ prompt, dry_run: dryRun })
            });
            const data = await res.json();
            renderInsights(data);
          } catch (err) {
            insightsPanel.innerHTML = `<p style="color: #ef4444;">Error: ${err.message}</p>`;
          }
        }

        runBtn.addEventListener("click", () => executeRun(false));
        dryRunBtn.addEventListener("click", () => executeRun(true));

        function renderInsights(data) {
          const s = data.snapshot;
          const blocked = data.blocked ? '<span style="color:#ef4444">BLOCKED</span>' : '<span style="color:#22c55e">ALLOWED</span>';
          
          let html = `
            <h3>Result: ${blocked}</h3>
            <div class="insight-section">
              <h4>Response</h4>
              <pre>${escapeHtml(data.content)}</pre>
            </div>
            <div class="insight-section">
              <h4>BoundaryContext</h4>
              <pre>${JSON.stringify(s.boundary_context, null, 2)}</pre>
            </div>
            <div class="insight-section">
              <h4>Policy Decisions (${s.policy_decisions.length})</h4>
              <pre>${JSON.stringify(s.policy_decisions, null, 2)}</pre>
            </div>
            <div class="insight-section">
              <h4>DBL Outcome: <span class="outcome-${s.dbl_outcome}">${s.dbl_outcome}</span></h4>
            </div>
            <div class="insight-section">
              <h4>PsiDefinition</h4>
              <pre>${JSON.stringify(s.psi_definition, null, 2)}</pre>
            </div>
          `;

          if (s.llm_payload) {
            html += `
              <div class="insight-section">
                <h4>LLM Payload</h4>
                <pre>${JSON.stringify(s.llm_payload, null, 2)}</pre>
              </div>
            `;
          }

          if (s.llm_result) {
            html += `
              <div class="insight-section">
                <h4>LLM Result</h4>
                <pre>${JSON.stringify(s.llm_result, null, 2)}</pre>
              </div>
            `;
          }

          html += `
            <div class="insight-section">
              <h4>Trace</h4>
              <p>Request ID: ${s.request_id}</p>
              <p>Execution Trace: ${s.execution_trace_id || 'N/A'}</p>
              <p>Timestamp: ${s.timestamp}</p>
              <p>Dry Run: ${s.dry_run}</p>
            </div>
          `;

          insightsPanel.innerHTML = html;
        }

        function escapeHtml(str) {
          return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
      });
      </script>
    </head>
    <body>
      <div class="root">
        <div class="left">
          <div class="badge">
            <span class="badge-dot"></span>
            <span>DBL Boundary Service</span>
          </div>
          <h1>Governed LLM boundary</h1>
          <p class="tagline">
            Small deterministic front end that will route your LLM calls through DBL and KL.
          </p>

          <div class="row">
            <h2>Connection</h2>
            <label for="apiKey">OpenAI API key</label>
            <input id="apiKey" type="password" placeholder="sk-..." autocomplete="off" />
          </div>

          <div class="row">
            <h2>Prompt</h2>
            <label for="prompt">Prompt</label>
            <textarea id="prompt" placeholder="Ask the model something..."></textarea>
          </div>

          <div class="button-row">
            <button id="runBtn" disabled>Run through boundary</button>
            <button class="secondary" id="dryRunBtn">Dry run (no LLM)</button>
          </div>
          <p style="font-size: 11px; margin-top: 10px;">
            "Run" requires an API key. "Dry run" tests the full DBL+KL flow without calling the LLM.
          </p>
        </div>
        <div class="right">
          <div class="panel" id="insightsPanel">
            <h3>Execution and policy insights</h3>
            <p>
              Run a prompt to see the full request lifecycle:
            </p>
            <div class="pill-row">
              <div class="pill">BoundaryContext</div>
              <div class="pill">DBL policies</div>
              <div class="pill">LLM step</div>
              <div class="pill">Trace</div>
            </div>
            <p style="margin-top: 14px;">
              Use "Dry run" to test the flow without calling the LLM.
            </p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

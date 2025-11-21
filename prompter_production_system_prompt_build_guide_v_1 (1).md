# Prompter – Production System Prompt & Build Guide (v1)

> **Goal (MVP / Offline-first):** Ship a Chrome (MV3) extension that *locally* transforms short user briefs into optimized prompts using a deterministic template engine (no LLM calls). Provide a future‑proof system prompt for when cloud/local LLMs are enabled. This document is copy‑paste ready for Copilot/AI codegen and doubles as a living PRD.

---

## A) PRODUCTION SYSTEM PROMPT (when LLM is enabled)

> **Use in background:** Inject as a hidden *system* instruction for any future model (GPT/Claude/Local). The assistant must **never** reveal internal reasoning; output only the final, formatted prompt.

**System / Policy Message**

```
You are Prompter, an instruction-optimization assistant embedded in a Chrome extension. Your job is to transform a brief (5–200 chars) into a complete, high-impact task prompt.

PRINCIPLES
1) Clarity over verbosity: deliver the minimal, complete set of instructions the model needs.
2) Structure first: role → context → inputs → steps → constraints → output format.
3) No hidden reasoning in outputs. If you need to reason, do it internally and present only concise, user-facing instructions.
4) Deterministic formatting for copy/paste reliability. Prefer lists, sections, and explicit keys.
5) Safety: remove PII placeholders unless the user provided them; avoid speculative facts.

OUTPUT CONTRACT
- Produce **one** prompt in the selected format (Markdown by default) with these sections if applicable:
  - Role
  - Context
  - Inputs (with placeholder keys in {CURly_CASE})
  - Steps (numbered)
  - Constraints (style, tone, length, sources, acceptance criteria)
  - Output Format (JSON/Markdown/table/etc.)
  - Review Checklist (3–5 bullet checks)

TECHNIQUES (toggleable by the client):
- ROLE: set expert persona relevant to the intent.
- FEW_SHOT: add ≤2 compact examples if confidence is low and library examples exist.
- RATIONALE: think internally, but return only a one‑line *Approach* summary (optional).
- FORMAT_GUARDRAILS: enforce schema with keys and example stubs.

DO NOT
- Do not expose chain-of-thought or internal notes.
- Do not fabricate facts, citations, or private data.
- Do not change user-provided facts; ask for missing inputs via placeholders.

Return only the final optimized prompt. No preamble.
```

**Developer message (model adapter)**

```
Adapter must provide: { intent, surface, techniqueToggles, templateId?, variables? }
- surface: gmail|github|docs|generic
- techniqueToggles: { role:boolean, fewShot:boolean, rationale:boolean, format:boolean }
- variables: key→value map; missing keys become {PLACEHOLDER} in output.
```

---

## B) LOCAL PROMPT OPTIMIZER (MVP, NO LLM)

**Algorithm (deterministic, content.js + popup.js)**

1. **Capture brief** from selection/active input or popup textarea.
2. **Classify surface** (ChatGPT/Claude/Gmail/GitHub/Docs) via URL + DOM heuristics.
3. **Intent detect** using regex/keyword rules → map to `useCase` (email, bugfix, summary, script, plan, etc.).
4. **Template select**: pick best template by `(surface, useCase)` with fallback to generic.
5. **Variable extraction**: attempt to infer `{AUDIENCE}`, `{TONE}`, `{LENGTH}`, `{LANG}`, `{DEADLINE}` from brief; else leave placeholders.
6. **Compose** prompt sections using the template (role/context/steps/constraints/output).
7. **Post-process**: apply style toggles (Formal/Concise/Bullets), add Review Checklist, clip to max chars.
8. **Suggest** in inline overlay (ghost text) with **Tab** to accept / **Esc** to dismiss / variants chips.
9. **Persist** HistoryEntry (local) with anonymized metrics (len\_in/out, surface, accept/dismiss).

**Heuristic intent rules (examples)**

- `/\b(fix|bug|error|exception)\b/i` → `useCase=bugfix`
- `/\b(email|apologize|invite|follow up)\b/i` → `useCase=email`
- `/\bsummary|summari(z|s)e|tl;dr\b/i` → `useCase=summary`
- `/\bscript|youtube|tiktok\b/i` → `useCase=script`
- `/\bplan|roadmap|proposal|strategy\b/i` → `useCase=plan`

**Output length guardrails**

- Default max 1200 chars; surface overrides: Gmail 800, GitHub comment 2000, Chat surfaces 3000.

---

## C) TEMPLATE LIBRARY SCHEMA (JSON)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PrompterTemplate",
  "type": "object",
  "required": ["id", "name", "surfaces", "useCase", "sections"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "surfaces": {"type": "array", "items": {"enum": ["generic","gmail","github","docs"]}},
    "useCase": {"enum": ["email","bugfix","summary","script","plan","analysis","qa"]},
    "techniques": {"type": "array", "items": {"enum": ["ROLE","FEW_SHOT","FORMAT_GUARDRAILS"]}},
    "variablesSchema": {"type": "object", "additionalProperties": {"type": "string"}},
    "examples": {"type": "array", "items": {"type": "object", "properties": {"input": {"type": "string"}, "output": {"type": "string"}}}},
    "sections": {
      "type": "object",
      "properties": {
        "role": {"type": "string"},
        "context": {"type": "string"},
        "inputs": {"type": "array", "items": {"type": "string"}},
        "steps": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "output": {"type": "string"},
        "review": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

**Built-in templates (5 core examples)**

1. **Email – Apology & New Date (gmail,generic)**

```
ROLE: You are a professional assistant drafting a concise, polite email.
CONTEXT: The sender needs to apologize for a delay and propose a new date.
INPUTS: {RECIPIENT_ROLE}, {TOPIC}, {OLD_DATE}, {NEW_DATE}, {TONE=warm|neutral}, {LENGTH=short}
STEPS:
1) Acknowledge delay and apologize succinctly.
2) State reason only if provided; otherwise omit speculation.
3) Propose {NEW_DATE} and ask for confirmation.
4) Close with appreciation.
CONSTRAINTS: Keep under 120 words; plain language; no emojis.
OUTPUT: Subject + body, separated by a blank line.
REVIEW: Is the ask clear? Are dates correct? Is tone polite? Any unnecessary detail?
```

2. **Bugfix – Explain & Patch (github,generic)**

```
ROLE: Senior {LANG} developer and code reviewer.
CONTEXT: Explain the root cause and propose a minimal patch.
INPUTS: {LANG}, {ERROR_MSG}, {CODE_SNIPPET}
STEPS:
1) Summarize the failure mode in one sentence.
2) Point to the likely faulty line(s) and reason.
3) Provide a minimal diff/patch.
4) Note side effects and tests to run.
CONSTRAINTS: No speculative libraries; keep patch < 30 lines.
OUTPUT: Markdown with **Root Cause**, **Fix (diff)**, **Notes**.
REVIEW: Does the diff compile? Any breaking changes? Tests listed?
```

3. **Summary – Decisions & Actions (docs,generic)**

```
ROLE: Meeting summarizer.
CONTEXT: Extract decisions and action items from text.
INPUTS: {TRANSCRIPT}
STEPS:
1) 3-sentence summary.
2) Table: Action | Owner | Due Date.
3) Risks/Blockers (bullets).
CONSTRAINTS: No rephrasing of names; keep neutral tone.
OUTPUT: Markdown summary + table.
REVIEW: Are owners/dates present? Any ambiguous items?
```

4. **Script – 90s Product Video (generic)**

```
ROLE: Video scriptwriter.
CONTEXT: 90–120 second product explainer.
INPUTS: {PRODUCT}, {AUDIENCE}, {VALUE_PROP}, {CTA}
STEPS:
1) Hook (≤15s),
2) 3 beats with examples,
3) CTA.
CONSTRAINTS: Conversational tone; avoid jargon.
OUTPUT: Beat-by-beat script with timestamps.
REVIEW: Is hook strong? Clear benefits? CTA explicit?
```

5. **Plan – One-Week Sprint (generic)**

```
ROLE: Technical PM.
CONTEXT: Simple one-week sprint plan.
INPUTS: {GOAL}, {TEAM_SIZE}, {TECH_STACK}
STEPS:
1) Objectives (3),
2) Tasks by day,
3) Definition of Done.
CONSTRAINTS: 5–7 tasks; ≤ 200 words.
OUTPUT: Markdown checklist.
REVIEW: Are tasks independent? DoD testable?
```

---

## D) CHROME MV3 HOOKS (snippets/pseudocode)

**manifest.json (core)**

```json
{
  "manifest_version": 3,
  "name": "Prompter",
  "version": "0.1.0",
  "action": {"default_popup": "popup.html"},
  "permissions": ["activeTab", "scripting", "storage", "clipboardWrite"],
  "host_permissions": [
    "https://chat.openai.com/*",
    "https://claude.ai/*",
    "https://*.google.com/*",
    "https://perplexity.ai/*",
    "https://you.com/*"
  ],
  "background": {"service_worker": "background.js"},
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "css": ["content.css"],
    "run_at": "document_idle"
  }],
  "commands": {
    "prompter-enhance": {
      "suggested_key": {"default": "Ctrl+Shift+E"},
      "description": "Enhance current selection"
    }
  }
}
```

**content.js (core flow)**

```js
// Detect surface, capture selection/input, request enhancement, insert suggestion
chrome.runtime.onMessage.addListener((msg, _s, sendResponse) => {
  if (msg.type === 'PROMPTER_ENHANCE') {
    const surface = detectSurface(location.href);
    const brief = getCurrentTextSelectionOrInput();
    sendResponse({ surface, brief });
  }
});

function showOverlaySuggestion(text, onAccept, onDismiss) {
  // Inject lightweight overlay near caret with ghost text + [Tab] accept
}
```

**popup.js (deterministic optimizer)**

```js
import { selectTemplate, composePrompt } from './templates/index.js';

async function enhance({ brief, surface }) {
  const useCase = detectIntent(brief);
  const tpl = selectTemplate({ surface, useCase });
  const vars = inferVariables(brief, tpl.variablesSchema);
  const prompt = composePrompt(tpl, vars, { style: 'concise' });
  return postProcess(prompt, { surface });
}
```

**background.js (command & bridge)**

```js
chrome.commands.onCommand.addListener(async (cmd) => {
  if (cmd === 'prompter-enhance') {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const res = await chrome.tabs.sendMessage(tab.id, { type: 'PROMPTER_ENHANCE' });
    const prompt = await enhance(res);
    chrome.tabs.sendMessage(tab.id, { type: 'PROMPTER_SUGGEST', prompt });
  }
});
```

---

## E) KEYBOARD UX & CONFLICTS

- **Accept:** `Tab` (if input is ours); fallback `Ctrl+Enter` when host captures Tab.
- **Dismiss:** `Esc`
- **Variants:** `Alt+[1..3]` → Formal / Concise / Bulleted
- Prevent conflicts by overlaying a contenteditable *shadow* input while focused.

---

## F) LOCAL STORAGE & PRIVACY (MVP)

- `chrome.storage.local` keys: `history[]`, `library[]`, `settings`, `trial`.
- History item: `{ ts, surface, briefLen, promptLen, accepted:boolean }` (no PII text).
- All processing client-side. No network calls.

---

## G) ANALYTICS (LOCAL-ONLY FOR MVP)

- Counters: runs, accepts, dismisses, avg chars saved.
- Quality pulse: 2-click rating after insert (store locally).
- Export diagnostics: user can export JSON to share for support.

---

## H) READINESS CHECKLIST (GO/NO-GO)

-

---

## I) MIGRATION PATH TO LLM ADAPTERS

- Introduce `Engine` interface: `optimize(brief, surface, toggles) => prompt`
- Implement `LocalHeuristicEngine` (current) and `LLMEngine` (future).
- Add cost preview + provider picker; preserve same output contract.
- Keep **no-CoT-in-output** policy; optional 1‑line *Approach* summary.

---

## J) DEVELOPER PROMPTS (for Copilot / codegen)

**1) Scaffold Core Files**

```
Create MV3 files: manifest.json, background.js, content.js, popup.html/css/js. Add command `prompter-enhance`. Implement message bridge background↔content↔popup. Include storage helpers and overlay component stubs.
```

**2) Implement Deterministic Optimizer**

```
Write `detectIntent(brief)`, `selectTemplate({surface,useCase})`, `inferVariables(brief,schema)`, `composePrompt(tpl,vars,opts)`, `postProcess(prompt,{surface})`. Add unit tests with sample briefs. Ensure no external calls.
```

**3) Build Template Library**

```
Create `/templates` with JSON files for email, bugfix, summary, script, plan. Export index with lookup by surface/useCase. Add 2 examples each for future FEW_SHOT (stored but unused in MVP).
```

**4) Overlay & Keyboard Handling**

```
Implement a floating suggestion overlay anchored to caret. Intercept Tab only when overlay focused. Provide fallback Ctrl+Enter accept. Clean up on navigation.
```

**5) Privacy & Trials**

```
Add trial store: start_ts, days_left computed locally. Store only metrics, not raw text. Add settings page link to privacy policy.
```

**6) Tests & QA Matrix**

```
Automate e2e with Playwright + chrome extension testing. Test on ChatGPT, Claude, Gmail, GitHub, Docs. Scenarios: accept, dismiss, variant, long brief, empty brief, Tab conflict, dark mode.
```

---

## K) COPY READY – DEFAULT PROMPT (GENERIC)

```
Role: You are an expert assistant.
Context: The user provided a short brief and wants a complete, high-quality instruction.
Inputs: {AUDIENCE?} {TOPIC} {GOAL} {TONE?} {LENGTH?}
Steps:
1) Clarify the objective and constraints.
2) Outline the approach in 3–5 steps.
3) Specify any assumptions or inputs required.
4) Define the expected output format.
Constraints: Keep concise, avoid speculation, no private data.
Output Format: Markdown with sections (Goal, Steps, Constraints, Output Spec).
Review Checklist: goal clear; steps actionable; constraints explicit; format testable.
```

---

## L) ROADMAP SNAPSHOT (M0→M2)

- **M0 (this doc)**: Local heuristic engine + 5 templates + overlay + hotkeys.
- **M1**: Library ×25 templates, variant styles, history & ratings, export .md.
- **M2**: Pluggable LLM engine (OpenAI/Anthropic/Local), cost preview, evidence mode.

---

**End of v1** – paste into your repo as `docs/PROMPTER_SYSTEM_PROMPT.md` and use the *Developer Prompts* with Copilot to generate code stubs and tests.


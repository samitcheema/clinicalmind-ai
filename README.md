# ClinicalMind AI

A concept MCP server that lets clinicians query a behavioral health patient cohort in plain English — built with [FastMCP](https://github.com/jlowin/fastmcp) and Claude.

---

## What It Does

ClinicalMind AI connects a mock behavioral health dataset to Claude via the **Model Context Protocol (MCP)**. Claude decides which tools to call based on the question, fetches only what's needed, and returns a clinically relevant response — no dashboards, no filters, no SQL.

**Example queries:**
- *"Who are my highest-risk patients right now?"*
- *"Which patients have overdue SRA assessments?"*
- *"Were there any crisis events in the last 7 days?"*
- *"What's our KPI compliance rate for PHQ-9?"*
- *"Who hasn't had contact in over 30 days?"*

---

## Why MCP Instead of RAG or System Prompt Injection?

The naive approach is to load the full patient list into the system prompt on every query. MCP inverts this: Claude decides what to fetch, when, based on the question.

| Approach | Token cost per query | Stale data risk | Auditability |
|----------|---------------------|-----------------|--------------|
| Inject all patients in system prompt | ~50k tokens | High | None |
| RAG (vector search) | Low | Medium | Partial |
| **MCP tool calls (this project)** | **Only what's needed** | **None (live fetch)** | **Full** |

Every tool call is structured — arguments in, typed response out. Claude never touches data it didn't explicitly ask for.

---

## MCP Concepts Demonstrated

- **Tools** — structured function calls with typed inputs/outputs; Claude decides when and how to invoke them
- **stdio transport** — runs over standard I/O, compatible with Claude Desktop and Claude Code out of the box
- **Schema-first design** — Python `Annotated` type hints generate MCP JSON Schema automatically via FastMCP; no manual schema files
- **Adapter pattern** — data layer is swappable (mock → SQL) without touching a single tool definition
- **Scoped tool granularity** — 7 focused tools with single responsibilities instead of one flexible catch-all

---

## Architecture

```
Claude Desktop
      │
      │  natural language
      ▼
Claude API (claude-opus-4-6)
      │
      │  MCP tool calls (stdio)
      ▼
ClinicalMind MCP Server  ◄── FastMCP (Python)
      │
      │  adapter interface
      ▼
Mock Adapter (45 patients)
      │
      └──(extensible)──► SQL Adapter stub included
```

---

## Tool Schema via Python Type Hints

FastMCP converts Python type annotations directly to MCP JSON Schema — no Zod, no JSON Schema files, no manual `inputSchema` objects. The type hint *is* the contract:

```python
@mcp.tool()
def get_patients(
    risk_level: Annotated[Literal["High", "Moderate", "Low"] | None,
                           "Filter by overall risk level"] = None,
    county:     Annotated[str | None, "Partial county name match"] = None,
    provider:   Annotated[str | None, "Provider name or ID"] = None,
) -> dict:
    """Returns patient list with summary clinical data."""
```

Claude sees `risk_level` as a strict enum, `county` as optional free text. The docstring becomes the tool description. Python types are the source of truth end-to-end.

---

## Tool Granularity: Why 7 Focused Tools?

A single `query_patients(question: str)` tool would push interpretation back onto the tool itself — removing the structured contract that makes MCP valuable. Instead, each tool has a single responsibility and Claude routes to the right one:

- `get_high_risk_patients` — called when urgency or acuity is detected
- `get_crisis_events` — only invoked when safety is relevant; near-zero token cost otherwise
- `get_patient_detail` — Claude resolves *which* patient first, then calls this; no full-cohort scan
- `get_kpi_compliance` — aggregate view for population-level questions

**Tools are verbs with clear contracts**, not a single flexible endpoint.

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_patients` | Patient list with optional filters (risk level, county, provider) |
| `get_patient_detail` | Full clinical record for one patient |
| `get_high_risk_patients` | Patients flagged by PHQ-9, SSRS, or recent crisis |
| `get_kpi_compliance` | Cohort-wide KPI completion vs 75% target |
| `get_overdue_assessments` | Patients past their assessment due dates |
| `get_crisis_events` | Crisis episodes within a configurable date window (default: 28 days) |
| `get_disengaged_patients` | No contact beyond a configurable threshold (default: 30 days) |

---

## Project Structure

```
clinicalmind-ai/
└── mcp-server/
    ├── server.py              # FastMCP server — all 7 tool definitions
    ├── requirements.txt       # fastmcp>=2.0.0
    ├── adapter/
    │   ├── mock_adapter.py    # In-memory mock cohort (45 patients)
    │   └── sql_adapter.py     # Stub for real SQL — swap with one import change
    └── data/
        └── mock_data.py       # Patient generator with clinical scoring logic
```

---

## Mock Dataset

45 patients across three behavioral health teams:

| Metric | Value |
|--------|-------|
| Total patients | 45 |
| High risk | 9 |
| Moderate risk | 18 |
| Low risk | 18 |
| Overall KPI compliance | ~72% |
| Disengaged (>30 days) | 9 |
| Crisis events (28-day window) | 10 |

---

## Setup

**Prerequisites:** Python 3.10+, Claude Desktop or any MCP-compatible client

```bash
cd mcp-server
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clinicalmind": {
      "command": "/path/to/clinicalmind-ai/mcp-server/.venv/bin/python",
      "args": ["/path/to/clinicalmind-ai/mcp-server/server.py"]
    }
  }
}
```

Restart Claude Desktop. Tools appear under the hammer icon in any chat.

### Dev mode (interactive inspector)

```bash
.venv/bin/fastmcp dev server.py
```

---

## Extending This Project

The adapter pattern makes it straightforward to connect real data. Change one import line in `server.py`:

```python
# Mock (current)
from adapter.mock_adapter import ...

# Real SQL — stubs already in adapter/sql_adapter.py
from adapter.sql_adapter import ...
```

Tool definitions, descriptions, and return shapes stay the same — Claude doesn't know which adapter is running.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | [Claude](https://anthropic.com) (`claude-opus-4-6`) |
| MCP framework | [FastMCP](https://github.com/jlowin/fastmcp) (Python) |
| Transport | stdio |
| Data | Pure Python mock — no database required |

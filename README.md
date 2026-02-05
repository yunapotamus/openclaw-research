# deep-research

Multi-step web research with parallel sub-agents and citation tracking.

Give it a research question. It breaks it into sub-questions, investigates
them in parallel using sub-agents, and delivers a structured report with
deduplicated inline citations.

## Example

```
> Research the current state of solid-state batteries for EVs

I'll research "solid-state batteries for EVs" by investigating:
1. What is the current technological readiness of solid-state batteries?
2. Which companies are leading solid-state battery development?
3. How do solid-state batteries compare to lithium-ion on cost/performance?
4. What are the main technical barriers to mass production?
5. What are recent breakthroughs and timeline projections?

Mode: Deep (parallel sub-agents)

Shall I proceed, or would you like to adjust?
```

After confirmation, the agent launches parallel sub-agents, synthesizes
findings, and saves a cited report to `research/solid-state-batteries-for-evs/research.md`.

### Example Output (excerpt)

```markdown
## Executive Summary

Solid-state batteries have progressed from lab curiosity to pilot production,
with Toyota, Samsung SDI, and QuantumScape leading commercialization efforts.
Current prototypes achieve 400+ Wh/kg energy density (vs ~250 for lithium-ion)
but manufacturing costs remain 3-8x higher [1][3]. Most analysts project
limited commercial availability by 2027-2028, with cost parity unlikely
before 2030 [2][5].

## References
[1] Solid-State Battery Progress Report — https://example.com/ss-battery
[2] EV Battery Roadmap 2026 — https://example.com/ev-roadmap
...
```

## Installation

### Via ClawHub

```bash
clawhub install yunapotamus/deep-research
```

### Manual

Clone this repo into your OpenClaw skills directory:

```bash
git clone https://github.com/yunapotamus/openclaw-research.git \
  ~/.openclaw/skills/deep-research
```

## Usage

Just ask your agent to research something:

```
Research the pros and cons of microservices vs monoliths for startups
```

```
Investigate recent advances in CRISPR gene therapy, quick mode
```

```
Deep dive into the state of WebAssembly adoption in production systems
```

### Quick Mode

Add "quick", "brief", or "fast" to your request, or the agent will
auto-select quick mode for simple, single-faceted questions:

```
Quick research on current Python 3.13 release status
```

Quick mode does serial research (no sub-agents) — fewer sources but
faster results.

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│  User: "Research <topic>"                                        │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│  PHASE 1: PLAN           │
│  Decompose into 3-6      │
│  sub-questions           │
│  → Show plan to user     │
│  → Wait for confirmation │
└──────────────┬───────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Deep Mode   │ │ Quick Mode  │
└──────┬──────┘ └──────┬──────┘
       │               │
       ▼               ▼
┌──────────────────┐ ┌──────────────────┐
│ PHASE 2: RESEARCH│ │ PHASE 2: RESEARCH│
│                  │ │                  │
│ ┌─────┐ ┌─────┐  │ │ For each sub-Q:  │
│ │Sub 1│ │Sub 2│  │ │  web_search x2   │
│ │agent│ │agent│  │ │  web_fetch top 3 │
│ └──┬──┘ └──┬──┘  │ │  Record findings │
│ ┌──┴──┐    │     │ │  Next sub-Q...   │
│ │Sub 3│    │     │ └────────┬─────────┘
│ │agent│    │     │          │
│ └──┬──┘    │     │          │
│    │       │     │          │
│  ┌─┴───────┴─┐   │          │
│  │  Collect  │   │          │
│  │  results  │   │          │
│  └─────┬─────┘   │          │
└────────┼─────────┘          │
         └──────┬─────────────┘
                │
                ▼
┌───────────────────────────────┐
│  PHASE 3: SYNTHESIZE          │
│  - Deduplicate citations      │
│  - Cross-reference findings   │
│  - Identify consensus/gaps    │
│  - Rate confidence levels     │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  PHASE 4: DELIVER             │
│  - Write structured report    │
│  - Save to workspace          │
│  - Show executive summary     │
│  - Offer to go deeper         │
└───────────────────────────────┘
```

## Configuration

The skill uses sensible defaults. You can adjust behavior through
your research prompt:

| Option | How to set it | Default |
|--------|--------------|---------|
| Mode | Say "quick" or "deep" | Auto (based on complexity) |
| Sub-questions | "Focus on X and Y" | 3-6 auto-generated |
| Depth | "Be thorough" / "Keep it brief" | Moderate |
| Recency | "Only last 6 months" | Prefers last 1-2 years |
| Output path | "Save to reports/" | `research/<topic-slug>/` |

### Sub-agent Timeout

Sub-agents time out after 120 seconds by default. If a sub-agent times
out, the report notes the gap and offers to retry.

## Report Formatting

The included helper script can clean up and validate reports:

```bash
# Validate citations (check only, no changes)
python scripts/format-report.py research/topic/research.md --check

# Renumber citations and deduplicate
python scripts/format-report.py research/topic/research.md

# Export to PDF (requires pandoc)
python scripts/format-report.py research/topic/research.md --pdf
```

## Limitations

- **Source quality**: The agent searches the open web. It cannot access
  paywalled journals, internal databases, or authenticated resources.
- **Recency**: Web search indexes may lag a few days behind real-time events.
- **Depth**: Each sub-agent runs 2-3 searches with 3-5 fetches. For exhaustive
  academic literature review, a specialized tool is more appropriate.
- **No API keys**: Uses only built-in OpenClaw tools. This means no access
  to specialized APIs (Semantic Scholar, PubMed, etc.) unless you add them.
- **Model-agnostic**: Works with any model supported by OpenClaw (Anthropic,
  OpenAI, Gemini), but quality varies by model capability.

## Contributing

Contributions welcome. Some ideas:

- **More output formats**: HTML, DOCX, LaTeX
- **Source scoring**: Rank sources by domain authority
- **Incremental research**: "Update my last report on X with new findings"
- **Academic mode**: Integration with Semantic Scholar / arXiv APIs
- **Fact-checking pass**: Cross-validate claims against known reliable sources

To contribute:

1. Fork this repo
2. Create a branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test with a real research query
5. Open a PR

## License

MIT — see [LICENSE](LICENSE).

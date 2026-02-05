# Changelog

## 1.0.0 — 2026-02-05

### Added
- Initial release
- Phase-based research workflow: Plan → Research → Synthesize → Deliver
- Parallel sub-agent research via `sessions_spawn`
- Quick mode for simpler questions (serial, single-agent)
- Global citation deduplication (same URL = same reference number)
- Cross-cutting analysis: consensus, contradictions, gaps, confidence
- Structured markdown report output with inline citations
- Automatic workspace save to `research/<topic-slug>/research.md`
- Sub-agent timeout handling (120s default) with graceful fallback
- format-report.py helper for citation renumbering and cleanup

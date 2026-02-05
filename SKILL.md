---
name: deep-research
description: >
  Multi-step web research with parallel sub-agents and citation tracking.
  Use when the user asks to research a topic in depth, investigate a question
  thoroughly, compare options with sources, or produce a cited research report.
  Triggers on: "research", "investigate", "deep dive", "find out about",
  "compare X vs Y with sources", "literature review", "what does the evidence say".
emoji: 🔬
dependencies: []
tags:
  - research
  - web-search
  - citations
  - parallel
---

# Deep Research Skill

You are a research agent. Your job is to take a research question, decompose it,
investigate sub-questions in parallel, and produce a cited report.

## Mode Selection

First, determine the research mode:

- **Deep mode** (default): Parallel sub-agents, thorough coverage.
  Use for complex, multi-faceted questions.
- **Quick mode**: Serial research, single agent, faster.
  Use when the user says "quick", "brief", "fast", or the question is simple
  and single-faceted.

If the user hasn't specified, choose based on question complexity.

## Search Provider Detection

Before Phase 1, run a single short `web_search` query related to the topic.
Check the response format to detect the search provider:

- **Perplexity Sonar**: Returns synthesized prose with inline citations and
  source URLs already extracted. You do NOT need to `web_fetch` individual pages.
- **Standard search** (Brave, Google, etc.): Returns a list of result links
  with short snippets. You MUST `web_fetch` pages to get full content.

Remember which provider you detected — it changes the sub-agent instructions
in Phase 2. You can reuse this initial search result as part of Phase 2.

---

## PHASE 1: PLAN

Break the research question into **3–6 sub-questions** that together cover
the full scope. Each sub-question should target a distinct angle:

- Core facts / definitions
- Current state / recent developments
- Competing viewpoints or alternatives
- Evidence quality / data sources
- Practical implications / applications
- Risks, limitations, or criticisms

Present the plan to the user:

```
I'll research "<topic>" by investigating these sub-questions:

1. <sub-question>
2. <sub-question>
3. <sub-question>
...

Mode: [Deep / Quick]

Shall I proceed, or would you like to adjust the sub-questions?
```

Wait for user confirmation before proceeding.

---

## PHASE 2: RESEARCH

### Deep Mode (parallel sub-agents)

For **each** sub-question, spawn a background sub-agent:

```
sessions_spawn background:true timeout:120
```

Give each sub-agent the appropriate prompt based on the detected provider:

**Standard search prompt** (Brave, Google, etc.):

```
Research the following question thoroughly:
"<sub-question>"

Instructions:
1. Run 2-3 different web_search queries approaching the question
   from different angles (try synonyms, related terms, specific vs broad)
2. For each search, web_fetch the 3 most relevant results
3. Extract key findings with source attribution
4. Note when sources disagree or data is uncertain

Return your findings in this EXACT format:

## Findings
- [Finding 1] (Source: <url>)
- [Finding 2] (Source: <url>)
- [Finding 3] (Source: <url>)

## Sources
1. <title> — <url> — <brief description>
2. <title> — <url> — <brief description>

Be thorough. Prefer recent sources (last 1-2 years). Note disagreements.
```

**Perplexity Sonar prompt** (search results are already synthesized):

```
Research the following question thoroughly:
"<sub-question>"

Instructions:
1. Run 2-3 different web_search queries approaching the question
   from different angles (try synonyms, related terms, specific vs broad)
2. DO NOT web_fetch — search results already include synthesized content
   with source URLs. Extract findings directly from search responses.
3. Collect all source URLs from the search response citations
4. Note when sources disagree or data is uncertain

Return your findings in this EXACT format:

## Findings
- [Finding 1] (Source: <url>)
- [Finding 2] (Source: <url>)
- [Finding 3] (Source: <url>)

## Sources
1. <title> — <url> — <brief description>
2. <title> — <url> — <brief description>

Be thorough. Prefer recent sources (last 1-2 years). Note disagreements.
```

After spawning all sub-agents:
1. Inform the user: "Researching N sub-questions in parallel..."
2. Monitor sub-agent sessions for completion
3. If a sub-agent times out after 120s, note the gap and continue
4. Collect all results once finished

### Quick Mode (serial)

Do the research yourself sequentially:

For each sub-question:
1. Run 2 `web_search` queries from different angles
2. **Standard search**: `web_fetch` the top 2-3 results from each search
   **Perplexity Sonar**: Skip `web_fetch` — extract findings and source
   URLs directly from the synthesized search response
3. Record findings with source URLs
4. Move to the next sub-question

---

## PHASE 3: SYNTHESIZE

### 3a. Collect & Parse

Gather all findings from sub-agents (or your own serial research).
Parse each finding into: `{claim, source_url, source_title, sub_question}`.

### 3b. Deduplicate Citations

Build a **global reference list**. Rules:
- Same URL = same reference number everywhere in the report
- Assign `[1]`, `[2]`, `[3]`... in order of first appearance
- Strip tracking parameters from URLs before comparing
  (`utm_source`, `utm_medium`, `fbclid`, etc.)

### 3c. Cross-Reference

Across all sub-question results:
- **Consensus**: Claims supported by 2+ independent sources
- **Contradictions**: Claims where sources disagree — note both sides
- **Gaps**: Sub-questions with thin or no results
- **Confidence**: Rate each major finding (high / medium / low) based
  on source quality and agreement

### 3d. Handle Failures

- If a sub-agent timed out: note which sub-question has incomplete data
- If a sub-question yielded no useful results: note the gap explicitly
- Never fabricate sources or findings

---

## PHASE 4: DELIVER

### 4a. Write the Report

Use this format exactly:

```markdown
# <Research Topic>

**Date:** YYYY-MM-DD
**Status:** Complete | Partial (if gaps exist)
**Sub-questions researched:** N

---

## Executive Summary

<2-3 paragraphs synthesizing all key findings. Lead with the most important
conclusions. Mention confidence levels for major claims.>

## Detailed Findings

### <Sub-topic 1>
- Finding with inline citation [1]
- Finding with citation [2]
- <Note any disagreements between sources>

### <Sub-topic 2>
- Finding with citation [3]
- Finding with citation [1] (reuse if same source)

### <Sub-topic N>
...

## Cross-cutting Analysis

### Consensus
- <Claims well-supported across multiple sources>

### Contradictions
- <Where sources disagree, with citations for each side>

### Gaps & Limitations
- <What couldn't be determined, and why>

### Confidence Assessment
| Finding | Confidence | Basis |
|---------|-----------|-------|
| <key claim> | High/Med/Low | <why> |

## Recommendations / Next Steps
<If applicable: what to investigate further, actions to take>

## References
[1] <Title> — <URL>
[2] <Title> — <URL>
...
```

### 4b. Save to Workspace

```
write path:"research/<topic-slug>/research.md"
```

Where `<topic-slug>` is the topic in lowercase, spaces replaced with hyphens,
special characters removed. Example: "AI Safety in 2026" → `ai-safety-in-2026`.

### 4c. Share via Messaging (optional)

If the user asks to share the report, or if the conversation originated from
a messaging integration, attach the saved report file. Use whichever tool
is available:

- **Slack**: `slack action:"sendMessage" to:"<channel>" content:"Research report: <topic>" mediaUrl:"file://research/<topic-slug>/research.md"`
- **Discord**: `discord action:"sendMessage" to:"<channel>" content:"Research report: <topic>" mediaUrl:"file://research/<topic-slug>/research.md"`
- **iMessage**: `imsg send --to "<recipient>" --text "Research report: <topic>" --file research/<topic-slug>/research.md`
- **BlueBubbles**: `bluebubbles action:"sendAttachment" path:"research/<topic-slug>/research.md" caption:"Research report: <topic>"`

Rules:
- Only share if the user requests it or the conversation context implies it
  (e.g., user asked from a Slack channel)
- If the messaging tool isn't available, skip silently — just deliver via
  the saved file and chat summary
- Include a brief caption with the topic name, not the full summary

### 4d. Present to User

Show the **Executive Summary** directly in chat, then:

```
Full report saved to: research/<topic-slug>/research.md

I found N sources across M sub-questions.

Would you like me to:
- Go deeper on any section?
- Research additional angles?
- Share the report to a channel or contact?
- Export in a different format?
```

---

## ERROR HANDLING

- **Sub-agent timeout**: Log which sub-question was affected.
  Include a "Gaps" note in the report. Offer to retry that sub-question.
- **No search results**: Try alternative search queries (broader terms,
  different phrasing). If still nothing, note the gap honestly.
- **web_fetch failures**: Skip the URL, note it, try the next result.
- **All sub-agents fail**: Fall back to quick mode automatically.
  Inform the user: "Parallel research failed; switching to quick mode."

---

## RULES

1. **Every claim needs a citation.** No unsourced assertions in findings.
2. **Never invent URLs or sources.** If you can't find it, say so.
3. **Prefer recent sources** — within the last 1-2 years when possible.
4. **Be honest about uncertainty.** "Low confidence" is better than false certainty.
5. **Keep the executive summary readable** — no jargon walls, no citation spam.
   Save detailed citations for the findings sections.
6. **Respect the user's time.** If quick mode is more appropriate, suggest it.
7. **No external API keys required.** Use only built-in tools: `web_search`,
   `web_fetch`, `sessions_spawn`, `read`, `write`.
8. **Skip `web_fetch` with Perplexity Sonar.** If search results are already
   synthesized with citations, fetching individual pages wastes time and tokens.

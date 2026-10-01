# JOB RADAR — Project Status & Agent Control File

## 1. Project Goal

Build a personal, zero-recurring-cost job discovery system for a Java developer that continuously finds the freshest relevant jobs in India and presents only useful opportunities instead of forcing the user to manually search job portals for hours.

The system should maximize legitimate public-source coverage, minimize discovery delay, distinguish original publication time from discovery time, remove duplicates/reposts, rank jobs for the user's profile, and eventually learn from the user's own feedback.

### Core requirements

- Freshness-first: prioritize jobs actually published recently.
- India-first: especially Ahmedabad, Gujarat, Bengaluru, Hyderabad, Pune, Mumbai, Chennai, Delhi NCR and Remote India.
- Java-first: Java, Spring Boot, backend, microservices and full-stack roles.
- Experience target: approximately 1.5 years; default acceptable range 0–3 years.
- Maximum legitimate source coverage.
- No unauthorized scraping, access-control bypass, CAPTCHA bypass, proxy evasion or login automation against restricted job portals.
- Zero recurring cost.
- No dependency on Gemini, OpenAI, Claude or another cloud LLM API.
- Core cloud collector must work completely without AI.
- Local AI is optional and runs on the user's Windows machine.
- The system must survive source failures and continue collecting from healthy sources.
- The system must become better over time through source performance and user-feedback learning.

---

## 2. Architecture Direction

### Cloud / always-on collector

Runs through GitHub Actions and performs:

1. Direct ATS collection.
2. Public RSS/feed/community ingestion.
3. Supplementary dataset ingestion.
4. Source discovery.
5. Normalization.
6. Cross-source deduplication.
7. Repost detection.
8. Freshness classification.
9. Experience/location/relevance filtering.
10. Deterministic ranking.
11. Source health and adaptive polling.
12. Static JSON/site export.
13. Optional Telegram notifications.

### Local / optional intelligence

Runs on Windows and performs:

1. Local embeddings using Sentence Transformers.
2. Semantic job/profile similarity.
3. Semantic duplicate detection.
4. Personal ranking model using user feedback.
5. Optional local LLM through Ollama/Qwen for ambiguous jobs only.
6. Optional future model fine-tuning only after sufficient labeled data.

The cloud collector MUST NOT depend on local AI.

---

## 3. Zero-Cost Rules

Never introduce a mandatory paid service or cloud AI API.

Do not make the system dependent on temporary free-tier quotas.

Allowed free-first components include:

- GitHub public repository.
- GitHub Actions.
- GitHub Pages.
- Public employer/ATS endpoints and feeds.
- Open-source libraries and datasets with compatible licenses.
- Python.
- SQLite for ephemeral/local storage.
- Local Sentence Transformers.
- Local scikit-learn/LightGBM.
- Local Ollama/Qwen.
- Telegram Bot API for optional notifications.

---

## 4. Current Phase Status

### Total phases

- Phase 0 = architecture/audit.
- Phases 1–13 = implementation phases.
- Total including Phase 0: 14 phases.
- Completed: Phase 0, 1, 2, 3.
- Remaining: Phase 4 through Phase 13 = 10 phases.
- Implementation phases completed: 3 of 13.
- Overall including Phase 0: 4 of 14 phases completed.

### Completed

| Phase | Name | Status |
|---|---|---|
| 0 | Architecture + Repository Audit | COMPLETE |
| 1 | Core Models, Registry, Persistence Engine | COMPLETE |
| 2 | Real ATS Adapters / End-to-End Collection | COMPLETE |
| 3 | Broad & Fresh Java Discovery / Filtering / Dedup | COMPLETE |

### Current next phase

**Phase 4 — Quality Validation + Real User Targeting**

### Remaining

| Phase | Name | Status |
|---|---|---|
| 4 | Quality Validation + Real User Targeting | NEXT |
| 5 | Source Discovery Expansion | PENDING |
| 6 | Feed + Alert Ingestion | PENDING |
| 7 | Automated Refresh + Adaptive Scheduling | PENDING |
| 8 | Web Dashboard | PENDING |
| 9 | Local Semantic AI | PENDING |
| 10 | Personal Learning / Ranking Model | PENDING |
| 11 | Local LLM / Ollama | PENDING |
| 12 | Notifications | PENDING |
| 13 | Optional Local Browser Assistance | PENDING |

Do not skip phases without explicit user approval.

---

## 5. Phase 0 Result

Architecture established with:

- public ATS/direct-source strategy;
- jobhive as supplementary snapshot coverage, not a freshness source;
- persistent state branch strategy;
- adaptive source tiers P0/P1/P2/P3;
- cloud/local separation;
- provenance-aware Job model;
- no mandatory cloud AI;
- local AI only as an optional later layer.

Important architectural decisions:

- `posted_at` is never inferred from `first_seen_at`.
- Jobhive snapshot timestamp is never treated as publisher timestamp.
- GitHub Actions runners are ephemeral, so cross-run state is persisted separately.
- High-value sources should be polled more frequently than the full registry.
- Search/discovery is supplementary, not a universal real-time job database.

---

## 6. Phase 1 Result

Implemented and tested:

- Job model.
- Source model.
- CollectorRun model.
- UserAction model.
- YAML configuration loading.
- SQLite repository.
- Persistent state files.
- Source registry.
- Adaptive source scoring/tiering.
- Source health.
- Selective jobhive reader.
- JSON exporter.
- GitHub Actions workflow foundations.

Phase 1 reported 21 passing tests.

---

## 7. Phase 2 Result

Live ATS collection was proven against public endpoints:

- Greenhouse.
- Lever.
- Ashby.

Reported live verification:

- 741 live jobs collected.
- 741 had trustworthy `posted_at` timestamps.
- Re-running produced 0 new jobs and preserved `first_seen_at`.
- Invalid source handling did not stop the run.
- Offline tests used recorded real API fixtures.
- Reported coverage: 87% overall.

Important limitation discovered:

This proved real collection and idempotency, but the initial test companies were not representative of the full India-focused target.

---

## 8. Phase 3 Result

Expanded live collection to 7 ATS platforms:

- Greenhouse.
- Lever.
- Ashby.
- Workable.
- SmartRecruiters.
- Recruitee.
- BambooHR.

Reported live metrics:

- 37 companies tested.
- 18 successful sources.
- 19 failed sources handled gracefully.
- 2,667 live jobs collected.
- 333 Java-relevant jobs.
- 125 India-located jobs.
- 2,653 jobs with trustworthy `posted_at`.
- 135 jobs under 24h.
- 174 jobs under 48h.
- 205 jobs under 72h.
- 270 jobs detected as possible reposts.
- 50 tests passed offline.

Implemented deterministic filtering for:

- Java/Spring/backend/full-stack relevance.
- Experience.
- Indian location normalization.
- Remote/hybrid/onsite classification.
- Cross-source deduplication.
- Repost detection.
- Source health semantics.

Known limitation:

The Phase 3 report proves the pipeline works, but further validation is required for true cross-source deduplication, repost confidence and the specific KPI `Java + India + <24h` / `<48h` / `<72h`.

---

## 9. REQUIRED PHASE 4 OBJECTIVE

Phase 4 must NOT add local AI yet.

It must first prove the deterministic system is producing useful results.

### Phase 4 must verify

1. Real cross-source duplicates.
2. Repost confidence rather than blindly labeling all similar jobs as reposts.
3. Correct source-health semantics.
4. Strong Java relevance filtering.
5. Strong experience parsing.
6. Location normalization.
7. Freshness-first ranking.
8. India-specific product metrics.

### Mandatory metrics

Every verification run should report:

- `total_jobs`
- `java_relevant`
- `india_relevant`
- `java_india`
- `java_india_under_24h`
- `java_india_under_48h`
- `java_india_under_72h`
- `fresh_java_total`
- `fresh_java_india`
- `duplicate_count`
- `repost_count`
- `sources_ok`
- `sources_degraded`
- `sources_failed`

### Phase 4 must NOT

- add Gemini;
- add OpenAI;
- add Claude;
- add another cloud AI API;
- start LLM processing;
- aggressively scrape restricted portals.

The deterministic top 20 should become useful before local AI is introduced.

---

## 10. Remaining Phase Specifications

### Phase 5 — Source Discovery Expansion

Goal: grow the registry automatically instead of relying on manual company lists.

Use:

- existing ATS/company inventories;
- validated career URLs;
- discovered ATS boards;
- open-source public company/source datasets;
- supplementary search/discovery signals.

Validate every candidate before activation.

Do not blindly add thousands of unverified sources.

Use adaptive tiers:

- P0: approximately 100–300 highest-value companies, around 15 min.
- P1: approximately 500–2,000 relevant companies, around 30–60 min.
- P2: remaining validated sources, around 6–24h.
- P3: discovery/low-value/unhealthy sources, slow or weekly.

Automatic promotion/demotion must use source usefulness, freshness, reliability and failure rate.

---

### Phase 6 — Feed + Alert Ingestion

Add:

- RSS/Atom;
- public JSON feeds;
- community sources;
- optional native job-alert email ingestion.

Possible alert sources:

- LinkedIn native alerts;
- Naukri native alerts;
- Indeed native alerts;
- company alert emails;
- recruiter alerts.

Normalize alerts into the common Job model and deduplicate against direct sources.

No portal-login scraping.

---

### Phase 7 — Automated Refresh + Adaptive Scheduling

Implement:

- GitHub Actions schedules;
- P0/P1/P2 adaptive polling;
- retries;
- timeout handling;
- exponential backoff;
- source health;
- concurrency control;
- persistent state updates;
- static exports.

Do not assume scheduled execution occurs at the exact requested minute.

Prevent concurrent state-writing workflows.

---

### Phase 8 — Web Dashboard

Build a mobile-first static dashboard.

Display:

- NEW jobs;
- freshness;
- score;
- location;
- experience;
- source;
- skills;
- Apply link;
- Save;
- Hide;
- Applied;
- filters;
- search;
- source health;
- last refresh.

Important display distinction:

`Published X ago` only when the publication timestamp is trustworthy.

Otherwise:

`First seen X ago` or `Publication time unknown`.

Add one-click fallback search buttons for major job portals without scraping them.

---

### Phase 9 — Local Semantic AI

Local only.

Use Sentence Transformers initially.

Start with a lightweight embedding model such as `all-MiniLM-L6-v2`.

Use it for:

- profile/job semantic similarity;
- title similarity;
- skill equivalence;
- semantic duplicate detection.

Do not call any cloud AI API.

Do not run an LLM on every job.

---

### Phase 10 — Personal Learning / Ranking Model

Track local user actions:

- viewed;
- saved;
- hidden;
- applied;
- interview;
- rejected;
- ignored.

Create local training examples and features.

Use LightGBM or scikit-learn after enough labeled examples exist.

Evaluate using held-out validation data and ranking metrics such as precision@10 and precision@20.

Do not train until there is enough real feedback.

---

### Phase 11 — Local LLM / Ollama

Optional.

Use Ollama with a suitable small local model such as Qwen3.

Only use the local LLM for ambiguous/low-confidence cases.

Use an uncertainty gate so deterministic rules and embeddings handle normal jobs.

Require structured JSON output.

The system must work normally when Ollama is not installed.

Do not fine-tune initially.

---

### Phase 12 — Notifications

Add optional Telegram notifications.

Use:

- instant alert for genuinely high-priority new jobs;
- daily digest for other useful fresh jobs;
- duplicate notification suppression;
- notification history;
- retry handling.

Do not spam the user.

---

### Phase 13 — Optional Browser Assistance

Only after the discovery/ranking system is stable.

Possible local browser assistance may use Browser Use or similar open-source tooling.

It must remain user-controlled.

Never:

- bypass CAPTCHA;
- bypass access controls;
- evade website restrictions;
- use proxy tricks to defeat blocks;
- automatically submit applications without user confirmation.

---

## 11. Source Strategy Rules

Priority order:

1. Direct employer ATS/API.
2. Employer public career page.
3. Public ATS page.
4. Public RSS/JSON feed.
5. Trusted structured aggregator/community source.
6. Native job-alert email.
7. Search/discovery signal.

A lower-tier source can still produce a useful job, but its freshness confidence must reflect the source quality.

---

## 12. Freshness Rules

Never confuse:

- `posted_at`
- `updated_at`
- `fetched_at`
- `first_seen_at`
- `last_seen_at`

If original publication time is unavailable, explicitly mark it as unknown/estimated.

Freshness classes:

- `<6h`
- `<12h`
- `<24h`
- `24–48h`
- `48–72h`
- `3–7d`
- `>7d`
- `UNKNOWN`

The product's most important target KPI is:

**Java + India + recent publication time.**

---

## 13. Engineering Rules

- Never let one source failure stop the entire collector.
- Use timeouts and bounded concurrency.
- Use retry with exponential backoff.
- Respect source rate limits.
- Keep adapters isolated.
- Keep all user/profile tuning in configuration.
- Pin important dependency versions.
- Prefer reusable open-source adapters when licenses permit.
- Never hide failures.
- Never fabricate timestamps.
- Never silently delete historical job state.
- Never store secrets in the repository.
- Keep user actions, resume and private training data local/private.

---

## 14. Git / Collaboration Rules

The GitHub repository is the canonical shared project repository.

Repository:

`https://github.com/hussainvali2003/job-search-automation.git`

### Branch policy

Prefer:

- `main` = stable approved work.
- `phase-04-*` = phase work.
- `feature-*` = small independent features.

Do not force-push.

Before pushing:

1. `git status`
2. check changed files;
3. ensure no secrets/private data are included;
4. run tests;
5. update this file;
6. commit;
7. push.

When a phase is completed, push the phase changes and this status file to GitHub.

Never overwrite another contributor's work.

Before starting work on a new phase:

- fetch latest changes;
- inspect current branch status;
- integrate/rebase safely when appropriate;
- do not discard unknown changes made by another contributor.

---

## 15. Mandatory Status-File Update After EVERY Phase

At the end of EVERY completed phase, update this file BEFORE declaring the phase complete.

Update:

1. Overall completion counts.
2. Current phase.
3. Completed phase row.
4. Date/time of completion.
5. Summary of implementation.
6. Important metrics.
7. Tests and test results.
8. Known limitations/issues.
9. Next phase.

Use this template:

```text
Phase X
Status: COMPLETE
Completed at: YYYY-MM-DD HH:MM IST

Implemented:
- ...

Measured:
- ...

Tests:
- ...

Known limitations:
- ...

Next phase:
- ...
```

Then:

```bash
git add .
git status
git commit -m "phase-X: complete <short description>"
git push
```

The status file must accurately describe what was actually implemented. Do not mark a phase complete merely because code exists.

---

## 16. Antigravity Operating Procedure

At the start of every phase:

1. Read this file completely.
2. Inspect the current repository.
3. Inspect current Git status.
4. Read the current phase requirements.
5. Produce a detailed implementation plan.
6. WAIT for user approval.
7. Implement only the approved phase.
8. Run unit/integration tests.
9. Perform live verification when the phase requires it.
10. Report actual metrics.
11. Update this file.
12. Show the Git diff/status.
13. Commit the phase.
14. Push to GitHub.
15. STOP and wait for approval for the next phase.

Do not silently proceed through multiple phases.

---

## 17. Current Starting Point

Current phase: **PHASE 4**

Phase 0: COMPLETE
Phase 1: COMPLETE
Phase 2: COMPLETE
Phase 3: COMPLETE
Phase 4: NEXT
Phase 5: PENDING
Phase 6: PENDING
Phase 7: PENDING
Phase 8: PENDING
Phase 9: PENDING
Phase 10: PENDING
Phase 11: PENDING
Phase 12: PENDING
Phase 13: PENDING

The next task is to implement Phase 4 according to its specification above.

DO NOT start Phase 5 until Phase 4 is tested, documented in this file, committed, pushed, and explicitly approved by the user.

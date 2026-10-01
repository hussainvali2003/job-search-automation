# JOB RADAR

> Zero-Cost, Fresh-First, Multi-Source Java Job Discovery System

JOB RADAR is a continuous job discovery system designed for Java developers (Spring Boot, Microservices, Kafka, Redis, Docker, AWS). It automatically collects, normalizes, deduplicates, and ranks software engineering job opportunities from public ATS endpoints, feeds, and datasets.

## Architecture Highlights

* **Adaptive Source Tiers (P0–P3)**: Prioritizes high-value sources on 15-minute polling schedules while running remaining validated sources on 6–24 hour cadences.
* **Source Value Score**: Automatically promotes/demotes polling tiers based on yield, freshness, reliability, failure rates, and duplicate ratios.
* **Manifest-Driven Ingestion**: Selectively ingests relevant ATS snapshot partitions without full memory loading.
* **State Persistence**: Uses GitHub Actions `concurrency` locks and safe git rebase loops for state branch persistence.
* **Zero Cost**: 100% free runner deployment via GitHub Actions and presentation via GitHub Pages.

## Directory Layout

* `collector/` — Python collection engine & CLI
* `config/` — Declarative YAML configurations (profile, scoring, sources, filters)
* `data/` — Source registry and priority lists
* `tests/` — Comprehensive unit and integration test suite

## Usage

```bash
# Run P0 tier collection
python -m collector.main --tier P0

# Run P1 tier collection
python -m collector.main --tier P1

# Run tests
pytest tests/
```

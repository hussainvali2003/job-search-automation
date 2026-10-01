import argparse
import asyncio
import sys
from pathlib import Path
from collector.core.config import load_config
from collector.core.database import Database
from collector.core.state import StateManager
from collector.core.exporter import Exporter
from collector.core.models import CollectorRun
from collector.sources.registry import SourceRegistry
from collector.sources.score import SourceScoreEvaluator
from collector.sources.factory import create_adapter
from collector.sources.health import HealthTracker
from collector.core.deduplication import DeduplicationEngine
from collector.core.filtering import evaluate_java_relevance
from collector.core.experience import extract_experience, is_experience_eligible
from collector.core.location import normalize_location
from collector.core.freshness import compute_freshness_metrics
from collector.core.logger import logger

def parse_args():
    parser = argparse.ArgumentParser(description="JOB RADAR Collector Engine")
    parser.add_argument("--tier", choices=["P0", "P1", "P2", "P3"], default="P0", help="Polling tier to execute")
    parser.add_argument("--config-dir", default="config", help="Directory containing YAML configuration files")
    parser.add_argument("--registry-file", default="data/source_registry.json", help="Path to source registry JSON")
    parser.add_argument("--state-dir", default="state", help="Directory storing cloud state JSON files")
    parser.add_argument("--output-dir", default="output", help="Directory for exported public JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode without committing state")
    return parser.parse_args()

async def main_async():
    args = parse_args()
    logger.info(f"Starting JOB RADAR Collector Run (Tier: {args.tier}, Dry-Run: {args.dry_run})")
    
    # 1. Load Config & Registry
    cfg = load_config(args.config_dir)
    registry = SourceRegistry(args.registry_file)
    state_mgr = StateManager(args.state_dir)
    exporter = Exporter(args.output_dir)
    
    run = CollectorRun(tier_run=args.tier)
    sources = registry.get_sources(tier=args.tier, enabled_only=True)
    logger.info(f"Found {len(sources)} active sources for tier {args.tier}")
    
    db = Database(":memory:")
    fetched_jobs = []
    
    # 2. Process Sources via Adapter Factory
    for s in sources:
        run.sources_polled += 1
        adapter = create_adapter(s)
        res = await adapter.fetch_jobs()

        if res.is_success:
            run.sources_successful += 1
            rel_count = 0
            fresh_count = 0

            for j in res.jobs:
                run.jobs_fetched += 1

                # Location normalization
                norm_loc, country, remote, workplace_type = normalize_location(j.location, j.remote)
                j.location = norm_loc
                j.country = country
                j.remote = remote

                # Experience extraction
                exp_min, exp_max = extract_experience(f"{j.title} {j.description or ''}")
                j.experience_min = exp_min
                j.experience_max = exp_max

                # Java relevance evaluation
                is_rel, rel_score, signals = evaluate_java_relevance(j.title, j.description)
                j.relevance_score = rel_score
                if is_rel:
                    rel_count += 1

                if j.freshness_class in ["<6h", "<12h", "<24h", "24-48h"]:
                    fresh_count += 1

                # Deduplication & Repost Detection
                processed_job, _ = DeduplicationEngine.process_job(j, db, state_mgr)
                if processed_job.is_new:
                    run.jobs_new += 1
                else:
                    run.jobs_duplicates += 1

                db.save_job(processed_job)
                fetched_jobs.append(processed_job)

            HealthTracker.record_success(s, res.duration_ms, len(res.jobs), rel_count, fresh_count)
        else:
            run.sources_failed += 1
            HealthTracker.record_failure(s, res.duration_ms, res.error_message or "Fetch failed")

        state_mgr.update_source_health(s)
        db.save_source(s)

    # 3. Evaluate Tiers
    SourceScoreEvaluator.evaluate_all(registry.sources)
    
    # 4. Finalize Run
    run.finalize("COMPLETED")
    db.save_run(run)
    state_mgr.add_run_summary(run)
    
    # 5. Persist State & Export JSONs if not dry-run
    if not args.dry_run:
        state_mgr.save_state()
        registry.save_registry()
        exporter.export_jobs(fetched_jobs)
        exporter.export_metadata(run)
        exporter.export_source_health(registry.sources)
        logger.info("Successfully persisted state branch files and public JSON exports.")

    freshness_metrics = compute_freshness_metrics(fetched_jobs)
    logger.info(f"Freshness metrics: {freshness_metrics}")

    db.close()
    logger.info(f"Run {run.run_id} finished in {run.duration_seconds:.2f}s. Jobs fetched: {run.jobs_fetched} (New: {run.jobs_new})")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()

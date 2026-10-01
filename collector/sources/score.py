from typing import Sequence
from collector.core.models import Source
from collector.core.logger import logger

class SourceScoreEvaluator:
    @staticmethod
    def evaluate_all(sources: Sequence[Source]) -> dict[str, int]:
        """Evaluates scores and updates tiers for all sources. Returns summary count of tier distributions."""
        tier_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for s in sources:
            old_tier = s.tier
            new_tier = s.evaluate_tier_promotion()
            if old_tier != new_tier:
                logger.info(f"Source '{s.source_id}' re-tiered: {old_tier} -> {new_tier} (Score: {s.source_value_score:.1f})")
            tier_counts[new_tier] = tier_counts.get(new_tier, 0) + 1
        return tier_counts

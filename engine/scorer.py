"""Scoring logic for interest radar.

Implements rule-based scoring plus recall-based boost.
"""

from typing import List, Dict, Any


class RelevanceScorer:
    """Assigns relevance score to content based on context."""

    def __init__(self, provider):
        self.provider = provider

    def score(
        self,
        title: str,
        summary: str,
        entities: List[str],
        recall_results: List[Dict[str, Any]],
        provider,
    ) -> tuple[int, str, Dict[str, Any]]:
        """Compute relevance score and bucket.

        Args:
            title, summary, entities: extracted from content
            recall_results: from provider.recall()
            provider: current context provider (for interest snapshot)

        Returns:
            (score, bucket, components) where components breaks down points.
        """
        text = f"{title} {summary}".lower()
        comp = {
            "project_impact": 0,
            "interest_match": 0,
            "novelty": 0,
            "actionability": 0,
            "source_cred": 0,
            "timing": 0,
            "recall_boost": 0,
        }

        # 1. project impact (0-35)
        active_projects = provider.get_active_projects()
        project_hits = 0
        for proj in active_projects:
            # any keyword overlap between project keywords and entities
            pkw = [k.lower() for k in proj.get("keywords", [])]
            if any(ent in pkw for ent in entities):
                project_hits += 1
        comp["project_impact"] = min(35, project_hits * 12)

        # 2. interest alignment (0-20)
        interests = provider.get_interests()
        interest_hits = 0
        for interest in interests:
            ilabel = interest["label"].lower()
            # any entity appears in interest label?
            if any(ent in ilabel for ent in entities):
                interest_hits += 1
        comp["interest_match"] = min(20, interest_hits * 5)

        # 3. novelty (0-15)
        change_words = [
            "release", "released", "launch", "new", "sdk", "api",
            "breaking", "deprecat", "security", "major", "update",
        ]
        novelty = 5
        novelty += sum(2 for w in change_words if w in text)
        comp["novelty"] = min(15, novelty)

        # 4. actionability (0-15)
        action_words = ["sdk", "api", "release", "migration", "deprecated", "breaking", "guide", "benchmark"]
        comp["actionability"] = min(15, sum(3 for w in action_words if w in text))

        # 5. source credibility (0-10) - default moderate
        comp["source_cred"] = 6  # default neutral

        # 6. timing (0-5)
        # we don't have timestamp here; assume recent => 3
        comp["timing"] = 3

        # 7. recall boost
        if recall_results:
            boost = 18 if len(recall_results) >= 3 else 12
            comp["recall_boost"] = boost
        else:
            boost = 0

        total = sum(comp.values())

        # bucket
        if total >= 75:
            bucket = "top"
        elif total >= 55:
            bucket = "watch"
        elif total >= 35:
            bucket = "silent"
        else:
            bucket = "ignore"

        return total, bucket, comp

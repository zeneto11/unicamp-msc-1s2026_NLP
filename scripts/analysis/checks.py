"""Output checks for the V2 analysis phases.

Validates the artifacts produced by phases 1-4 before they are loaded into Neo4j.
Each check appends a PASS / FAIL / WARN / SKIP row; missing artifacts are SKIPped
so the suite can run after any subset of phases.

Run:  python -m scripts.analysis.checks
"""
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG, EMOTION_CATEGORIES
from scripts.utils.logger import setup_logger


setup_logger(__file__)

# Valid dominant-emotion labels (eight emotions plus the neutral fallback).
VALID_DOMINANT = set(EMOTION_CATEGORIES) | {"neutral"}

RESULTS: list[dict] = []


def record(check: str, status: str, detail: str = "") -> None:
    """
    Append one check result and log it.

    Args:
        check: Check name.
        status: One of PASS, FAIL, WARN, SKIP.
        detail: Optional human-readable detail.

    Returns:
        None.
    """
    RESULTS.append({"check": check, "status": status, "detail": detail})
    logger.info(f"[{status:4}] {check}" + (f" -- {detail}" if detail else ""))


def _load(name: str) -> pd.DataFrame | None:
    """
    Load an artifact CSV if present, else return None.

    Args:
        name: Artifact file name under the V2 artifact directory.

    Returns:
        DataFrame when the file exists, otherwise None.
    """
    path = CONFIG.artifact_dir / name
    if not path.exists():
        return None
    return pd.read_csv(path)


def check_phase1() -> None:
    """Validate Phase 1 community detection artifacts."""
    communities = _load(CONFIG.f_communities)
    assignment = _load(CONFIG.f_channel_community)

    if communities is None or assignment is None:
        record("phase1 artifacts present", "SKIP", "communities/channel_community missing")
        return

    # Community ids are unique.
    dup = communities["id"].duplicated().sum()
    record("phase1 community ids unique", "PASS" if dup == 0 else "FAIL",
           f"{dup} duplicates")

    # Sizes reported on Community match the per-community assignment counts.
    actual_sizes = assignment.groupby("community_id").size()
    reported = communities.set_index("id")["size"]
    aligned = reported.reindex(actual_sizes.index)
    size_match = bool((aligned == actual_sizes).all())
    record("phase1 community sizes match assignment", "PASS" if size_match else "FAIL")

    # Every channel is assigned to exactly one community.
    multi = assignment["channel_id"].duplicated().sum()
    record("phase1 each channel assigned once", "PASS" if multi == 0 else "FAIL",
           f"{multi} channels assigned more than once")

    # Modularity is within the theoretical range.
    mod = communities["modularity"].dropna()
    mod_ok = bool(((mod >= -1.0) & (mod <= 1.0)).all())
    record("phase1 modularity in [-1, 1]", "PASS" if mod_ok else "FAIL")

    # No null channel or community ids.
    nulls = assignment[["channel_id", "community_id"]].isnull().any().any()
    record("phase1 no null assignment ids", "PASS" if not nulls else "FAIL")


def check_phase2() -> None:
    """Validate Phase 2 topic modeling artifacts."""
    topics = _load(CONFIG.f_topics)
    message_topics = _load(CONFIG.f_message_topics)
    community_topics = _load(CONFIG.f_community_topics)

    if topics is None or message_topics is None:
        record("phase2 artifacts present", "SKIP", "topics/message_topics missing")
        return

    # Topic ids unique.
    dup = topics["id"].duplicated().sum()
    record("phase2 topic ids unique", "PASS" if dup == 0 else "FAIL", f"{dup} duplicates")

    # Probabilities within [0, 1].
    prob = message_topics["probability"].dropna()
    prob_ok = bool(((prob >= 0.0) & (prob <= 1.0)).all())
    record("phase2 probability in [0, 1]", "PASS" if prob_ok else "FAIL")

    # Ranks are positive integers.
    rank_ok = bool((message_topics["rank"] >= 1).all())
    record("phase2 rank >= 1", "PASS" if rank_ok else "FAIL")

    # Assigned topic ids exist in the topic table.
    unknown = set(message_topics["topic_id"]) - set(topics["id"])
    record("phase2 assigned topics exist", "PASS" if not unknown else "FAIL",
           f"unknown topic ids: {sorted(unknown)[:5]}")

    # Embeddings matrix aligns with its index and with the assignments.
    emb_path = CONFIG.artifact_dir / CONFIG.f_message_embeddings
    idx = _load(CONFIG.f_embeddings_index)
    if emb_path.exists() and idx is not None:
        emb = np.load(emb_path, mmap_mode="r")
        align = emb.shape[0] == len(idx) == len(message_topics)
        record("phase2 embeddings align with assignments",
               "PASS" if align else "FAIL",
               f"emb={emb.shape[0]} idx={len(idx)} assign={len(message_topics)}")
    else:
        record("phase2 embeddings present", "SKIP", "embeddings npy/index missing")

    # Community topic shares within (0, 1] and noise excluded.
    if community_topics is not None and not community_topics.empty:
        share = community_topics["share"]
        share_ok = bool(((share > 0.0) & (share <= 1.0)).all())
        record("phase2 community topic share in (0, 1]", "PASS" if share_ok else "FAIL")
        noise = (community_topics["topic_id"] == CONFIG.noise_topic_id).sum()
        record("phase2 noise topic excluded from dominance",
               "PASS" if noise == 0 else "WARN", f"{noise} noise rows")
    else:
        record("phase2 community topics present", "SKIP", "community_topics missing/empty")


def check_phase3() -> None:
    """Validate Phase 3 message similarity artifacts."""
    sim = _load(CONFIG.f_message_similarity)
    if sim is None:
        record("phase3 artifacts present", "SKIP", "message_similarity missing")
        return

    if sim.empty:
        record("phase3 similarity edges present", "WARN", "no edges above threshold")
        return

    # Cosine similarity respects the configured threshold and upper bound.
    cos = sim["cosine_similarity"]
    cos_ok = bool(((cos >= CONFIG.similarity_threshold - 1e-6) & (cos <= 1.0 + 1e-6)).all())
    record("phase3 cosine in [threshold, 1]", "PASS" if cos_ok else "FAIL",
           f"min={cos.min():.4f} max={cos.max():.4f}")

    # Rank within [1, top_k].
    rank_ok = bool(((sim["rank"] >= 1) & (sim["rank"] <= CONFIG.similarity_top_k)).all())
    record("phase3 rank in [1, top_k]", "PASS" if rank_ok else "FAIL")

    # No self-similarity edges.
    self_loops = (sim["source_message_id"] == sim["target_message_id"]).sum()
    record("phase3 no self-similarity", "PASS" if self_loops == 0 else "FAIL",
           f"{self_loops} self edges")

    # At most top_k neighbours per source message.
    over = (sim.groupby("source_message_id").size() > CONFIG.similarity_top_k).sum()
    record("phase3 <= top_k per source", "PASS" if over == 0 else "FAIL",
           f"{over} sources exceed top_k")


def check_phase4() -> None:
    """Validate Phase 4 emotion analysis artifacts."""
    emotions = _load(CONFIG.f_message_emotions)
    if emotions is None:
        record("phase4 artifacts present", "SKIP", "message_emotions missing")
        return

    score_cols = [c for c in emotions.columns if c.endswith("_score")]

    # All scores within [0, 1].
    in_range = bool(
        ((emotions[score_cols] >= 0.0) & (emotions[score_cols] <= 1.0)).all().all()
    )
    record("phase4 scores in [0, 1]", "PASS" if in_range else "FAIL")

    # Dominant emotion labels are valid.
    bad = set(emotions["dominant_emotion"].unique()) - VALID_DOMINANT
    record("phase4 dominant_emotion valid", "PASS" if not bad else "FAIL",
           f"unexpected labels: {bad}")

    # No null message ids.
    nulls = emotions["message_id"].isnull().sum()
    record("phase4 no null message ids", "PASS" if nulls == 0 else "FAIL")

    # Coverage against the source message count.
    raw = pd.read_csv(CONFIG.raw_csv, usecols=["message_id"])
    missing = set(raw["message_id"]) - set(emotions["message_id"])
    record("phase4 all messages scored", "PASS" if not missing else "WARN",
           f"{len(missing)} messages unscored")


def main() -> None:
    """
    Run every phase check and print a status summary.

    Args:
        None.

    Returns:
        None.
    """
    logger.info(f"Running V2 analysis checks against {CONFIG.artifact_dir}")

    check_phase1()
    check_phase2()
    check_phase3()
    check_phase4()

    summary = pd.DataFrame(RESULTS)["status"].value_counts().to_dict()
    logger.info(f"CHECK SUMMARY: {summary}")

    fails = [r for r in RESULTS if r["status"] == "FAIL"]
    if fails:
        logger.error(f"{len(fails)} checks FAILED")
        for r in fails:
            logger.error(f"  {r['check']}: {r['detail']}")


if __name__ == "__main__":
    main()

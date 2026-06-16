"""Phase 4 — Emotion Analysis.

Score each message against the Portuguese NRC Emotion Lexicon and assign a
dominant emotion. Scores are written as message properties to enrich existing
``(:Message)`` nodes.

Inputs:
    data/aletheia_clean_pt.csv      (message text)
    Portuguese-NRC-EmoLex.txt       (via scripts.analysis.lexicon)

Output (neo4j/import/aletheia_pt_v2/):
    message_emotions.csv    message_id, <emotion>_score x8,
                            positive_score, negative_score, dominant_emotion

This phase is pure-python (no embedding model), so it runs quickly over the full
dataset. Scores are proportions of emotion-bearing tokens in the message.
"""
import numpy as np
import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG, EMOTION_CATEGORIES, POLARITY_CATEGORIES
from scripts.analysis.io_utils import write_artifact
from scripts.analysis.lexicon import load_nrc_lexicon, tokenize
from scripts.utils.logger import setup_logger


setup_logger(__file__)

# Output score column names derived from the emotion and polarity categories.
EMOTION_SCORE_COLUMNS = [f"{e}_score" for e in EMOTION_CATEGORIES]
POLARITY_SCORE_COLUMNS = [f"{p}_score" for p in POLARITY_CATEGORIES]


def score_message(tokens: list[str], lexicon: dict[str, dict[str, int]]) -> dict:
    """
    Compute emotion and polarity scores for a single tokenized message.

    Emotion scores are the proportion of emotion-bearing tokens carrying that
    emotion; polarity scores are the proportion of polarity-bearing tokens
    carrying that polarity. The two groups are normalized independently because a
    token may carry polarity without any of the eight emotions (and vice versa),
    so sharing one denominator can push polarity scores above 1. The dominant
    emotion is the argmax over the eight emotion counts; messages with no
    emotional tokens are labelled 'neutral'.

    Args:
        tokens: Normalized message tokens.
        lexicon: NRC lookup from word to emotion/polarity flags.

    Returns:
        Dict of score columns plus dominant_emotion.
    """
    counts = {c: 0 for c in EMOTION_CATEGORIES + POLARITY_CATEGORIES}
    matched_emotion = 0
    matched_polarity = 0

    for token in tokens:
        flags = lexicon.get(token)
        if not flags:
            continue
        # Track emotion- and polarity-bearing tokens separately.
        if any(flags[e] for e in EMOTION_CATEGORIES):
            matched_emotion += 1
        if any(flags[p] for p in POLARITY_CATEGORIES):
            matched_polarity += 1
        for category in counts:
            counts[category] += flags[category]

    # Normalize each category group by its own matched-token count.
    emotion_denom = matched_emotion if matched_emotion > 0 else 1
    polarity_denom = matched_polarity if matched_polarity > 0 else 1
    scores = {f"{e}_score": round(counts[e] / emotion_denom, 6) for e in EMOTION_CATEGORIES}
    scores.update({f"{p}_score": round(counts[p] / polarity_denom, 6) for p in POLARITY_CATEGORIES})

    # Dominant emotion from the eight emotion counts (excluding polarity).
    emotion_counts = {e: counts[e] for e in EMOTION_CATEGORIES}
    if matched_emotion == 0 or max(emotion_counts.values()) == 0:
        scores["dominant_emotion"] = "neutral"
    else:
        scores["dominant_emotion"] = max(emotion_counts, key=emotion_counts.get)

    return scores


def build_emotion_records(lexicon: dict[str, dict[str, int]]) -> pd.DataFrame:
    """
    Score every message in the dataset against the lexicon.

    Args:
        lexicon: NRC lookup from word to emotion/polarity flags.

    Returns:
        DataFrame with message_id, all score columns, and dominant_emotion.
    """
    logger.info(f"Loading messages: {CONFIG.raw_csv}")
    df = pd.read_csv(CONFIG.raw_csv, usecols=["message_id", "text_clean"])
    df["text_clean"] = df["text_clean"].fillna("")

    logger.info(f"Scoring {len(df)} messages against the NRC lexicon.")
    scored = [
        {"message_id": mid, **score_message(tokenize(text), lexicon)}
        for mid, text in zip(df["message_id"], df["text_clean"])
    ]

    columns = (
        ["message_id"]
        + EMOTION_SCORE_COLUMNS
        + POLARITY_SCORE_COLUMNS
        + ["dominant_emotion"]
    )
    return pd.DataFrame(scored, columns=columns)


def main() -> None:
    """
    Run Phase 4 and write the message emotion artifact.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting Phase 4 — emotion analysis.")

    lexicon = load_nrc_lexicon()
    emotions = build_emotion_records(lexicon)
    write_artifact(emotions, CONFIG.f_message_emotions)

    # Report the dominant-emotion distribution for a quick sanity check.
    distribution = emotions["dominant_emotion"].value_counts().to_dict()
    logger.info(f"Phase 4 complete. Dominant emotion distribution: {distribution}")


if __name__ == "__main__":
    main()

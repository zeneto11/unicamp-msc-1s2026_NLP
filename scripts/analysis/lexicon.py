"""NRC Emotion Lexicon loader for the Portuguese column.

Parses ``Portuguese-NRC-EmoLex.txt`` (tab-separated, one row per English word
with its Portuguese translation and ten binary emotion/polarity flags) into a
lookup from normalized Portuguese word to its emotion vector.
"""
import re

import pandas as pd
from loguru import logger

from scripts.analysis.config import CONFIG, EMOTION_CATEGORIES, POLARITY_CATEGORIES


# All ten lexicon flag columns (eight emotions plus two polarity columns).
LEXICON_FLAG_COLUMNS = EMOTION_CATEGORIES + POLARITY_CATEGORIES

# Token pattern: unicode word characters with an optional leading hashtag.
TOKEN_PATTERN = re.compile(r"#?\w+", re.UNICODE)


def normalize_word(word: str) -> str:
    """
    Apply light normalization to a single token for lexicon matching.

    Lowercases, strips surrounding whitespace, and drops a leading hashtag so
    that '#vacina' matches the lexicon entry 'vacina'.

    Args:
        word: Raw token.

    Returns:
        Normalized token.
    """
    word = word.strip().lower()
    if word.startswith("#"):
        word = word[1:]
    return word


def load_nrc_lexicon() -> dict[str, dict[str, int]]:
    """
    Load the Portuguese NRC lexicon into a per-word emotion lookup.

    Multiple English senses can map to the same Portuguese word; flags are
    aggregated with a logical OR (max) so a word carries an emotion if any sense
    does.

    Args:
        None.

    Returns:
        Mapping of normalized Portuguese word to {emotion/polarity: 0/1}.
    """
    logger.info(f"Loading NRC lexicon: {CONFIG.lexicon_path}")
    df = pd.read_csv(CONFIG.lexicon_path, sep="\t")

    # The Portuguese translation column is the matching key.
    word_col = "Portuguese Word"
    df[word_col] = df[word_col].astype(str).map(normalize_word)

    # Coerce flag columns to integers and aggregate duplicate words by max.
    for col in LEXICON_FLAG_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    aggregated = (
        df.groupby(word_col)[LEXICON_FLAG_COLUMNS].max()
    )

    # Drop empty keys produced by missing translations.
    aggregated = aggregated[aggregated.index.str.len() > 0]

    lexicon = aggregated.to_dict(orient="index")
    logger.info(f"Loaded lexicon entries={len(lexicon)}")
    return lexicon


def tokenize(text: str) -> list[str]:
    """
    Tokenize message text into normalized tokens for lexicon lookup.

    Args:
        text: Raw message text.

    Returns:
        List of normalized tokens.
    """
    if not isinstance(text, str):
        return []
    return [normalize_word(t) for t in TOKEN_PATTERN.findall(text)]

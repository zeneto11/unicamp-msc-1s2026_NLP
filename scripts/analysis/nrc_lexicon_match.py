"""NRC Lexicon Match Analysis.

Calculate percentage of NRC lexicon words found in the Aletheia clean dataset.

Inputs:
    data/Portuguese-NRC-EmoLex.txt
    data/aletheia_clean_pt.csv

Output:
    Console report with matching statistics.
"""
import pandas as pd
from pathlib import Path
from loguru import logger
import re
from collections import Counter

from scripts.utils.logger import setup_logger

setup_logger(__file__)


def load_nrc_lexicon(nrc_path: str) -> set[str]:
    """
    Load Portuguese words from NRC lexicon.

    Args:
        nrc_path: Path to Portuguese-NRC-EmoLex.txt

    Returns:
        Set of Portuguese words (lowercased).
    """
    logger.info(f"Loading NRC lexicon from {nrc_path}")
    df = pd.read_csv(nrc_path, sep="\t")

    # Extract Portuguese words (last column)
    portuguese_words = set(
        df["Portuguese Word"]
        .dropna()
        .str.strip()
        .str.lower()
        .unique()
    )

    logger.info(f"NRC lexicon contains {len(portuguese_words)} unique Portuguese words")
    return portuguese_words


def load_aletheia_text(aletheia_path: str) -> str:
    """
    Load and concatenate all text from Aletheia clean dataset.

    Args:
        aletheia_path: Path to aletheia_clean_pt.csv

    Returns:
        Concatenated text from all messages.
    """
    logger.info(f"Loading Aletheia dataset from {aletheia_path}")
    df = pd.read_csv(aletheia_path, usecols=["text_clean"])

    # Concatenate all text
    all_text = " ".join(
        df["text_clean"]
        .fillna("")
        .astype(str)
    )

    logger.info(f"Loaded {len(df)} messages from Aletheia")
    return all_text


def tokenize_text(text: str) -> list[str]:
    """
    Tokenize text into words (letters only, lowercase).

    Args:
        text: Raw text to tokenize

    Returns:
        List of lowercased word tokens.
    """
    # Keep only letters and spaces, convert to lowercase
    text = re.sub(r"[^a-záéíóúâêôãõç\s]", "", text.lower())

    # Split by whitespace and remove empty strings
    tokens = [word.strip() for word in text.split() if word.strip()]

    return tokens


def calculate_matches(
    nrc_words: set[str],
    aletheia_tokens: list[str]
) -> dict:
    """
    Calculate matching statistics.

    Args:
        nrc_words: Set of NRC Portuguese words
        aletheia_tokens: List of tokens from Aletheia

    Returns:
        Dictionary with statistics.
    """
    logger.info(f"Analyzing {len(aletheia_tokens)} tokens from Aletheia")

    # Count unique words in Aletheia
    aletheia_unique = set(aletheia_tokens)

    # Find matches
    matched_words = nrc_words & aletheia_unique

    # Count occurrences
    token_counter = Counter(aletheia_tokens)
    matched_occurrences = sum(
        token_counter[word]
        for word in matched_words
    )

    # Calculate percentages
    pct_nrc_covered = (len(matched_words) / len(nrc_words)) * 100
    pct_aletheia_coverage = (len(matched_words) / len(aletheia_unique)) * 100
    pct_tokens_matched = (matched_occurrences / len(aletheia_tokens)) * 100

    return {
        "nrc_total_words": len(nrc_words),
        "aletheia_unique_words": len(aletheia_unique),
        "aletheia_total_tokens": len(aletheia_tokens),
        "matched_words": len(matched_words),
        "matched_occurrences": matched_occurrences,
        "pct_nrc_covered": pct_nrc_covered,
        "pct_aletheia_coverage": pct_aletheia_coverage,
        "pct_tokens_matched": pct_tokens_matched,
    }


def print_results(stats: dict) -> None:
    """
    Print formatted results.

    Args:
        stats: Dictionary with statistics

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("NRC LEXICON MATCH ANALYSIS")
    print("="*60)
    print(f"\nNRC Lexicon:")
    print(f"  Total unique words: {stats['nrc_total_words']:,}")

    print(f"\nAletheia Dataset:")
    print(f"  Unique words: {stats['aletheia_unique_words']:,}")
    print(f"  Total tokens: {stats['aletheia_total_tokens']:,}")

    print(f"\nMatches:")
    print(f"  Matched words: {stats['matched_words']:,}")
    print(f"  Matched token occurrences: {stats['matched_occurrences']:,}")

    print(f"\nMatch Percentages:")
    print(f"  % of NRC words found in Aletheia: {stats['pct_nrc_covered']:.2f}%")
    print(f"  % of Aletheia words in NRC: {stats['pct_aletheia_coverage']:.2f}%")
    print(f"  % of Aletheia tokens matched: {stats['pct_tokens_matched']:.2f}%")
    print("\n" + "="*60 + "\n")


def main() -> None:
    """
    Run NRC lexicon match analysis.

    Args:
        None.

    Returns:
        None.
    """
    logger.info("Starting NRC lexicon match analysis")

    # Paths
    nrc_path = Path("data/Portuguese-NRC-EmoLex.txt")
    aletheia_path = Path("data/aletheia_clean_pt.csv")

    # Load data
    nrc_words = load_nrc_lexicon(nrc_path)
    aletheia_text = load_aletheia_text(aletheia_path)

    # Tokenize
    logger.info("Tokenizing Aletheia text")
    aletheia_tokens = tokenize_text(aletheia_text)

    # Calculate matches
    stats = calculate_matches(nrc_words, aletheia_tokens)

    # Print results
    print_results(stats)

    logger.info("NRC lexicon match analysis complete")


if __name__ == "__main__":
    main()
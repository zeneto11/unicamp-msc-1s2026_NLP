"""Shared text-feature constants for keyword and topic extraction.

Both Phase 1 (TF-IDF community keywords) and Phase 2 (BERTopic c-TF-IDF topic
labels) need the same Portuguese stopword list and the same token filter. The
token filter keeps only alphabetic tokens (incl. Portuguese accents, 2+ chars),
which drops pure-digit and digit-glued fragments — e.g. binary-corruption
remnants like ``5m5`` / ``youtube5`` that the canonical text cleaning cannot
remove because they are printable ASCII. Keeping these in one place ensures the
fix applies identically in both layers.
"""

# A compact Portuguese stopword list. Hash/URL noise is already stripped upstream
# in the canonical text_clean column (scripts/dataset/cleaning.py); these are
# genuine high-frequency words that otherwise dominate keyword/topic labels.
PT_STOPWORDS = [
    "a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "um", "uma", "uns", "umas", "para", "por", "com", "sem",
    "que", "se", "as", "os", "ao", "aos", "à", "às", "mais", "mas", "como",
    "ou", "já", "não", "sim", "também", "muito", "muita", "ser", "está",
    "este", "esta", "isso", "isto", "esse", "essa", "the", "to",
    "br", "me", "eu", "você", "ele", "ela", "nós",
    "eles", "elas", "foi", "são", "tem", "vai", "está", "pra", "pro", "lá",
    "aqui", "todo", "toda", "todos", "todas", "seu", "sua", "seus", "suas",
    # Common non-Portuguese function words (Italian/Spanish/English). They are
    # rare in this PT corpus, so c-TF-IDF over-weights the few that leak from
    # merged outliers and surfaces them as spurious topic labels. None of these
    # are valid unaccented Portuguese words (PT uses não/de/o/a, not non/di/la).
    "non", "che", "di", "la", "el", "il", "le", "the", "of", "and", "for",
]

# Keep only alphabetic tokens (incl. Portuguese accents), 2+ chars. Drops
# pure-digit and digit-prefixed/suffixed fragments that carry no descriptive
# value. Compatible with both scikit-learn's TfidfVectorizer and BERTopic's
# CountVectorizer (both accept a `token_pattern`).
KEYWORD_TOKEN_PATTERN = r"(?u)\b[^\W\d_][^\W\d_]+\b"

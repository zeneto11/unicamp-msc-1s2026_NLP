from pathlib import Path
from dataclasses import dataclass


# The eight NRC emotion categories used across Phase 4.
EMOTION_CATEGORIES = [
    "anger",
    "anticipation",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "surprise",
    "trust",
]

# Polarity columns kept alongside the emotion categories.
POLARITY_CATEGORIES = [
    "positive",
    "negative",
]


@dataclass(frozen=True)
class AnalysisConfig:
    """
    Store immutable paths and parameters for the V2 analysis pipeline.

    The analysis phases consume V1 outputs (the message CSV and the channel
    interaction graph) and write enrichment artifacts that the V2 graph loaders
    ingest. Connection settings live in scripts.graph.v2.config; this config only
    covers the compute side (paths, models, thresholds).

    Args:
        None.

    Returns:
        AnalysisConfig instance with default analysis configuration values.
    """
    # Name used for the V2 graph-specific artifact directory.
    graph_name: str = "aletheia_pt_v2"

    # Resolve the repository root from this configuration file.
    project_root: Path = Path(__file__).resolve().parents[2]

    # Inputs: the cleaned source CSV and the V1 import directory.
    raw_csv: Path = project_root / "data" / "aletheia_clean_pt.csv"
    import_root: Path = project_root / "neo4j" / "import"
    v1_import_dir: Path = import_root / "aletheia_pt_v1"

    # Outputs: V2 artifacts written here are loaded into Neo4j via file:/// URLs.
    artifact_dir: Path = import_root / "aletheia_pt_v2"

    # Phase 4 lexicon (NRC Emotion Lexicon, Portuguese column).
    lexicon_path: Path = project_root / "data" / "Portuguese-NRC-EmoLex.txt"

    # Shared reproducibility seed.
    random_seed: int = 42

    # ----- Phase 1: community detection -----
    # Algorithm preference order; the first importable one is used.
    community_algorithms: tuple[str, ...] = ("leiden", "louvain")
    # Edge weight property projected from INTERACTS_WITH.
    interaction_weight_property: str = "interaction_weight"
    # Number of descriptive keywords generated per community.
    descriptive_keywords_top_n: int = 8

    # ----- Phase 2: topic modeling -----
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # Light preprocessing threshold; messages below this are dropped from modeling.
    min_words: int = 5
    # A topic is "dominant" in a community above this share of its modeled messages.
    topic_dominance_min_share: float = 0.05
    # BERTopic noise/outlier topic id.
    noise_topic_id: int = -1
    # HDBSCAN min cluster size (BERTopic min_topic_size). Larger -> fewer, denser
    # topics; the default of 10 over-fragments and inflates the noise bucket.
    min_topic_size: int = 15
    # Reassign noise (-1) messages to their nearest topic by embedding proximity,
    # then refresh topic representations. Fixes the ~48% outlier rate that is a
    # known artifact of default HDBSCAN on short social text.
    reduce_outliers: bool = True
    outlier_reduction_strategy: str = "embeddings"
    # Minimum embedding cosine to a topic for an outlier to be reassigned. Above
    # 0 keeps genuinely un-clusterable messages in the noise bucket instead of
    # forcing every message into a topic (which would yield mostly low-confidence
    # assignments).
    outlier_reduction_threshold: float = 0.50
    # Drop non-target-language messages before modeling (catches contamination
    # the upstream `language` column mislabels). Requires langdetect; skipped with
    # a warning if it is not installed.
    language_filter: bool = True
    keep_language: str = "pt"

    # ----- Phase 3: message similarity -----
    similarity_threshold: float = 0.80
    similarity_top_k: int = 5
    similarity_same_topic_only: bool = False
    similarity_exclude_same_message: bool = True
    similarity_method: str = "faiss_cosine_knn"

    # ----- Phase 4: emotion analysis -----
    emotion_categories: tuple[str, ...] = tuple(EMOTION_CATEGORIES)
    polarity_categories: tuple[str, ...] = tuple(POLARITY_CATEGORIES)

    # ----- Artifact file names (written under artifact_dir) -----
    f_communities: str = "communities.csv"
    f_channel_community: str = "channel_community.csv"
    f_topics: str = "topics.csv"
    f_message_topics: str = "message_topics.csv"
    f_community_topics: str = "community_topics.csv"
    f_message_similarity: str = "message_similarity.csv"
    f_message_emotions: str = "message_emotions.csv"
    f_message_embeddings: str = "message_embeddings.npy"
    f_embeddings_index: str = "message_embeddings_index.csv"

    def ensure_artifact_dir(self) -> Path:
        """
        Create the V2 artifact directory when it does not exist.

        Args:
            None.

        Returns:
            Path to the V2 artifact directory.
        """
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        return self.artifact_dir


# Instantiate the shared analysis configuration.
CONFIG = AnalysisConfig()

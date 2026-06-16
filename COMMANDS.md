# Commands

## Dataset

```bash
# Clean the raw dataset → produces data/aletheia_clean_pt.csv
python -m scripts.dataset.cleaning

# Full dataset report (all channels, all languages)
python -m scripts.dataset.report_full

# Portuguese-only channel report
python -m scripts.dataset.report_pt
```

## Graph V1

```bash
# Prepare import CSVs: node files (channels, users, messages) + edge files
python -m scripts.graph.v1.prepare_imports

# Load the V1 structural graph into Neo4j
python -m scripts.graph.v1.load_graph
```

## Analysis — V2 Enrichment Phases

```bash
# Phase 1 — community detection on the channel interaction graph (Leiden/Louvain)
python -m scripts.analysis.phase1_community_detection

# Phase 2 — topic modeling via BERTopic + multilingual sentence embeddings (slow, GPU helps)
python -m scripts.analysis.phase2_topic_modeling

# Phase 3 — message similarity via FAISS cosine kNN (reuses Phase 2 embeddings)
python -m scripts.analysis.phase3_message_similarity

# Phase 4 — emotion scoring via Portuguese NRC lexicon (fast, independent of phases 1–3)
python -m scripts.analysis.phase4_emotion_analysis

# Validate all phase artifacts before loading into Neo4j
python -m scripts.analysis.checks
```

## Graph V2

```bash
# Load enrichment artifacts into Neo4j (skips any phase whose artifacts are missing)
python -m scripts.graph.v2.load_graph
```

## Report — Graph V2 Analytical Report

```bash
# Build final report from the V1/V2 artifacts
python -m scripts.report.generate
```

## Neo4j Management

```bash
# Wipe all graph data while keeping the Neo4j container running
python -m scripts.graph.clear_data

# Hard reset: tear down Docker, delete Neo4j state, restart, and wait for readiness
python -m scripts.graph.reset_graph
```

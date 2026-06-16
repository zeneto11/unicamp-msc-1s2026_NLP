# Aletheia NLP — Portuguese Telegram Misinformation Analysis

Analysis of the **Aletheia-PT** dataset: ~32k messages from 109 Telegram channels flagged as misinformation sources in Portuguese. The pipeline builds a structural knowledge graph in Neo4j and progressively enriches it with NLP layers.

## Dataset

| Stat     | Value |
| -------- | ----- |
| Messages | ~32k  |
| Channels | 109   |
| Users    | 5,854 |
| Forwards | ~5k   |
| Replies  | ~8k   |

Raw data lives in `data/`. The cleaning step produces `aletheia_clean_pt.csv`, the canonical input for all downstream scripts.

## Pipeline

```
dataset/cleaning  →  graph/v1  →  analysis (phases 1–4)  →  graph/v2
```

| Step         | What it does                                                             |
| ------------ | ------------------------------------------------------------------------ |
| **Dataset**  | Clean raw CSV, generate reports                                          |
| **Graph V1** | Build structural graph: channels, users, messages, interaction edges     |
| **Analysis** | Community detection, topic modeling, message similarity, emotion scoring |
| **Graph V2** | Load enrichment artifacts back into Neo4j                                |

## Folder Structure

| Folder              | Contents                                                  |
| ------------------- | --------------------------------------------------------- |
| `data/`             | Raw and cleaned CSV datasets, NRC Emotion Lexicon         |
| `docs/`             | Graph schema documentation (`graph_v1.md`, `graph_v2.md`) |
| `neo4j/`            | Docker-managed Neo4j data, logs, and import files         |
| `notebooks/`        | Exploratory analysis notebooks                            |
| `reports/`          | Generated dataset reports and figures                     |
| `scripts/analysis/` | NLP phases: communities, topics, similarity, emotions     |
| `scripts/dataset/`  | Raw dataset cleaning and reporting                        |
| `scripts/graph/v1/` | Build import CSVs and load the V1 structural graph        |
| `scripts/graph/v2/` | Load V2 enrichment artifacts into Neo4j                   |
| `scripts/report/`   | Final report markdown generation                          |
| `scripts/utils/`    | Shared logger setup                                       |

## Graph V1 — Structural Layer

Nodes: **Channel**, **User**, **Message**

Key relationships: `POSTED`, `IN_CHANNEL`, `REPLIES_TO`, `FORWARDED_FROM`, `ACTIVE_IN`, `INTERACTS_WITH` (channel-to-channel, weighted by shared users, forwards, and replies).

## Graph V2 — Enrichment Layers

Built on top of V1 without rebuilding any existing nodes or relationships.

| Layer                                                                                              | Added by |
| -------------------------------------------------------------------------------------------------- | -------- |
| `(:Community)` + `(:Channel)-[:BELONGS_TO]->(:Community)`                                          | Phase 1  |
| `(:Topic)` + `(:Message)-[:BELONGS_TO_TOPIC]->(:Topic)` + `(:Community)-[:DOMINATED_BY]->(:Topic)` | Phase 2  |
| `(:Message)-[:SIMILAR_TO]->(:Message)`                                                             | Phase 3  |
| Emotion scores on `(:Message)`                                                                     | Phase 4  |

## Infrastructure

Neo4j runs in Docker (`docker-compose.yml`).  
Use `scripts/graph/reset_graph.py` to recreate the environment from scratch, or `scripts/graph/clear_data.py` to wipe only the graph data while keeping the container running.

**Environment Setup**

This project uses **Poetry (v2.2.1)** for dependency management.

```bash
# Install dependencies and create virtual environment
poetry install

# Activate the virtual environment
poetry shell
```

See [**COMMANDS.md**](COMMANDS.md) for all runnable commands.

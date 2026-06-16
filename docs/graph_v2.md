# Graph V2 — Communities, Topics & Semantic Layer

Reference: `graph_v1.md`

## Goal

V2 extends Graph V1.

V1 models:

- actors
- communication
- diffusion
- reply structure

V2 adds:

- community structure
- topic structure
- narrative similarity
- community-level analysis

V2 does not rebuild existing V1 nodes or relationships.

It enriches the graph with new layers derived from V1.

---

# Pipeline Overview

```text
Graph V1
    ↓
Community Detection
    ↓
Topic Modeling
    ↓
Semantic Enrichment
    ↓
Similarity Analysis
    ↓
Statistical Analysis
    ↓
Graph V2
```

---

# New NODE TYPES

## 1. Community

```yaml
label: Community

id: community_id

properties: size
  density
  modularity
  algorithm
```

Description:

Represents a detected community of channels and users derived from the V1 interaction graph.

---

## 2. Topic

```yaml
label: Topic

id: topic_id

properties: label
  keywords
  coherence_score
  message_count
  embedding
```

Description:

Represents a latent topic extracted from messages belonging to a community.

---

# New RELATION TYPES

## 1. Community Membership

```yaml
(Channel)-[:BELONGS_TO]->(Community)
(User)-[:BELONGS_TO]->(Community)
(Message)-[:BELONGS_TO]->(Community)
```

Description:

Assigns a entity to its detected community.

---

## 2. Topic Assignment

```yaml
(Message)-[:BELONGS_TO_TOPIC]->(Topic)
```

Properties:

```yaml
probability
rank
```

Description:

Links messages to inferred topics.

---

## 3. Community Topic Dominance

```yaml
(Community)-[:DOMINATED_BY]->(Topic)
```

Properties:

```yaml
share
message_count
```

Description:

Represents dominant topics inside a community.

---

## 4. Message Similarity

```yaml
(Message)-[:SIMILAR_TO]->(Message)
```

Properties:

```yaml
cosine_similarity
```

Description:

Represents semantic similarity between messages.

# Analysis Phases

## Phase 1 — Community Detection

Detect structural communities of channels using the V1 channel interaction layer.

This phase identifies groups of channels that are closely connected through interaction patterns.

### Input

Use the V1 channel interaction graph:

```text
(Channel)-[:INTERACTS_WITH]->(Channel)
```

The `INTERACTS_WITH` relation summarizes structural signals from V1, including:

- shared user activity
- forwarding patterns
- reply patterns
- optional engagement-based interaction strength

### Algorithms

```text
Leiden (preferred)
Louvain
```

### Community Assignment

Each channel receives a community assignment.

```text
(Channel)-[:BELONGS_TO]->(Community)
```

Users and messages are not directly clustered in this phase.

They can be associated with communities indirectly:

```text
User → ACTIVE_IN → Channel → Community

Message → IN_CHANNEL → Channel → Community
```

### Descriptive Keywords

After communities are detected, generate descriptive keywords for each community.

These keywords are based on the message content from the channels inside each community.

Purpose:

- provide a readable summary of each community
- help inspect whether communities are coherent
- support early interpretation before topic modeling
- provide context for the next phase

These are descriptive labels only.

They should not be treated as formal topics.

Formal topic extraction happens in Phase 2.

Suggested output:

```yaml
community_name
descriptive_keywords
keyword_method
```

Example:

```yaml
community_name: "vacinas · eleições · fraude · liberdade"

descriptive_keywords:
  - vacinas
  - eleições
  - fraude
  - liberdade

keyword_method: "descriptive_keywords"
```

---

### Output

This phase produces:

```yaml
community_id
community_size
algorithm
modularity_score
community_name
descriptive_keywords
```

Graph additions prepared by this phase:

```text
(:Community)

(:Channel)-[:BELONGS_TO]->(:Community)
```

---

## Phase 2 — Topic Modeling

Extract latent topics from Portuguese Telegram messages.

This phase assigns semantic topics to messages and summarizes topic dominance by community.

### Input

Use messages from V1 with community assignment from Phase 1.

```text
(Message)-[:IN_CHANNEL]->(Channel)-[:BELONGS_TO]->(Community)
```

Required message fields:

```yaml
message_id
text
date
month
channel_id
community_id
is_forwarded
is_reply
views
reactions
forwards
```

### Unit of Analysis

Primary unit:

```text
Message
```

Each message receives a topic assignment.

Community-level topics are created later by aggregation.

### Text Language

Message content is in Portuguese.

Use a multilingual embedding model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Reason:

- supports Portuguese
- fast enough for this dataset
- good for short message similarity
- produces compact embeddings

Save embeddings after generation.

```text
message_id → embedding
```

Embeddings should not be recomputed unless preprocessing changes.

### Topic Model

Preferred method:

```text
BERTopic
```

### Preprocessing

Apply light preprocessing only.

Remove:

- empty messages
- very short messages
- pure URLs
- duplicated boilerplate
- messages without textual content

Keep:

- hashtags
- named entities
- forwarded messages
- reply messages
- emojis if useful for later emotion analysis

Minimum message length:

```yaml
min_words: 5
```

### Topic Assignment

Each modeled message receives:

```yaml
topic_id
topic_probability
topic_rank
```

Graph relation:

```text
(Message)-[:BELONGS_TO_TOPIC]->(Topic)
```

Relation properties:

```yaml
probability
rank
```

Topic `-1` is treated as noise or outlier.

### Topic Labels

Topic labels are generated from top topic keywords.

Labels should be manually inspected.

Example:

```yaml
topic_id: 12
label: "eleições · fraude · urnas · governo"
keywords:
  - eleições
  - fraude
  - urnas
  - governo
```

### Community Topic Aggregation

After message-level topic assignment, aggregate topics by community.

```text
Community → Messages → Topics
```

Create dominance relation:

```text
(Community)-[:DOMINATED_BY]->(Topic)
```

Properties:

```yaml
share
message_count
```

A topic is dominant when it represents a relevant share of messages in a community.

### Output

This phase produces:

```yaml
topic_id
topic_label
keywords
message_count
topic_embedding
```

Per-message output:

```yaml
message_id
topic_id
topic_probability
topic_rank
```

Per-community output:

```yaml
community_id
topic_id
message_count
topic_share
```

Graph additions prepared by this phase:

```text
(:Topic)

(:Message)-[:BELONGS_TO_TOPIC]->(:Topic)

(:Community)-[:DOMINATED_BY]->(:Topic)
```

---

## Phase 3 — Message Similarity

Create semantic similarity links between messages.

This phase uses the same embeddings generated in Phase 2.

### Input

```yaml
message_id
text
embedding
topic_id
community_id
month
```

### Similarity Method

Use cosine similarity between message embeddings.

```text
message_embedding → cosine similarity → similar messages
```

Preferred embedding source:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Do not compare every message with every other message directly.

Use approximate nearest neighbors.

Suggested method:

```text
FAISS
```

### Filtering

Create similarity links only when:

```yaml
cosine_similarity: >= 0.80
top_k: 5
```

Optional filters:

```yaml
same_topic: true
same_language: true
exclude_same_message: true
```

### Output

Graph relation:

```text
(Message)-[:SIMILAR_TO]->(Message)
```

Relation properties:

```yaml
cosine_similarity
rank
method
embedding_model
```

---

## Phase 4 — Emotion Analysis

Analyze emotional tone in Portuguese Telegram messages.

This phase adds emotion scores to messages and aggregates them by topic, community, and month.

### Input

```yaml
message_id
text
topic_id
community_id
month
is_forwarded
is_reply
```

### Main Lexicon

Use:

```text
NRC Emotion Lexicon
```

on: `Portuguese-NRC-EmoLex.txt`

Emotion categories:

```text
anger
fear
sadness
joy
disgust
trust
anticipation
surprise
```

Also keep polarity when available:

```text
positive
negative
```

### Portuguese Handling

Use the Portuguese version of NRC.

Apply light normalization:

```text
lowercase
remove extra spaces
keep hashtags
keep emojis
lemmatize if useful
```

### Output

Each message receives emotion scores.

```yaml
message_id
anger_score
fear_score
sadness_score
joy_score
disgust_score
trust_score
anticipation_score
surprise_score
positive_score
negative_score
dominant_emotion
```

Graph additions prepared by this phase:

Add emotion properties to messages:

```text
(:Message)
```

Properties:

```yaml
dominant_emotion
anger_score
fear_score
sadness_score
joy_score
disgust_score
trust_score
anticipation_score
surprise_score
positive_score
negative_score
```

## Phase 5 — Statistical Analysis

Status: TO DO
Later Implementation.

Potential analyses:

- Community-level topic differences
- Community-level linguistic differences
- Topic diffusion patterns
- Forwarding behavior by topic
- Entity usage differences across communities
- Temporal narrative shifts
- Community engagement comparisons

Potential methods:

```text
t-test
ANOVA
Linear Mixed Models
Poisson Models
Negative Binomial Models
Survival Analysis
Time Series Analysis
```

---

# Final V2 Topology

```text
(Channel) ─BELONGS_TO─▶ (Community)
                              │
                              ▼
                         DOMINATED_BY
                              │
                              ▼
                           (Topic)

(Message) ─BELONGS_TO_TOPIC─▶ (Topic)

(Message) ─SIMILAR_TO─▶ (Message)
```

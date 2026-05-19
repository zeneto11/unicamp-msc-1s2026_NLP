# Graph V2 — Communities + Topics + Semantic Layer

Reference: **`graph_v1.md`**

V2 extends V1.

Do **not rebuild** nodes and relations from V1.

V2 adds:

- community detection
- topic extraction
- semantic enrichment
- diffusion communities
- narrative analysis

---

# Pipeline

```text
Graph V1
    ↓

Community Detection
    ↓

Community Assignment
    ↓

Topic Modeling per Community
    ↓

Semantic Enrichment
    ↓

Graph V2
```

---

# Step 1 — Community Detection

Input:

```text
Channel
User
Message

POSTED
ACTIVE_IN
REPLIES_TO
FORWARDED_FROM
```

From V1.

---

## Community graph projection

Create projection:

```text
Channel
    +
ACTIVE_IN
    +
FORWARDED_FROM
    +
REPLIES_TO
```

Derived graph:

```text
(Channel)
      |
INTERACTS_WITH
      |
(Channel)
```

Weights:

```yaml
shared_users_weight

forward_weight

reply_weight

engagement_weight
```

Example:

```cypher
(Channel_A)-[:INTERACTS_WITH {
    shared_users:20,
    forwards:55,
    replies:8
}]->(Channel_B)
```

---

## Community algorithms

Run:

```text
Leiden      (preferred)

Louvain     (baseline)

Infomap     (optional)
```

Output:

```yaml
community_id
community_size
density
modularity_score
```

---

# New Node Type

## Community

```yaml
label: Community

id: community_id

properties: size

  density

  modularity

  algorithm

  created_at
```

Example:

```cypher
(:Community {
    community_id:12,
    size:18,
    modularity:0.61
})
```

---

# New Relations

## Channel assignment

```yaml
(Channel)-[:BELONGS_TO]->(Community)
```

Properties:

```yaml
membership_score
```

Example:

```cypher
(Channel_1)-[:BELONGS_TO]->(Community_12)
```

---

## User assignment

Optional:

```yaml
(User)-[:PART_OF]->(Community)
```

Construction:

```python
majority(
ACTIVE_IN channels
)
```

---

# Step 2 — Topic Modeling

Input:

Messages grouped by:

```python
community_id
```

Do NOT run topic modeling globally.

Run:

```text
Community
      ↓
messages
      ↓
topic extraction
```

Recommended:

```text
BERTopic

Top2Vec

LDA (baseline)
```

Preferred:

```text
BERTopic
```

because later similarity edges can reuse embeddings.

---

# New Node Type

## Topic

```yaml
label: Topic

id: topic_id

properties: label

  keywords

  coherence_score

  message_count

  embedding
```

Example:

```cypher
(:Topic {
    topic_id:5,
    label:"vaccines",
    coherence_score:0.74
})
```

---

# New Relations

## Message topic assignment

```yaml
(Message)-[:BELONGS_TO_TOPIC]->(Topic)
```

Properties:

```yaml
probability

rank
```

Example:

```cypher
(Message_100)-[:BELONGS_TO_TOPIC {
    probability:0.88
}]->(Topic_5)
```

---

## Community topic dominance

```yaml
(Community)-[:DOMINATED_BY]->(Topic)
```

Properties:

```yaml
share

message_count
```

Example:

```cypher
(Community_12)-[:DOMINATED_BY {
    share:0.41
}]->(Topic_5)
```

---

# Step 3 — Semantic Layer

Add extracted entities.

---

## Entity node

```yaml
label: Entity

id: entity_id

properties: text

  type

  frequency
```

Types:

```text
PERSON

ORG

LOCATION

URL

HASHTAG

EVENT
```

---

## Relations

Message mentions:

```yaml
(Message)-[:MENTIONS]->(Entity)
```

Community usage:

```yaml
(Community)-[:USES]->(Entity)
```

Topic references:

```yaml
(Topic)-[:REFERENCES]->(Entity)
```

---

# Step 4 — Similarity Layer

Compute embeddings:

Input:

```text
Message.text
```

Recommended:

```text
Sentence-BERT

multilingual-e5

BERTopic embeddings
```

Create:

```yaml
(Message)-[:SIMILAR_TO]->(Message)
```

Properties:

```yaml
cosine_similarity
```

Threshold:

```python
similarity > 0.80
```

Example:

```cypher
(m1)-[:SIMILAR_TO {
    cosine:0.91
}]->(m2)
```

---

# Final V2 topology

```text
                +----------------+
                |   Community    |
                +----------------+
                   ^        |
                   |        |
              BELONGS_TO  DOMINATED_BY
                   |        |
                   |        v

(User)      (Channel) ---> (Topic)
   |             ^             |
   |             |             |
POSTED      IN_CHANNEL     REFERENCES
   |             |             |
   v             |             v

(Message) ----MENTIONS----> (Entity)
     |
     |
SIMILAR_TO
     |
     v

(Message)
```

---

# Suggested config object

```yaml
graph_name: telegram_v2

extends: telegram_v1

new_nodes:
  Community:
    key: community_id

  Topic:
    key: topic_id

  Entity:
    key: entity_id

new_edges:
  BELONGS_TO:
    source: channel_id
    target: community_id

  PART_OF:
    source: user_id
    target: community_id

  BELONGS_TO_TOPIC:
    source: message_id
    target: topic_id

  DOMINATED_BY:
    source: community_id
    target: topic_id

  MENTIONS:
    source: message_id
    target: entity_id

  USES:
    source: community_id
    target: entity_id

  REFERENCES:
    source: topic_id
    target: entity_id

  SIMILAR_TO:
    source: message_id
    target: message_id
    metric: cosine_similarity
```

---

# V1 → V2 progression

```text
V1
Actors + Communication + Diffusion
(User, Channel, Message)

        ↓

Communities

        ↓

Topics

        ↓

Entities

        ↓

Similarity

        ↓

Narratives / Propagation Analysis
```

This keeps V2 as an **extension layer**, not a rewrite of V1.

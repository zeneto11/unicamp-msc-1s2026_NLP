# Aletheia-PT — Graph V2 Analytical Report

_Structural, community, topic, semantic, and emotional analysis of the Portuguese Aletheia Telegram corpus. Generated automatically by `scripts/report/generate.py` from the V1/V2 graph artifacts._

_Generated: 2026-06-16_

---

## 1. Executive Summary

- **Structure (V1).** 477 channels (109 core + external sources) and 5,854 users are linked through 1,154 channel-interaction edges (shared users, forwards, replies).
- **Communities (V2 / Phase 1).** Leiden finds **12 communities** over 463 channels at modularity **0.42** — a clear, well-separated structure.
- **Topics (V2 / Phase 2).** **270 topics** extracted from 29,729 modeled messages; 48.5% fall in the BERTopic noise bucket (`-1`).
- **Semantics (V2 / Phase 3).** **9,044 near-duplicate message pairs** (cosine ≥ 0.80); 56.5% of them link _different_ communities — measurable cross-group narrative reuse.
- **Emotion (V2 / Phase 4).** Dominant tone is **anger, trust, anticipation**; 22.5% of messages carry no lexicon emotion (neutral).
- **Most active community:** `C4` (8,424 messages) — vacina · só · pessoas.

> The graph is highly centralized: a few large channels and one or two communities carry most messages, topics repeat across communities, and negatively-valenced emotions (anger, fear) lead the corpus.

---

## 2. Dataset and Graph Overview

The graph models a Portuguese misinformation Telegram corpus. **V1** captures _who said what, where, and to whom_ (channels, users, messages, and their interaction edges). **V2** layers _meaning_ on top: community structure, topics, semantic similarity, and emotion — without rebuilding any V1 node or edge.

- **Time range:** 2020-03-01 → 2025-06-10 (~64 months)
- **Core channels:** 109 (the V1 interaction graph also includes 368 external forward/reply source channels)
- **Missing data:** forwarding and reply metadata are sparse by nature (most messages are neither forwarded nor replies); this is expected, not corruption.

### V1 vs V2 at a glance

| Element                  | Graph V1                                                  | Graph V2 (adds) |
| :----------------------- | :-------------------------------------------------------- | :-------------- |
| Node: Channel            | 477                                                       | 477             |
| Node: User               | 5,854                                                     | 5,854           |
| Node: Message            | 32,285                                                    | 32,285          |
| Node: Community          | —                                                         | 12              |
| Node: Topic              | —                                                         | 270             |
| Edge: structural         | POSTED, IN_CHANNEL, ACTIVE_IN, REPLIES_TO, FORWARDED_FROM | (inherited)     |
| Edge: INTERACTS_WITH     | 1,154                                                     | (inherited)     |
| Edge: BELONGS_TO         | —                                                         | 463             |
| Edge: BELONGS_TO_TOPIC   | —                                                         | 29,729          |
| Edge: SIMILAR_TO         | —                                                         | 9,044           |
| Msg attr: emotion scores | —                                                         | 32,285 messages |

![Monthly message volume](figures/final_report/overview_messages_over_time.png)

_Activity is uneven across the 5-year span, with pronounced surges — useful context for the temporal analysis in Section 9._

---

## 3. Graph Version 1 — Basic Structural Analysis

V1 analysis runs on the derived `INTERACTS_WITH` channel graph, which summarizes shared users, forwards, and replies into weighted channel-to-channel edges.

| Metric                         | Value        |
| :----------------------------- | :----------- |
| Channels in interaction graph  | 463          |
| Interaction edges (undirected) | 1,066        |
| Average degree                 | 4.6          |
| Median degree                  | 1            |
| Graph density                  | 0.0100       |
| Connected components           | 1            |
| Largest component (channels)   | 463 (100.0%) |
| Isolated channels              | 0            |

![Channel degree distribution](figures/final_report/v1_degree_distribution.png)

_The degree distribution is right-skewed: most channels connect to few others while a handful are hubs — the hallmark of a centralized diffusion network._

### Most central channels

Weighted degree measures total interaction strength; betweenness flags channels that sit on many shortest paths (structural bridges).

| channel  | community | degree | weighted_degree | betweenness |
| :------- | --------: | -----: | --------------: | ----------: |
| b2d0f2a3 |         3 |    116 |       1385.0000 |      0.2302 |
| 4a74a4ce |         3 |     28 |        802.0000 |      0.0618 |
| 3de2e13d |         4 |     39 |        719.0000 |      0.0328 |
| 283ecc10 |         6 |     64 |        657.0000 |      0.0880 |
| da78cbfc |         6 |     27 |        509.0000 |      0.0180 |
| 5e16f210 |         1 |    105 |        477.0000 |      0.2114 |
| f8dd7853 |         4 |     81 |        370.0000 |      0.1667 |
| 7d609299 |         4 |     18 |        320.0000 |      0.0073 |
| 6412cadd |         2 |     65 |        257.0000 |      0.1152 |
| 319ff846 |         0 |     33 |        229.0000 |      0.0317 |

_The graph is effectively one connected core (100.0% of channels in the largest component); high-betweenness channels are the brokers that hold otherwise distinct groups together — a question revisited as community bridges in Section 5._

---

## 4. Graph Version 2 — Expanded Structural and Semantic Analysis

V2 keeps every V1 node and edge and adds four enrichment layers, each derived from V1 by one analysis phase:

| Phase   | New node  | New edges / attributes         | Volume                           |
| :------ | :-------- | :----------------------------- | :------------------------------- |
| Phase 1 | Community | BELONGS_TO (channel→community) | 12 communities / 463 memberships |
| Phase 2 | Topic     | BELONGS_TO_TOPIC, DOMINATED_BY | 270 topics / 29,729 assignments  |
| Phase 3 | —         | SIMILAR_TO (message→message)   | 9,044 edges (cosine ≥ 0.80)      |
| Phase 4 | —         | emotion scores on Message      | 32,285 messages labelled         |

**How the phases enrich the graph**

1. _Community detection_ partitions the channel interaction graph into structural groups (Phase 1).
2. _Topic modeling_ (BERTopic over multilingual embeddings) assigns each modeled message a latent topic and rolls topics up to community dominance (Phase 2).
3. _Message similarity_ turns the same embeddings into semantic `SIMILAR_TO` edges, exposing near-duplicate / reused content (Phase 3).
4. _Emotion scoring_ (Portuguese NRC lexicon) attaches eight emotion scores plus polarity and a dominant emotion to every message (Phase 4).

**V2 coverage**

- Communities: 12 · Topics: 270 (+1 noise bucket)
- Similarity edges: 9,044 · Emotion-labelled messages: 32,285
- Temporal span carried from V1: 2020-03 → 2025-06

---

## 5. Community Analysis

### Basic statistics

| Metric             | Value  |
| :----------------- | :----- |
| Communities        | 12     |
| Channels covered   | 463    |
| Mean size          | 38.6   |
| Median size        | 42     |
| Size variance      | 944.3  |
| Largest / smallest | 79 / 2 |

![Channels per community](figures/final_report/community_sizes.png)

_Community sizes are strongly imbalanced — a few large communities dominate the structure while several are small satellites._

### Top communities (by message volume)

| community | channels | messages | users | density | keywords                                  |
| :-------- | -------: | -------: | ----: | ------: | :---------------------------------------- |
| C4        |       57 |     8424 |  4214 |   0.048 | vacina · só · pessoas · quem              |
| C0        |       79 |     7085 |    60 |   0.033 | apocalipserd · estão · contra · mundo     |
| C2        |       67 |     4642 |    89 |   0.039 | trump · presidente · sobre · estão        |
| C3        |       63 |     4562 |   840 |   0.036 | vacina · covid · contra · vacinas         |
| C6        |       41 |     4450 |   472 |   0.113 | sobre · contra · estão · brasil           |
| C1        |       78 |     1706 |   372 |   0.028 | canal · covid · pessoas · vacina          |
| C5        |       44 |      583 |     6 |   0.048 | inscreva · oráculo · nacionalista · canal |
| C7        |       24 |      417 |    41 |   0.116 | israel · deuxxxsss · nazarena · yhwh      |

_Message and user counts come only from the core channels; size (channels) additionally includes external forward/reply sources clustered with them._

### Bridges between communities

Cross-community `INTERACTS_WITH` weight reveals which communities are most tightly coupled — the strongest candidates for shared audiences or content flow.

| community_pair | interaction_weight | bridging_edges |
| :------------- | -----------------: | -------------: |
| C3 ↔ C4        |              321.0 |             34 |
| C4 ↔ C6        |              232.0 |             26 |
| C1 ↔ C4        |              156.0 |             41 |
| C1 ↔ C3        |              129.0 |             29 |
| C0 ↔ C3        |              102.0 |             35 |
| C2 ↔ C6        |               89.0 |             35 |
| C3 ↔ C6        |               87.0 |             18 |
| C0 ↔ C2        |               72.0 |             36 |
| C0 ↔ C4        |               67.0 |             28 |
| C2 ↔ C4        |               65.0 |             29 |

- **281 users** are active across more than one community, acting as human bridges that carry content between otherwise separate groups.

_What this answers: the dominant communities are structurally central (largest, densest), and a measurable set of shared users plus weighted cross-links shows the communities are not isolated silos but a coupled ecosystem._

---

## 6. Topic Analysis

BERTopic produced **270 topics** from 29,729 modeled messages. The noise bucket (`-1`) absorbs **48.5%** of assignments — short or generic messages with no stable topic.

### Most frequent topics

| topic | messages | label / keywords                        |
| ----: | -------: | :-------------------------------------- |
|     0 |     1089 | ucrânia · rússia · putin · russo        |
|     1 |      879 | israel · gaza · hamas · hezbollah       |
|     2 |      606 | deus · jesus · senhor · cristo          |
|     3 |      432 | vacina · vacinas · vacinados · vacinado |
|     4 |      414 | morre · morreu · anos · infarto         |
|     5 |      353 | non · che · di · esta                   |
|     6 |      351 | bolsonaro · jair · presidente · ele     |
|     7 |      304 | eu · estou · vou · vc                   |
|     8 |      263 | trump · donald · fbi · presidente       |
|     9 |      260 | chá · corpo · colher · água             |
|    10 |      250 | vídeo · youtube · vídeos · video        |
|    11 |      237 | brasil · brasileiro · brasileiros · no  |

![Top topics by message count](figures/final_report/topic_top_counts.png)

_A few large topics capture mainstream narratives; the long tail of small topics reflects niche or fast-moving content._

### Dominant topic per community

| community | top_topic | share | label / keywords                        |
| :-------- | --------: | ----: | :-------------------------------------- |
| C0        |         0 | 0.116 | ucrânia · rússia · putin · russo        |
| C6        |         0 | 0.131 | ucrânia · rússia · putin · russo        |
| C4        |         3 | 0.070 | vacina · vacinas · vacinados · vacinado |
| C2        |         0 | 0.104 | ucrânia · rússia · putin · russo        |
| C3        |         4 | 0.091 | morre · morreu · anos · infarto         |
| C7        |        25 | 0.317 | deuxxxsss · yhwh · israel · diabo       |
| C1        |         2 | 0.053 | deus · jesus · senhor · cristo          |
| C10       |        95 | 0.361 | 5ø · 5â · 5ô · 5j                       |

- **4 topics** are dominant in more than one community — evidence that core narratives are shared across structurally separate groups.
- **Most thematically diverse communities:** C0 (246 topics), C4 (236 topics), C3 (235 topics); the narrowest carry only a handful of distinct topics.

_What this answers: communities differ sharply in thematic breadth, yet the biggest topics recur across communities — narrative reuse is structural, not isolated._

---

## 7. Semantic Similarity Analysis

Phase 3 retains message pairs with cosine ≥ 0.80 (top-5 neighbours each). Because the threshold is a hard floor, the score distribution starts there and decays toward 1.0.

| Metric                | Value         |
| :-------------------- | :------------ |
| Similar pairs (edges) | 9,044         |
| Mean similarity       | 0.846         |
| Median similarity     | 0.832         |
| Min / Max             | 0.800 / 1.000 |
| Intra-community pairs | 3,932         |
| Cross-community pairs | 5,112         |

![Cosine similarity distribution](figures/final_report/similarity_score_distribution.png)

_About **56.5%** of similar pairs cross community boundaries: the same or near-identical content is being reposted across structurally distinct groups._

### Strongest similar pairs

| source          | target          | cosine | same_community |
| :-------------- | :-------------- | -----: | :------------- |
| ae1c52ac_33114  | 5c8f1dbc_90810  |  1.000 | False          |
| d1ca5f3b_979643 | d1ca5f3b_984338 |  1.000 | True           |
| d1ca5f3b_984338 | d1ca5f3b_979643 |  1.000 | True           |
| 5e16f210_63592  | 5d56df3d_885    |  1.000 | False          |
| f212c8a1_1495   | 5d56df3d_44990  |  1.000 | True           |
| ece83e9b_10185  | 283ecc10_426194 |  1.000 | False          |
| 22a60237_1248   | 4a74a4ce_51786  |  1.000 | False          |
| 4a74a4ce_84754  | 59f557a4_62720  |  1.000 | False          |
| ece83e9b_67251  | 59f557a4_51482  |  1.000 | False          |
| 7d609299_531511 | 3de2e13d_168970 |  1.000 | True           |

### Most semantically redundant channels

Channels with many _internal_ similar pairs repeat their own content most often.

| channel  | internal_similar_pairs |
| :------- | ---------------------: |
| 319ff846 |                    525 |
| 3de2e13d |                    453 |
| b2d0f2a3 |                    114 |
| b09ba5f3 |                     65 |
| 5e16f210 |                     64 |
| d41e9a65 |                     64 |
| 6412cadd |                     56 |
| ece83e9b |                     56 |
| 2e9e491d |                     53 |
| 95818eec |                     50 |

### Cross-community bridge messages

Messages whose similar neighbours span the most communities act as semantic hubs — the same idea echoed everywhere.

| message         | linked_communities |
| :-------------- | -----------------: |
| b2d0f2a3_3360   |                  8 |
| f8dd7853_2677   |                  8 |
| f610bd52_37360  |                  8 |
| 0eceb77f_17040  |                  7 |
| 5fc27012_12790  |                  7 |
| 279a22fc_1173   |                  7 |
| 5870b702_3074   |                  7 |
| 87c04c78_7727   |                  7 |
| 71744f76_1030   |                  7 |
| b2d0f2a3_355556 |                  7 |

_What this answers: redundancy is concentrated in specific channels, and a small set of messages function as cross-community templates — a fingerprint of coordinated reuse._

---

## 8. Sentiment and Emotion Analysis

All 32,285 messages carry NRC emotion scores. Mean polarity is **0.42 positive / 0.44 negative** — the corpus leans negative.

![Dominant emotion distribution](figures/final_report/emotion_distribution.png)

_Negatively-valenced emotions (anger, fear) and trust lead; surprise and joy are rare. `neutral` marks messages with no lexicon match._

### Emotion profile by community

![Emotion share by community](figures/final_report/emotion_by_community.png)

_Communities differ in tone: some are anger-dominated, others trust- or anticipation-leaning, despite drawing on overlapping topics._

### Where each emotion concentrates

| emotion      | top_community | share |
| :----------- | :------------ | ----: |
| anger        | C0            | 0.215 |
| anticipation | C8            | 0.375 |
| disgust      | C11           | 0.111 |
| fear         | C0            | 0.155 |
| joy          | C11           | 0.111 |
| sadness      | C1            | 0.081 |
| surprise     | C4            | 0.016 |
| trust        | C9            | 0.575 |

### Channels with the most distinctive emotional profile

Channels (≥50 messages) where a single emotion captures the largest share — the clearest emotional 'signatures'.

| channel  | messages | top_emotion | share |
| :------- | -------: | :---------- | ----: |
| e75f171b |       87 | trust       | 0.575 |
| 71744f76 |       95 | trust       | 0.474 |
| 11106440 |       90 | trust       | 0.444 |
| e16902a1 |      300 | trust       | 0.433 |
| 93aaf191 |       77 | sadness     | 0.312 |
| 86854a3d |       84 | anger       | 0.310 |
| 51d03a78 |      120 | trust       | 0.308 |
| 99da5dfb |       52 | trust       | 0.308 |
| 7e8416c9 |      258 | trust       | 0.298 |
| 944f6c68 |       74 | anger       | 0.284 |

_What this answers: emotion is not uniform — specific communities and channels specialize in specific affective registers, which Section 10 ties back to topics._

---

## 9. Temporal Analysis

Message timestamps (2020–2025) let us track how structure and tone evolve.

### Community activity over time

![Monthly activity of the largest communities](figures/final_report/temporal_community_activity.png)

_Communities rise and fall at different times — activity is event-driven, not steady, and leadership of the conversation shifts between groups._

### Emotion over time

![Monthly emotion composition](figures/final_report/temporal_emotion_share.png)

_The emotional mix is not stable: periods of elevated anger/fear alternate with calmer trust/anticipation phases, suggesting reactive responses to external events._

### Sentiment volatility by community

Standard deviation of monthly net polarity (positive − negative) measures emotional stability: high values = volatile mood, low = consistent tone.

| community | net_polarity_volatility | mean_net_polarity |
| :-------- | ----------------------: | ----------------: |
| C7        |                  0.5228 |           -0.1135 |
| C10       |                  0.5095 |            0.1873 |
| C8        |                  0.4597 |            0.4077 |
| C11       |                  0.4492 |            0.1537 |
| C5        |                  0.3534 |            0.0415 |
| C9        |                  0.2781 |            0.3713 |
| C6        |                  0.2342 |            0.0520 |
| C1        |                  0.1967 |            0.0400 |
| C3        |                  0.1578 |           -0.0299 |
| C4        |                  0.1538 |           -0.0153 |

_What this answers: some communities keep a stable emotional profile while others swing sharply — the volatile ones are the most reactive to events._

---

## 10. Cross-Layer Analysis

Combining the four layers exposes relationships no single layer shows.

### Emotion × Topic

![Dominant emotion by topic](figures/final_report/crosslayer_emotion_by_topic.png)

_Topics carry distinct emotional signatures — some narratives are reliably anger-driven, others fear- or trust-driven, regardless of which community posts them._

### Community-level correlations

![Community metric correlations](figures/final_report/crosslayer_correlation.png)

![Community size vs topic diversity](figures/final_report/crosslayer_size_vs_diversity.png)

- Message volume vs topic diversity: **r = 0.89** — larger communities are more thematically diverse.
- Negative polarity vs internal similarity: **r = -0.12** — emotional negativity and content redundancy are largely independent.

_What this answers: structure, topic, semantics, and emotion are partially coupled — volume drives breadth, while emotion aligns more with topic than with raw community size._

---

## 11. Statistical Summary

Descriptive statistics across the 12 communities (each community is one observation). This quantifies the imbalance described qualitatively above.

| metric       |    mean |     std |   min |  median |     max |
| :----------- | ------: | ------: | ----: | ------: | ------: |
| channels     |   38.58 |   30.73 |  2.00 |   42.50 |   79.00 |
| messages     | 2680.17 | 3023.76 | 40.00 | 1144.50 | 8424.00 |
| users        |  512.42 | 1194.29 |  1.00 |   56.00 | 4214.00 |
| topics       |  131.75 |  101.40 |  9.00 |  143.50 |  246.00 |
| avg_sim      |    0.79 |    0.25 |  0.00 |    0.86 |    0.88 |
| net_polarity |    0.08 |    0.15 | -0.10 |    0.04 |    0.37 |

_Large standard deviations relative to means (especially for messages and users) confirm a heavy-tailed structure: a few communities dominate every metric. Topic breadth and similarity are more evenly spread._

---

## 12. Key Findings

### 1. Well-separated community structure

- **Evidence:** Leiden modularity = 0.42 across 12 communities.
- **Interpretation:** The channel network has genuine, non-random group structure — communities are a meaningful unit of analysis, not an artefact.
- **Supported by:** V2 / Phase 1

### 2. Activity is highly concentrated

- **Evidence:** The largest community alone holds 26.2% of all messages.
- **Interpretation:** A handful of channels/communities drive the corpus; moderation or study effort targeted there covers most of the volume.
- **Supported by:** V1 structure + V2 / Phase 1

### 3. Narratives are reused across communities

- **Evidence:** 56.5% of 9,044 near-duplicate pairs cross community lines; several top topics dominate multiple communities.
- **Interpretation:** The same content is repackaged across structurally distinct groups — consistent with coordinated or template-driven diffusion.
- **Supported by:** V2 / Phases 2 & 3

### 4. The corpus leans negative

- **Evidence:** 'anger' is the leading non-neutral emotion; mean negative polarity exceeds positive.
- **Interpretation:** Affective framing skews toward anger/fear, typical of mobilizing misinformation.
- **Supported by:** V2 / Phase 4

### 5. Emotion tracks topic more than size

- **Evidence:** Emotion×topic shows stable per-topic affect; community-level correlations are weak between size and negativity.
- **Interpretation:** Tone is driven by _what_ is discussed, not merely by _how active_ a group is.
- **Supported by:** V2 / Cross-layer

### 6. Topic noise is substantial

- **Evidence:** 48.5% of modeled messages fall in BERTopic's noise bucket.
- **Interpretation:** Short, generic, or boilerplate messages resist topic assignment — a caveat for any topic-based conclusion.
- **Supported by:** V2 / Phase 2

---

## 13. Limitations

- **Topic noise.** A large share of messages land in BERTopic's `-1` bucket; topic-level figures describe only the modeled subset.
- **Lexicon emotion.** NRC is a bag-of-words lexicon: it misses negation, sarcasm, irony, and context, and Portuguese coverage is imperfect. Scores are indicative, not ground truth.
- **Community detection scope.** Communities are detected on the channel interaction graph only; users and messages inherit a community via their channel.
- **Similarity truncation.** `SIMILAR_TO` keeps only pairs ≥ 0.80 with top-5 neighbours, so redundancy counts are lower bounds.
- **Incomplete reply/forward recovery.** Many reply/forward sources are external or unrecovered, so cross-channel structure is partially observed.
- **Descriptive keywords ≠ topics.** Per-community keywords (Phase 1) are TF-IDF descriptors, not the formal BERTopic topics of Phase 2.

---

## Appendix

### A1. All communities

| community | channels | messages | users | topics | dominant_emotion | keywords                                                 |
| :-------- | -------: | -------: | ----: | -----: | :--------------- | :------------------------------------------------------- |
| C0        |       79 |     7085 |    60 |    246 | anger            | apocalipserd · estão · contra · mundo · sobre            |
| C1        |       78 |     1706 |   372 |    178 | trust            | canal · covid · pessoas · vacina · nosso                 |
| C2        |       67 |     4642 |    89 |    218 | trust            | trump · presidente · sobre · estão · gefaziobreakingnews |
| C3        |       63 |     4562 |   840 |    235 | anger            | vacina · covid · contra · vacinas · sobre                |
| C4        |       57 |     8424 |  4214 |    236 | anticipation     | vacina · só · pessoas · quem · estão                     |
| C5        |       44 |      583 |     6 |    109 | trust            | inscreva · oráculo · nacionalista · canal · nosso        |
| C6        |       41 |     4450 |   472 |    232 | anger            | sobre · contra · estão · brasil · lula                   |
| C7        |       24 |      417 |    41 |     62 | anger            | israel · deuxxxsss · nazarena · yhwh · verdades          |
| C8        |        3 |       40 |     1 |      9 | anticipation     | live · hoje · pode · vocês · off                         |
| C9        |        3 |       87 |     1 |     17 | trust            | simões · info · daniel · canal · saúde                   |
| C10       |        2 |      121 |    52 |     26 | trust            | mms · cds · desparasitação · corpo · boa                 |
| C11       |        2 |       45 |     1 |     13 | anticipation     | água · cada · dia · sal · suco                           |

### A2. Full emotion-share matrix by community

| community | anger | anticipation | disgust |  fear |   joy | sadness | surprise | trust | neutral |
| :-------- | ----: | -----------: | ------: | ----: | ----: | ------: | -------: | ----: | ------: |
| C0        | 0.215 |        0.155 |   0.030 | 0.155 | 0.026 |   0.058 |    0.011 | 0.166 |   0.186 |
| C1        | 0.151 |        0.140 |   0.037 | 0.102 | 0.019 |   0.081 |    0.010 | 0.230 |   0.230 |
| C2        | 0.161 |        0.169 |   0.026 | 0.123 | 0.034 |   0.059 |    0.010 | 0.235 |   0.183 |
| C3        | 0.190 |        0.154 |   0.046 | 0.142 | 0.022 |   0.064 |    0.012 | 0.153 |   0.217 |
| C4        | 0.143 |        0.157 |   0.038 | 0.104 | 0.033 |   0.068 |    0.016 | 0.133 |   0.309 |
| C5        | 0.178 |        0.160 |   0.041 | 0.110 | 0.019 |   0.062 |    0.007 | 0.302 |   0.122 |
| C6        | 0.196 |        0.165 |   0.029 | 0.142 | 0.021 |   0.063 |    0.013 | 0.180 |   0.191 |
| C7        | 0.211 |        0.144 |   0.086 | 0.106 | 0.024 |   0.043 |    0.014 | 0.127 |   0.245 |
| C8        | 0.050 |        0.375 |   0.025 | 0.025 | 0.000 |   0.025 |    0.000 | 0.200 |   0.300 |
| C9        | 0.069 |        0.184 |   0.011 | 0.069 | 0.000 |   0.057 |    0.000 | 0.575 |   0.034 |
| C10       | 0.116 |        0.124 |   0.033 | 0.058 | 0.033 |   0.058 |    0.000 | 0.190 |   0.388 |
| C11       | 0.156 |        0.200 |   0.111 | 0.111 | 0.111 |   0.067 |    0.000 | 0.133 |   0.111 |

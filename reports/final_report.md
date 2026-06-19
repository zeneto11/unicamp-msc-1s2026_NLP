# Aletheia-PT — Graph V2 Analytical Report

_Structural, community, topic, semantic, and emotional analysis of the Portuguese Aletheia Telegram corpus. Generated automatically by `scripts/report/generate.py` from the V1/V2 graph artifacts._

_Generated: 2026-06-17_

---

## 1. Executive Summary

- **Structure (V1).**
  - 477 channels (109 core + external sources) and 5,854 users.
  - 1,154 channel-interaction edges (shared users, forwards, replies).
- **Communities (V2 / Phase 1).**
  - Leiden finds **12 communities** over 463 channels.
  - Modularity **0.42** — a clear, well-separated structure.
- **Topics (V2 / Phase 2).**
  - **169 topics** from 29,467 modeled messages.
  - 9.0% residual noise after outlier reassignment (down from ~48% default); each community has *characteristic* topics revealed by lift.
- **Semantics (V2 / Phase 3).**
  - **8,926 near-duplicate message pairs** (cosine ≥ 0.80).
  - 57.7% of them link *different* communities — measurable cross-group narrative reuse.
- **Emotion (V2 / Phase 4).**
  - Dominant tone is **anger, trust, anticipation**.
  - 22.5% of messages carry no lexicon emotion (neutral).
- **Most active community.**
  - `C4` with 8,424 messages — vacina · só · pessoas.

> The graph is highly centralized: a few large channels and communities carry most messages. Communities have distinct thematic identities (anti-vaccine, alternative-medicine, geopolitical, religious-extremist) yet cross-post shared templates; tone is neutral-heavy with anger/fear leading among emotional messages.

---

## 2. Dataset and Graph Overview

The graph models a Portuguese misinformation Telegram corpus. **V1** captures *who said what, where, and to whom* (channels, users, messages, and their interaction edges). **V2** layers *meaning* on top: community structure, topics, semantic similarity, and emotion — without rebuilding any V1 node or edge.

- **Time range:** 2020-03-01 → 2025-06-10 (~64 months)
- **Core channels:** 109 (the V1 interaction graph also includes 368 external forward/reply source channels)
- **Missing data:** forwarding and reply metadata are sparse by nature (most messages are neither forwarded nor replies); this is expected, not corruption.

### V1 vs V2 at a glance

| Element                  | Graph V1                                                  | Graph V2 (adds)   |
|:-------------------------|:----------------------------------------------------------|:------------------|
| Node: Channel            | 477                                                       | 477               |
| Node: User               | 5,854                                                     | 5,854             |
| Node: Message            | 32,285                                                    | 32,285            |
| Node: Community          | —                                                         | 12                |
| Node: Topic              | —                                                         | 169               |
| Edge: structural         | POSTED, IN_CHANNEL, ACTIVE_IN, REPLIES_TO, FORWARDED_FROM | (inherited)       |
| Edge: INTERACTS_WITH     | 1,154                                                     | (inherited)       |
| Edge: BELONGS_TO         | —                                                         | 463               |
| Edge: BELONGS_TO_TOPIC   | —                                                         | 29,467            |
| Edge: SIMILAR_TO         | —                                                         | 8,926             |
| Msg attr: emotion scores | —                                                         | 32,285 messages   |

![Monthly message volume](figures/final_report/overview_messages_over_time.png)

_Activity is uneven across the 5-year span, with pronounced surges — useful context for the temporal analysis in Section 9._

---

## 3. Graph Version 1 — Basic Structural Analysis

V1 is the structural layer: three entity types (Channel, User, Message) connected by authorship, membership, reply, and forwarding relations. From these, a derived `INTERACTS_WITH` edge projects the network onto a weighted channel-to-channel graph.

### Entities and relations

| Element        | Type   |   Count | Meaning                     |
|:---------------|:-------|--------:|:----------------------------|
| Channel        | node   |     477 | actors — Telegram channels  |
| User           | node   |    5854 | actors — message authors    |
| Message        | node   |   32285 | individual posts            |
| POSTED         | edge   |   32285 | User → Message              |
| IN_CHANNEL     | edge   |   32285 | Message → Channel           |
| ACTIVE_IN      | edge   |    6337 | User → Channel (aggregated) |
| REPLIES_TO     | edge   |    8315 | Message → Message           |
| FORWARDED_FROM | edge   |    4312 | Message → source Channel    |
| REPLIED_INTO   | edge   |    8315 | Message → replied Channel   |
| INTERACTS_WITH | edge   |    1154 | Channel ↔ Channel (derived) |

![Graph V1 entities and relations](figures/final_report/v1_graph_dimensions.png)

_The graph is message-centric: `POSTED` and `IN_CHANNEL` scale with the 32k messages, while reply/forward edges are far sparser — most posts are standalone._

### Channel interaction graph

The remaining structural analysis runs on the `INTERACTS_WITH` projection, which summarizes shared users, forwards, and replies into weighted channel edges — the same graph community detection consumes in Phase 1.

| Metric                         | Value        |
|:-------------------------------|:-------------|
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

| channel   |   community |   degree |   weighted_degree |   betweenness |
|:----------|------------:|---------:|------------------:|--------------:|
| b2d0f2a3  |           3 |      116 |         1385.0000 |        0.2302 |
| 4a74a4ce  |           3 |       28 |          802.0000 |        0.0618 |
| 3de2e13d  |           4 |       39 |          719.0000 |        0.0328 |
| 283ecc10  |           6 |       64 |          657.0000 |        0.0880 |
| da78cbfc  |           6 |       27 |          509.0000 |        0.0180 |
| 5e16f210  |           1 |      105 |          477.0000 |        0.2114 |
| f8dd7853  |           4 |       81 |          370.0000 |        0.1667 |
| 7d609299  |           4 |       18 |          320.0000 |        0.0073 |
| 6412cadd  |           2 |       65 |          257.0000 |        0.1152 |
| 319ff846  |           0 |       33 |          229.0000 |        0.0317 |

_The graph is effectively one connected core (100.0% of channels in the largest component); high-betweenness channels are the brokers that hold otherwise distinct groups together — a question revisited as community bridges in Section 5._

---

## 4. Graph Version 2 — Expanded Structural and Semantic Analysis

V2 keeps every V1 node and edge untouched and adds two new entity types (Community, Topic) plus semantic relations and per-message emotion scores. The plot below mirrors Section 3, showing only what each analysis phase *adds*:

![Graph V2 added entities and relations](figures/final_report/v2_graph_dimensions.png)

_Enrichment is dominated by `BELONGS_TO_TOPIC` (29,467) and `SIMILAR_TO` (8,926) — message-level edges — while the new Community/Topic nodes are comparatively few but anchor the whole semantic layer._

**What each phase adds**

1. *Community detection* — partitions the channel interaction graph into structural groups (Phase 1).
2. *Topic modeling* — BERTopic over multilingual embeddings assigns each modeled message a topic and rolls topics up to community dominance (Phase 2).
3. *Message similarity* — the same embeddings become `SIMILAR_TO` edges, exposing near-duplicate / reused content (Phase 3).
4. *Emotion scoring* — the Portuguese NRC lexicon attaches eight emotion scores, polarity, and a dominant emotion to every message (Phase 4).

---

## 5. Community Analysis

### Basic statistics

| Metric             | Value   |
|:-------------------|:--------|
| Communities        | 12      |
| Channels covered   | 463     |
| Mean size          | 38.6    |
| Median size        | 42      |
| Size variance      | 944.3   |
| Largest / smallest | 79 / 2  |

![Channels per community](figures/final_report/community_sizes.png)

_Community sizes are strongly imbalanced — a few large communities dominate the structure while several are small satellites._

![Messages per community](figures/final_report/community_messages.png)

_Volume is even more skewed than channel count: the ranking by messages differs from the ranking by channels, so structural size does not equal activity._

### Communities by message volume

| community   |   channels |   messages |   users |   density | keywords                                  |
|:------------|-----------:|-----------:|--------:|----------:|:------------------------------------------|
| C4          |         57 |       8424 |    4214 |     0.048 | vacina · só · pessoas · quem              |
| C0          |         79 |       7085 |      60 |     0.033 | apocalipserd · estão · contra · mundo     |
| C2          |         67 |       4642 |      89 |     0.039 | trump · presidente · sobre · estão        |
| C3          |         63 |       4562 |     840 |     0.036 | vacina · covid · contra · vacinas         |
| C6          |         41 |       4450 |     472 |     0.113 | sobre · contra · estão · brasil           |
| C1          |         78 |       1706 |     372 |     0.028 | canal · nosso · covid · pessoas           |
| C5          |         44 |        583 |       6 |     0.048 | inscreva · oráculo · nacionalista · canal |
| C7          |         24 |        417 |      41 |     0.116 | israel · deuxxxsss · nazarena · yhwh      |
| C10         |          2 |        121 |      52 |     1.000 | mms · cds · desparasitação · corpo        |
| C9          |          3 |         87 |       1 |     0.667 | simões · info · daniel · canal            |
| C11         |          2 |         45 |       1 |     1.000 | água · cada · dia · sal                   |
| C8          |          3 |         40 |       1 |     0.667 | live · hoje · pode · vocês                |

_Message and user counts come only from the core channels; size (channels) additionally includes external forward/reply sources clustered with them._

### Bridges between communities

Cross-community `INTERACTS_WITH` weight reveals which communities are most tightly coupled — the strongest candidates for shared audiences or content flow.

| community_pair   |   interaction_weight |   bridging_edges |
|:-----------------|---------------------:|-----------------:|
| C3 ↔ C4          |                321.0 |               34 |
| C4 ↔ C6          |                232.0 |               26 |
| C1 ↔ C4          |                156.0 |               41 |
| C1 ↔ C3          |                129.0 |               29 |
| C0 ↔ C3          |                102.0 |               35 |
| C2 ↔ C6          |                 89.0 |               35 |
| C3 ↔ C6          |                 87.0 |               18 |
| C0 ↔ C2          |                 72.0 |               36 |
| C0 ↔ C4          |                 67.0 |               28 |
| C2 ↔ C4          |                 65.0 |               29 |

- **281 users** are active across more than one community, acting as human bridges that carry content between otherwise separate groups.

_What this answers: the dominant communities are structurally central (largest, densest), and a measurable set of shared users plus weighted cross-links shows the communities are not isolated silos but a coupled ecosystem._

---

## 6. Topic Analysis

BERTopic produced **169 topics** from 29,467 modeled messages. Default HDBSCAN leaves ~48% of short social-media messages as outliers — and those outliers are **not** shorter than clustered messages, so the bucket is a clustering artifact, not a data-quality signal. We therefore reassign outliers to their nearest topic above a cosine floor, leaving a residual noise bucket of **9.0%** of assignments (genuinely un-clusterable content).

### Most frequent topics

|   topic |   messages | label / keywords                          |
|--------:|-----------:|:------------------------------------------|
|       0 |       3178 | vacina · vacinas · covid · vacinação      |
|       1 |       1135 | ucrânia · rússia · putin · russo          |
|       2 |       1091 | israel · gaza · hamas · israelense        |
|       3 |        662 | canal · quem · povo · especulando         |
|       6 |        647 | vou · vc · estou · minha                  |
|       8 |        547 | deus · jesus · senhor · cristo            |
|      12 |        519 | brasil · brasileiro · brasileiros · povo  |
|       5 |        430 | bolsonaro · jair · presidente · lula      |
|       4 |        423 | morre · morreu · anos · infarto           |
|      25 |        416 | liberdade · expressão · censura · governo |
|      10 |        398 | médicos · médico · hospital · saúde       |
|      13 |        366 | moraes · stf · federal · alexandre        |

![Top topics by message count](figures/final_report/topic_top_counts.png)

_A few large topics capture mainstream narratives; the long tail of small topics reflects niche or fast-moving content._

### Distinctive topics per community (lift)

Lift = a topic's share inside a community divided by its share in the whole corpus. Unlike the raw mode, lift reveals what each community is *characteristically* about rather than which global topic happens to be largest.

| community   |   topic |   lift |   messages | label / keywords                                       |
|:------------|--------:|-------:|-----------:|:-------------------------------------------------------|
| C0          |     111 |    3.8 |         28 | importantes · eventos · militares · dia                |
| C1          |     151 |   13.8 |         22 | nosso · canal · especulandosfatosgrupoficial · youtube |
| C2          |      95 |    4.1 |         42 | km · obras · barreira · pista                          |
| C3          |       4 |    3.0 |        182 | morre · morreu · anos · infarto                        |
| C4          |      31 |    3.6 |         89 | cds · protocolo · dmso · ml                            |
| C5          |       7 |    5.0 |         35 | lula · janja · governo · pl                            |
| C6          |      50 |    3.1 |         47 | imposto · impostos · reforma · lula                    |
| C7          |      27 |   44.0 |         76 | israel · yhwh · deuxxxsss · diabo                      |
| C9          |      33 |   22.1 |         15 | oms · mundial · global · fórum                         |
| C10         |     132 |  149.0 |         16 | aut · grama · blá · zebra                              |

_These over-represented topics separate the communities into recognisable misinformation genres — anti-vaccine, alternative-medicine, geopolitical, religious-extremist — that the raw 'most common topic' completely hides._

### Most common topic per community (for contrast)

| community   |   mode_topic |   plurality | label / keywords                     |
|:------------|-------------:|------------:|:-------------------------------------|
| C0          |            2 |       0.083 | israel · gaza · hamas · israelense   |
| C1          |            0 |       0.212 | vacina · vacinas · covid · vacinação |
| C2          |            1 |       0.067 | ucrânia · rússia · putin · russo     |
| C3          |            0 |       0.209 | vacina · vacinas · covid · vacinação |
| C4          |            0 |       0.180 | vacina · vacinas · covid · vacinação |
| C5          |            7 |       0.068 | lula · janja · governo · pl          |
| C6          |            1 |       0.083 | ucrânia · rússia · putin · russo     |
| C7          |           27 |       0.219 | israel · yhwh · deuxxxsss · diabo    |
| C8          |           59 |       0.219 | canal · live · vocês · canais        |
| C9          |           33 |       0.190 | oms · mundial · global · fórum       |
| C10         |          132 |       0.195 | aut · grama · blá · zebra            |
| C11         |           23 |       0.306 | corpo · diabetes · água · açúcar     |

- The modal topic captures at most **30.6%** of a community's messages — these are weak pluralities over a flat, long-tailed distribution, not true dominance. The same one or two globally-large topics top many communities, which is why the lift view above is the more informative cut.

### Topic coverage and breadth

![Topic diversity per community](figures/final_report/topic_diversity_by_community.png)

- **Noise coverage is uneven:** the residual outlier rate ranges from 6.7% to 14.6% across communities, so per-community topic figures rest on different fractions of each group's messages.
- Distinct-topic *counts* rise with message volume — a rarefaction effect. Section 10 normalizes for size and shows breadth-per-message actually **falls** as communities grow.

_What this answers: communities are thematically distinct once you control for the globally-popular topics (via lift); apparent 'shared dominance' is mostly an artifact of a few large topics plus a flat per-community distribution._

---

## 7. Semantic Similarity Analysis

Phase 3 retains message pairs with cosine ≥ 0.80 (top-5 neighbours each). Because the threshold is a hard floor, the score distribution starts there and decays toward 1.0.

| Metric                | Value         |
|:----------------------|:--------------|
| Similar pairs (edges) | 8,926         |
| Mean similarity       | 0.846         |
| Median similarity     | 0.832         |
| Min / Max             | 0.800 / 1.000 |
| Intra-community pairs | 3,772         |
| Cross-community pairs | 5,154         |

![Cosine similarity distribution](figures/final_report/similarity_score_distribution.png)

_About **57.7%** of similar pairs cross community boundaries: the same or near-identical content is being reposted across structurally distinct groups._

### Strongest similar pairs

| source          | target          |   cosine | same_community   |
|:----------------|:----------------|---------:|:-----------------|
| 5e16f210_111836 | 5e16f210_111205 |    1.000 | True             |
| 4a74a4ce_84754  | 59f557a4_62720  |    1.000 | False            |
| ece83e9b_68881  | 279a22fc_130938 |    1.000 | False            |
| 6412cadd_76386  | f212c8a1_9223   |    1.000 | True             |
| 5e16f210_111205 | 5e16f210_111836 |    1.000 | True             |
| 279a22fc_130938 | ece83e9b_68881  |    1.000 | False            |
| f212c8a1_9223   | 6412cadd_76386  |    1.000 | True             |
| 59f557a4_62720  | 4a74a4ce_84754  |    1.000 | False            |
| 5e16f210_63592  | 5d56df3d_885    |    1.000 | False            |
| 7d609299_531511 | 3de2e13d_168970 |    1.000 | True             |

### Most semantically redundant channels

Channels with many *internal* similar pairs repeat their own content most often.

| channel   |   internal_similar_pairs |
|:----------|-------------------------:|
| 319ff846  |                      520 |
| 3de2e13d  |                      437 |
| b2d0f2a3  |                      116 |
| b09ba5f3  |                       65 |
| 87c04c78  |                       62 |
| 5e16f210  |                       58 |
| ece83e9b  |                       56 |
| 95818eec  |                       50 |
| 2e9e491d  |                       49 |
| f8dd7853  |                       45 |

### Cross-community bridge messages

Messages whose similar neighbours span the most communities act as semantic hubs — the same idea echoed everywhere.

| message         |   linked_communities |
|:----------------|---------------------:|
| f8dd7853_2677   |                    8 |
| f610bd52_37360  |                    8 |
| 0eceb77f_26428  |                    8 |
| b2d0f2a3_3360   |                    8 |
| 3de2e13d_496016 |                    7 |
| 3de2e13d_262432 |                    7 |
| ece83e9b_47226  |                    7 |
| 59f557a4_52700  |                    7 |
| 286732f2_2644   |                    7 |
| e75f171b_7504   |                    7 |

_What this answers: redundancy is concentrated in specific channels, and a small set of messages function as cross-community templates — a fingerprint of coordinated reuse._

---

## 8. Sentiment and Emotion Analysis

All 32,285 messages carry NRC emotion scores. Mean polarity is **0.42 positive / 0.44 negative** — the corpus leans slightly negative.

![Dominant emotion distribution](figures/final_report/emotion_distribution.png)

> **Read the dominant-emotion labels with care.** `neutral` (no lexicon match) is the single largest class at **22.5%** of messages and is the actual plurality in **5/12** communities. The per-community and per-channel 'dominant emotion' reported below is the leading *non-neutral* register, so it overstates how emotionally-charged the average message is.

_Among non-neutral emotions, anger, trust, and anticipation lead; surprise and joy are rare._

### Emotion profile by community

![Emotion share by community](figures/final_report/emotion_by_community.png)

_Communities differ in tone: some are anger-dominated, others trust- or anticipation-leaning, despite drawing on overlapping topics._

### Where each emotion concentrates

| emotion      | top_community   |   share |
|:-------------|:----------------|--------:|
| anger        | C0              |   0.215 |
| anticipation | C8              |   0.375 |
| disgust      | C11             |   0.111 |
| fear         | C0              |   0.155 |
| joy          | C11             |   0.111 |
| sadness      | C1              |   0.081 |
| surprise     | C4              |   0.016 |
| trust        | C9              |   0.575 |

### Channels with the most distinctive emotional profile

Channels (≥50 messages) where a single emotion captures the largest share — the clearest emotional 'signatures'.

| channel   |   messages | top_emotion   |   share |
|:----------|-----------:|:--------------|--------:|
| e75f171b  |         87 | trust         |   0.575 |
| 71744f76  |         95 | trust         |   0.474 |
| 11106440  |         90 | trust         |   0.444 |
| e16902a1  |        300 | trust         |   0.433 |
| 93aaf191  |         77 | sadness       |   0.312 |
| 86854a3d  |         84 | anger         |   0.310 |
| 51d03a78  |        120 | trust         |   0.308 |
| 99da5dfb  |         52 | trust         |   0.308 |
| 7e8416c9  |        258 | trust         |   0.298 |
| 944f6c68  |         74 | anger         |   0.284 |

_What this answers: emotion is not uniform — specific communities and channels specialize in specific affective registers, which Section 10 ties back to topics._

---

## 9. Temporal Analysis

Message timestamps (2020–2025) let us track how structure and tone evolve.

### Community activity over time

![Monthly activity by community](figures/final_report/temporal_community_activity.png)

_Communities rise and fall at different times — activity is event-driven, not steady, and leadership of the conversation shifts between groups._

### Emotion over time

![Monthly emotion composition](figures/final_report/temporal_emotion_share.png)

_The emotional mix is not stable: periods of elevated anger/fear alternate with calmer trust/anticipation phases, suggesting reactive responses to external events._

### Emotion shift, quarterly

The monthly area chart shows churn but hides direction. Aggregating to quarters and drawing each emotion as its own line makes net rises and falls explicit.

![Emotion share by quarter](figures/final_report/temporal_emotion_quarterly.png)

Comparing the first 12 months of activity with the last 12: **trust fell 1.8 pp, fear rose 1.6 pp** (largest movers). Full breakdown:

| emotion      |   early % |   late % |   change (pp) |
|:-------------|----------:|---------:|--------------:|
| trust        |      19.5 |     17.7 |          -1.8 |
| fear         |      12.9 |     14.5 |           1.6 |
| anticipation |      15.7 |     16.9 |           1.1 |
| anger        |      19.1 |     18.4 |          -0.7 |
| sadness      |       6.7 |      6.0 |          -0.7 |
| disgust      |       3.2 |      3.5 |           0.3 |
| joy          |       2.7 |      2.6 |          -0.1 |
| surprise     |       1.2 |      1.2 |          -0.0 |

_What this answers: beyond month-to-month noise, the corpus shows a directional emotional drift — some registers structurally gain ground while others recede._

### Sentiment volatility by community

Standard deviation of monthly net polarity (positive − negative) measures emotional stability: high values = volatile mood, low = consistent tone.

| community   |   net_polarity_volatility |   mean_net_polarity |
|:------------|--------------------------:|--------------------:|
| C7          |                    0.5228 |             -0.1135 |
| C10         |                    0.5095 |              0.1873 |
| C8          |                    0.4597 |              0.4077 |
| C11         |                    0.4492 |              0.1537 |
| C5          |                    0.3534 |              0.0414 |
| C9          |                    0.2781 |              0.3713 |
| C6          |                    0.2342 |              0.0523 |
| C1          |                    0.1967 |              0.0400 |
| C3          |                    0.1578 |             -0.0299 |
| C4          |                    0.1538 |             -0.0154 |
| C2          |                    0.1407 |              0.0813 |
| C0          |                    0.0865 |             -0.0237 |

_What this answers: some communities keep a stable emotional profile while others swing sharply — the volatile ones are the most reactive to events._

---

## 10. Cross-Layer Analysis

Combining the four layers exposes relationships no single layer shows.

### Emotion × Topic

![Dominant emotion by topic](figures/final_report/crosslayer_emotion_by_topic.png)

_Topics carry distinct emotional signatures — some narratives are reliably anger-driven, others fear- or trust-driven, regardless of which community posts them._

### Community-level correlations

> **Caveat:** each correlation below is over only **n = 12 communities**, so the 95% confidence intervals are wide. Read these as directional, not precise.

![Community metric correlations](figures/final_report/crosslayer_correlation.png)

![Community size vs distinct topic count](figures/final_report/crosslayer_size_vs_diversity.png)

**Does size drive thematic diversity? Only as an artifact.**

- Volume vs distinct topic *count*: **r = 0.83** (95% CI 0.48–0.95). But a topic *count* mechanically grows with sample size (rarefaction): more messages hit more topic buckets.
- Volume vs **topics per 1k messages**: **r = -0.81** (95% CI -0.95–-0.44) — the sign **flips**. Normalized for size, larger communities are *less* diverse per message, not more.
- Volume vs topic **evenness** (Pielou): **r = -0.21** — essentially flat. Diversity of the topic *mix* is unrelated to how active a community is.
- Negative polarity vs internal similarity: **r = -0.11** — emotional negativity and content redundancy look largely independent (but see the n caveat).

_What this answers: the headline 'bigger communities are more diverse' is a sampling artifact — once you divide by message volume it reverses. Emotion aligns with topic far more than with raw community size._

---

## 11. Statistical Summary

Descriptive statistics across the 12 communities (each community is one observation). This quantifies the imbalance described qualitatively above.

| metric        |    mean |     std |   min |   median |     max |
|:--------------|--------:|--------:|------:|---------:|--------:|
| channels      |   38.58 |   30.73 |  2.00 |    42.50 |   79.00 |
| messages      | 2680.17 | 3023.76 | 40.00 |  1144.50 | 8424.00 |
| users         |  512.42 | 1194.29 |  1.00 |    56.00 | 4214.00 |
| topic_count   |  106.00 |   63.32 | 18.00 |   129.00 |  166.00 |
| topics_per_1k |  228.51 |  215.50 | 24.33 |   161.77 |  593.75 |
| evenness      |    0.85 |    0.04 |  0.79 |     0.85 |    0.89 |
| avg_sim       |    0.78 |    0.25 |  0.00 |     0.85 |    0.88 |
| net_polarity  |    0.08 |    0.15 | -0.10 |     0.04 |    0.37 |

> With **n = 12**, community-level summaries and correlations are low-power: standard deviations are large and any single community can move a statistic. The figures describe *this* corpus; they do not support strong population-level claims.

_Large standard deviations relative to means (especially for messages and users) confirm a heavy-tailed structure: a few communities dominate raw volume. Note the split in the diversity metrics — the distinct-topic *count* is heavy-tailed, but evenness (the size-normalized mix) is tight, underlining that 'breadth' is mostly a volume effect._

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

### 3. Communities have distinct thematic identities
- **Evidence:** 10 communities carry topics over-represented vs the corpus (lift up to ×44) — e.g. anti-vaccine, alternative-medicine, geopolitical, and religious-extremist clusters.
- **Interpretation:** Beneath a few globally-popular topics, the groups specialise in recognisable misinformation genres — visible via lift, hidden by the raw modal topic.
- **Supported by:** V2 / Phase 2

### 4. Narratives are also reused across communities
- **Evidence:** 57.7% of 8,926 near-duplicate pairs cross community lines.
- **Interpretation:** Distinct identities coexist with shared templates: the same content is repackaged across structurally separate groups — consistent with coordinated diffusion.
- **Supported by:** V2 / Phases 2 & 3

### 5. Tone is neutral-heavy with a mild negative lean
- **Evidence:** `neutral` is the plurality (22.5%); among non-neutral messages 'anger' leads and mean negative polarity (0.44) marginally exceeds positive (0.42).
- **Interpretation:** Affective framing skews to anger/fear when present, but most messages carry no lexicon emotion — the negative lean is real but modest.
- **Supported by:** V2 / Phase 4

### 6. Topic diversity is a sample-size artifact, not a real effect
- **Evidence:** Distinct-topic count rises with volume, but topics-per-message *falls* (r = -0.81) and evenness is flat.
- **Interpretation:** Larger communities are not more thematically diverse once normalized for activity; the raw count correlation is rarefaction.
- **Supported by:** V2 / Cross-layer

### 7. Topic noise was a clustering artifact, now controlled
- **Evidence:** Default HDBSCAN flagged ~48% of messages as outliers though they are not shorter than clustered ones; reassignment leaves a 9.0% residual.
- **Interpretation:** The original noise rate reflected default parameters on short text, not data quality; reassigned outliers are lower-confidence and flagged as such.
- **Supported by:** V2 / Phase 2

---

## 13. Limitations

- **Outlier reassignment.** Default HDBSCAN flags ~48% of messages as outliers; we reassign those above an embedding-cosine floor to their nearest topic, leaving a 9.0% residual. Reassigned messages are lower-confidence (low assignment probability) and should be read as best-fit, not firm, topic membership.
- **Low statistical power (n = 12).** Community-level statistics and correlations rest on twelve observations; confidence intervals are wide and individual communities can swing a coefficient.
- **Lexicon emotion.** NRC is a bag-of-words lexicon: it misses negation, sarcasm, irony, and context, and Portuguese coverage is imperfect; `neutral` (no match) is the largest class. Scores are indicative, not ground truth.
- **Language detection.** Non-Portuguese messages are dropped via langdetect before modeling, which is itself imperfect on very short text.
- **Community detection scope.** Communities are detected on the channel interaction graph only; users and messages inherit a community via their channel.
- **Similarity truncation.** `SIMILAR_TO` keeps only pairs ≥ 0.80 with top-5 neighbours, so redundancy counts are lower bounds.
- **Incomplete reply/forward recovery.** Many reply/forward sources are external or unrecovered, so cross-channel structure is partially observed.
- **Descriptive keywords ≠ topics.** Per-community keywords (Phase 1) are TF-IDF descriptors, not the formal BERTopic topics of Phase 2.

---

## Appendix

### A1. All communities

| community   |   channels |   messages |   users |   topics | dominant_emotion   | keywords                                                 |
|:------------|-----------:|-----------:|--------:|---------:|:-------------------|:---------------------------------------------------------|
| C0          |         79 |       7085 |      60 |      165 | anger              | apocalipserd · estão · contra · mundo · sobre            |
| C1          |         78 |       1706 |     372 |      146 | trust              | canal · nosso · covid · pessoas · vacina                 |
| C2          |         67 |       4642 |      89 |      162 | trust              | trump · presidente · sobre · estão · gefaziobreakingnews |
| C3          |         63 |       4562 |     840 |      166 | anger              | vacina · covid · contra · vacinas · sobre                |
| C4          |         57 |       8424 |    4214 |      164 | anticipation       | vacina · só · pessoas · quem · estão                     |
| C5          |         44 |        583 |       6 |      112 | trust              | inscreva · oráculo · nacionalista · canal · nosso        |
| C6          |         41 |       4450 |     472 |      164 | anger              | sobre · contra · estão · brasil · lula                   |
| C7          |         24 |        417 |      41 |       83 | anger              | israel · deuxxxsss · nazarena · yhwh · verdades          |
| C8          |          3 |         40 |       1 |       19 | anticipation       | live · hoje · pode · vocês · off                         |
| C9          |          3 |         87 |       1 |       33 | trust              | simões · info · daniel · canal · saúde                   |
| C10         |          2 |        121 |      52 |       40 | trust              | mms · cds · desparasitação · corpo · boa                 |
| C11         |          2 |         45 |       1 |       18 | anticipation       | água · cada · dia · sal · suco                           |

### A2. Full emotion-share matrix by community

| community   |   anger |   anticipation |   disgust |   fear |   joy |   sadness |   surprise |   trust |   neutral |
|:------------|--------:|---------------:|----------:|-------:|------:|----------:|-----------:|--------:|----------:|
| C0          |   0.215 |          0.155 |     0.030 |  0.155 | 0.026 |     0.058 |      0.011 |   0.166 |     0.186 |
| C1          |   0.151 |          0.140 |     0.037 |  0.102 | 0.019 |     0.081 |      0.010 |   0.230 |     0.230 |
| C2          |   0.161 |          0.169 |     0.026 |  0.123 | 0.034 |     0.059 |      0.010 |   0.235 |     0.183 |
| C3          |   0.190 |          0.154 |     0.046 |  0.142 | 0.022 |     0.064 |      0.012 |   0.153 |     0.217 |
| C4          |   0.143 |          0.157 |     0.038 |  0.104 | 0.033 |     0.068 |      0.016 |   0.133 |     0.309 |
| C5          |   0.178 |          0.160 |     0.041 |  0.110 | 0.019 |     0.062 |      0.007 |   0.302 |     0.122 |
| C6          |   0.196 |          0.165 |     0.029 |  0.142 | 0.021 |     0.063 |      0.014 |   0.180 |     0.191 |
| C7          |   0.211 |          0.144 |     0.086 |  0.106 | 0.024 |     0.043 |      0.014 |   0.127 |     0.245 |
| C8          |   0.050 |          0.375 |     0.025 |  0.025 | 0.000 |     0.025 |      0.000 |   0.200 |     0.300 |
| C9          |   0.069 |          0.184 |     0.011 |  0.069 | 0.000 |     0.057 |      0.000 |   0.575 |     0.034 |
| C10         |   0.116 |          0.124 |     0.033 |  0.058 | 0.033 |     0.058 |      0.000 |   0.190 |     0.388 |
| C11         |   0.156 |          0.200 |     0.111 |  0.111 | 0.111 |     0.067 |      0.000 |   0.133 |     0.111 |

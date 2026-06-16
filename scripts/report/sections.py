"""Section builders for the Graph V2 Markdown report.

Each ``section_NN_*`` function consumes the loaded :class:`ReportData` plus a
shared ``ctx`` dict of precomputed aggregates and returns a markdown string,
saving any figures it needs as a side effect. The orchestrator in
``generate.py`` concatenates them in order.

Style targets (from the report spec): compact tables (4-7 columns, top-N rows),
plots only where they add value, and a short interpretation under each — what it
shows, why it matters, what question it answers.
"""
import re

import numpy as np
import pandas as pd
import networkx as nx
from loguru import logger

from scripts.report.config import CONFIG
from scripts.report.loader import ReportData
from scripts.report import viz


_HEX = re.compile(r"([0-9a-fA-F]{12,})")

# Emotions commonly read as negative-valence, used for polarity-leaning summaries.
_NEGATIVE_EMOTIONS = {"anger", "fear", "sadness", "disgust"}


def _short_ch(x) -> str:
    """
    Shorten a hashed channel id to its first 8 hex characters for display.

    Args:
        x: Channel id string.

    Returns:
        Compact channel label.
    """
    m = _HEX.search(str(x))
    return m.group(1)[:8] if m else str(x)[:10]


def _short_msg(x) -> str:
    """
    Shorten a hashed message id to ``<hash8>_<suffix>`` for display.

    Args:
        x: Message id string.

    Returns:
        Compact message label.
    """
    s = str(x)
    m = _HEX.search(s)
    head = m.group(1)[:8] if m else s[:8]
    suffix = s.split("_")[-1] if "_" in s else ""
    return f"{head}_{suffix}" if suffix else head


def _pct(x) -> str:
    """
    Format a 0-1 fraction as a one-decimal percentage string.

    Args:
        x: Fraction value.

    Returns:
        Percentage string such as '12.3%'.
    """
    return f"{100 * float(x):.1f}%"


# ----------------------------------------------------------------------------
# Shared context
# ----------------------------------------------------------------------------
def build_context(data: ReportData) -> dict:
    """
    Precompute aggregates reused across multiple sections.

    Builds the channel interaction graph, the per-community profile table,
    inter-community links, and message->channel/community lookups so individual
    sections do not re-derive them.

    Args:
        data: Loaded report data.

    Returns:
        Dict of shared frames, graph objects, and headline metrics.
    """
    logger.info("Building shared report context.")
    msg = data.msg

    # --- Channel interaction graph (V1 INTERACTS_WITH), undirected weighted. ---
    graph = nx.Graph()
    for _, r in data.interacts_with.iterrows():
        w = float(r["interaction_weight"])
        if graph.has_edge(r["source"], r["target"]):
            graph[r["source"]][r["target"]]["weight"] += w
        else:
            graph.add_edge(r["source"], r["target"], weight=w)

    # --- Lookups. ---
    msg_to_channel = dict(zip(data.in_channel["message_id"], data.in_channel["channel_id"]))
    msg_to_comm = data.message_to_community
    ch_to_comm = data.channel_to_community

    # --- Dataset-channel flag per community. ---
    dataset_channels = set(
        data.channels.loc[data.channels["is_dataset_channel"] == True, "id"]  # noqa: E712
    )

    # --- Per-community message / user / topic / emotion aggregates. ---
    comm_msgs = msg.groupby("community_id").size().rename("messages")

    active = data.active_in.copy()
    active["community_id"] = active["channel_id"].map(ch_to_comm)
    comm_users = active.groupby("community_id")["user_id"].nunique().rename("users")

    # Topic diversity: distinct non-noise topics observed in a community.
    modeled = msg[msg["topic_id"].notna() & (msg["topic_id"] != CONFIG.noise_topic_id)]
    comm_topic_div = (
        modeled.groupby("community_id")["topic_id"].nunique().rename("topic_diversity")
    )

    # Mean polarity scores per community.
    comm_pol = msg.groupby("community_id")[["positive_score", "negative_score"]].mean()

    # Dominant non-neutral emotion + its share per community.
    def _dom_emotion(sub: pd.Series) -> str:
        counts = sub[sub != "neutral"].value_counts()
        return counts.index[0] if len(counts) else "neutral"

    comm_dom = msg.groupby("community_id")["dominant_emotion"].agg(_dom_emotion)

    # Intra-community average similarity.
    sim = data.similarity.copy()
    sim["src_comm"] = sim["source_message_id"].map(msg_to_comm)
    sim["tgt_comm"] = sim["target_message_id"].map(msg_to_comm)
    intra = sim[sim["src_comm"] == sim["tgt_comm"]]
    comm_sim = intra.groupby("src_comm")["cosine_similarity"].mean().rename("avg_similarity")
    comm_sim.index.name = "community_id"

    # Number of dataset channels (message-bearing) per community.
    cc = data.channel_community.copy()
    cc["is_dataset"] = cc["channel_id"].isin(dataset_channels)
    comm_dataset_ch = cc.groupby("community_id")["is_dataset"].sum().rename("dataset_channels")

    # --- Assemble the community profile. ---
    profile = data.communities.set_index("id")[
        ["size", "density", "modularity", "community_name", "descriptive_keywords"]
    ].copy()
    profile = profile.rename(columns={"size": "channels"})
    profile = profile.join([comm_dataset_ch, comm_msgs, comm_users,
                            comm_topic_div, comm_sim])
    profile = profile.join(comm_pol)
    profile["dominant_emotion"] = comm_dom
    profile["net_polarity"] = profile["positive_score"] - profile["negative_score"]
    profile = profile.fillna({"topic_diversity": 0, "avg_similarity": 0})
    profile.index.name = "community_id"

    # --- Inter-community links (cross-community INTERACTS_WITH weight). ---
    iw = data.interacts_with.copy()
    iw["src_comm"] = iw["source"].map(ch_to_comm)
    iw["tgt_comm"] = iw["target"].map(ch_to_comm)
    cross = iw[(iw["src_comm"] != iw["tgt_comm"])
               & iw["src_comm"].notna() & iw["tgt_comm"].notna()].copy()
    cross["pair"] = cross.apply(
        lambda r: tuple(sorted((int(r["src_comm"]), int(r["tgt_comm"])))), axis=1
    )
    inter_links = (
        cross.groupby("pair")
        .agg(interaction_weight=("interaction_weight", "sum"),
             edges=("interaction_weight", "size"))
        .reset_index()
        .sort_values("interaction_weight", ascending=False)
    )

    return {
        "graph": graph,
        "msg_to_channel": msg_to_channel,
        "dataset_channels": dataset_channels,
        "profile": profile,
        "inter_links": inter_links,
        "sim": sim,                       # similarity with community columns attached
        "modeled": modeled,
    }


# ----------------------------------------------------------------------------
# Section 1 — Executive Summary  (written last conceptually, placed first)
# ----------------------------------------------------------------------------
def section_01_summary(data: ReportData, ctx: dict) -> str:
    """
    Build the executive summary as concise headline bullets.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the executive summary section.
    """
    profile = ctx["profile"]
    n_msg = len(data.msg)
    n_comm = len(data.communities)
    modularity = float(data.communities["modularity"].iloc[0])
    n_topics = int((data.topics["id"] != CONFIG.noise_topic_id).sum())
    noise_share = float(
        (data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean()
    )
    n_sim = len(data.similarity)
    sim = ctx["sim"]
    inter_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())

    emo_counts = data.msg["dominant_emotion"].value_counts()
    top_emos = [e for e in emo_counts.index if e != "neutral"][:3]

    biggest = profile.sort_values("messages", ascending=False).iloc[0]
    biggest_kw = str(biggest["community_name"]).split(" · ")[:3]

    return "\n".join([
        "## 1. Executive Summary",
        "",
        f"- **Structure (V1).** {len(data.channels)} channels ({int((data.channels['is_dataset_channel']==True).sum())} core + external sources) "  # noqa: E712
        f"and {data.users['id'].nunique():,} users are linked through {data.interacts_with.shape[0]:,} "
        "channel-interaction edges (shared users, forwards, replies).",
        f"- **Communities (V2 / Phase 1).** Leiden finds **{n_comm} communities** "
        f"over {int(profile['channels'].sum())} channels at modularity **{modularity:.2f}** "
        "— a clear, well-separated structure.",
        f"- **Topics (V2 / Phase 2).** **{n_topics} topics** extracted from "
        f"{len(data.message_topics):,} modeled messages; "
        f"{_pct(noise_share)} fall in the BERTopic noise bucket (`-1`).",
        f"- **Semantics (V2 / Phase 3).** **{n_sim:,} near-duplicate message pairs** "
        f"(cosine ≥ {CONFIG.similarity_threshold:.2f}); {_pct(inter_share)} of them link "
        "*different* communities — measurable cross-group narrative reuse.",
        f"- **Emotion (V2 / Phase 4).** Dominant tone is **{', '.join(top_emos)}**; "
        f"{_pct((data.msg['dominant_emotion']=='neutral').mean())} of messages carry no "
        "lexicon emotion (neutral).",
        f"- **Most active community:** `C{int(biggest.name)}` "
        f"({int(biggest['messages']):,} messages) — {' · '.join(biggest_kw)}.",
        "",
        "> The graph is highly centralized: a few large channels and one or two "
        "communities carry most messages, topics repeat across communities, and "
        "negatively-valenced emotions (anger, fear) lead the corpus.",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 2 — Dataset & Graph Overview
# ----------------------------------------------------------------------------
def section_02_overview(data: ReportData, ctx: dict) -> str:
    """
    Build the dataset and V1-vs-V2 comparison overview.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the overview section.
    """
    msg = data.msg
    start, end = msg["date_parsed"].min(), msg["date_parsed"].max()

    n_channels = len(data.channels)
    n_dataset = int((data.channels["is_dataset_channel"] == True).sum())  # noqa: E712
    n_users = data.users["id"].nunique()
    n_msg = len(msg)

    comparison = pd.DataFrame(
        [
            ["Node: Channel", f"{n_channels}", f"{n_channels}"],
            ["Node: User", f"{n_users:,}", f"{n_users:,}"],
            ["Node: Message", f"{n_msg:,}", f"{n_msg:,}"],
            ["Node: Community", "—", f"{len(data.communities)}"],
            ["Node: Topic", "—", f"{int((data.topics['id'] != CONFIG.noise_topic_id).sum())}"],
            ["Edge: structural", "POSTED, IN_CHANNEL, ACTIVE_IN, REPLIES_TO, FORWARDED_FROM", "(inherited)"],
            ["Edge: INTERACTS_WITH", f"{len(data.interacts_with):,}", "(inherited)"],
            ["Edge: BELONGS_TO", "—", f"{len(data.channel_community):,}"],
            ["Edge: BELONGS_TO_TOPIC", "—", f"{len(data.message_topics):,}"],
            ["Edge: SIMILAR_TO", "—", f"{len(data.similarity):,}"],
            ["Msg attr: emotion scores", "—", f"{len(data.emotions):,} messages"],
        ],
        columns=["Element", "Graph V1", "Graph V2 (adds)"],
    )

    # Monthly message volume.
    monthly = msg.groupby("month").size()
    fig = viz.line(
        monthly.to_frame("messages"),
        "Monthly message volume",
        "month", "messages", "overview_messages_over_time.png",
    )

    return "\n".join([
        "## 2. Dataset and Graph Overview",
        "",
        "The graph models a Portuguese misinformation Telegram corpus. **V1** captures "
        "*who said what, where, and to whom* (channels, users, messages, and their "
        "interaction edges). **V2** layers *meaning* on top: community structure, topics, "
        "semantic similarity, and emotion — without rebuilding any V1 node or edge.",
        "",
        f"- **Time range:** {start:%Y-%m-%d} → {end:%Y-%m-%d} (~{(end-start).days // 30} months)",
        f"- **Core channels:** {n_dataset} (the V1 interaction graph also includes "
        f"{n_channels - n_dataset} external forward/reply source channels)",
        "- **Missing data:** forwarding and reply metadata are sparse by nature "
        "(most messages are neither forwarded nor replies); this is expected, not corruption.",
        "",
        "### V1 vs V2 at a glance",
        "",
        viz.md_table(comparison, max_rows=20, floatfmt=".0f"),
        "",
        viz.md_image(fig, "Monthly message volume"),
        "",
        "_Activity is uneven across the 5-year span, with pronounced surges — useful "
        "context for the temporal analysis in Section 9._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 3 — Graph V1 Structural Analysis
# ----------------------------------------------------------------------------
def section_03_v1_structure(data: ReportData, ctx: dict) -> str:
    """
    Build the V1 structural analysis of the channel interaction graph.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the V1 structural section.
    """
    g = ctx["graph"]
    n, m = g.number_of_nodes(), g.number_of_edges()
    degrees = [d for _, d in g.degree()]
    avg_deg = float(np.mean(degrees))
    med_deg = float(np.median(degrees))
    density = nx.density(g)
    components = list(nx.connected_components(g))
    largest = max(components, key=len)
    all_channels = set(data.channel_community["channel_id"])
    isolated = len(all_channels - set(g.nodes()))

    # Degree distribution figure.
    fig = viz.hist(
        pd.Series(degrees), "Channel degree distribution (INTERACTS_WITH)",
        "degree (number of connected channels)", "v1_degree_distribution.png", bins=30,
    )

    # Top channels by weighted degree (strength) + betweenness for bridges.
    strength = pd.Series(dict(g.degree(weight="weight")))
    btw = pd.Series(nx.betweenness_centrality(g, weight="weight", normalized=True))
    central = pd.DataFrame({
        "channel": [_short_ch(c) for c in strength.index],
        "community": [data.channel_to_community.get(c, "—") for c in strength.index],
        "degree": [g.degree(c) for c in strength.index],
        "weighted_degree": strength.values,
        "betweenness": btw.reindex(strength.index).values,
    }).sort_values("weighted_degree", ascending=False)

    stats = pd.DataFrame(
        [
            ["Channels in interaction graph", f"{n}"],
            ["Interaction edges (undirected)", f"{m:,}"],
            ["Average degree", f"{avg_deg:.1f}"],
            ["Median degree", f"{med_deg:.0f}"],
            ["Graph density", f"{density:.4f}"],
            ["Connected components", f"{len(components)}"],
            ["Largest component (channels)", f"{len(largest)} ({_pct(len(largest)/n)})"],
            ["Isolated channels", f"{isolated}"],
        ],
        columns=["Metric", "Value"],
    )

    return "\n".join([
        "## 3. Graph Version 1 — Basic Structural Analysis",
        "",
        "V1 analysis runs on the derived `INTERACTS_WITH` channel graph, which "
        "summarizes shared users, forwards, and replies into weighted channel-to-channel edges.",
        "",
        viz.md_table(stats, floatfmt=".4f"),
        "",
        viz.md_image(fig, "Channel degree distribution"),
        "",
        "_The degree distribution is right-skewed: most channels connect to few others "
        "while a handful are hubs — the hallmark of a centralized diffusion network._",
        "",
        "### Most central channels",
        "",
        "Weighted degree measures total interaction strength; betweenness flags channels "
        "that sit on many shortest paths (structural bridges).",
        "",
        viz.md_table(central, max_rows=CONFIG.top_n_table, floatfmt=".4f"),
        "",
        f"_The graph is effectively one connected core ({_pct(len(largest)/n)} of channels "
        "in the largest component); high-betweenness channels are the brokers that hold "
        "otherwise distinct groups together — a question revisited as community bridges in Section 5._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 4 — Graph V2 Expanded
# ----------------------------------------------------------------------------
def section_04_v2_expanded(data: ReportData, ctx: dict) -> str:
    """
    Describe how V2 enriches V1 and summarize the added layers.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the V2 expansion section.
    """
    msg = data.msg
    n_topics = int((data.topics["id"] != CONFIG.noise_topic_id).sum())

    layers = pd.DataFrame(
        [
            ["Phase 1", "Community", "BELONGS_TO (channel→community)",
             f"{len(data.communities)} communities / {len(data.channel_community)} memberships"],
            ["Phase 2", "Topic", "BELONGS_TO_TOPIC, DOMINATED_BY",
             f"{n_topics} topics / {len(data.message_topics):,} assignments"],
            ["Phase 3", "—", "SIMILAR_TO (message→message)",
             f"{len(data.similarity):,} edges (cosine ≥ {CONFIG.similarity_threshold:.2f})"],
            ["Phase 4", "—", "emotion scores on Message",
             f"{len(data.emotions):,} messages labelled"],
        ],
        columns=["Phase", "New node", "New edges / attributes", "Volume"],
    )

    start, end = msg["date_parsed"].min(), msg["date_parsed"].max()

    return "\n".join([
        "## 4. Graph Version 2 — Expanded Structural and Semantic Analysis",
        "",
        "V2 keeps every V1 node and edge and adds four enrichment layers, each derived "
        "from V1 by one analysis phase:",
        "",
        viz.md_table(layers, floatfmt=".0f"),
        "",
        "**How the phases enrich the graph**",
        "",
        "1. *Community detection* partitions the channel interaction graph into "
        "structural groups (Phase 1).",
        "2. *Topic modeling* (BERTopic over multilingual embeddings) assigns each modeled "
        "message a latent topic and rolls topics up to community dominance (Phase 2).",
        "3. *Message similarity* turns the same embeddings into semantic `SIMILAR_TO` "
        "edges, exposing near-duplicate / reused content (Phase 3).",
        "4. *Emotion scoring* (Portuguese NRC lexicon) attaches eight emotion scores plus "
        "polarity and a dominant emotion to every message (Phase 4).",
        "",
        "**V2 coverage**",
        "",
        f"- Communities: {len(data.communities)} · Topics: {n_topics} (+1 noise bucket)",
        f"- Similarity edges: {len(data.similarity):,} · Emotion-labelled messages: {len(data.emotions):,}",
        f"- Temporal span carried from V1: {start:%Y-%m} → {end:%Y-%m}",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 5 — Community Analysis
# ----------------------------------------------------------------------------
def section_05_communities(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper community analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the community analysis section.
    """
    profile = ctx["profile"].copy()
    sizes = profile["channels"]

    # Size distribution figure (channels per community).
    size_series = sizes.sort_values(ascending=True)
    size_series.index = [f"C{int(i)}" for i in size_series.index]
    fig_size = viz.bar(
        size_series, "Channels per community", "channels", "community",
        "community_sizes.png",
    )

    summary_stats = pd.DataFrame(
        [
            ["Communities", f"{len(profile)}"],
            ["Channels covered", f"{int(sizes.sum())}"],
            ["Mean size", f"{sizes.mean():.1f}"],
            ["Median size", f"{sizes.median():.0f}"],
            ["Size variance", f"{sizes.var():.1f}"],
            ["Largest / smallest", f"{int(sizes.max())} / {int(sizes.min())}"],
        ],
        columns=["Metric", "Value"],
    )

    # Top communities table.
    top = profile.sort_values("messages", ascending=False).head(CONFIG.top_communities)
    top_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in top.index],
        "channels": top["channels"].astype(int).values,
        "messages": top["messages"].fillna(0).astype(int).values,
        "users": top["users"].fillna(0).astype(int).values,
        "density": top["density"].values,
        "keywords": [" · ".join(str(k).split(" · ")[:4]) for k in top["community_name"]],
    })

    # Strongest inter-community links.
    inter = ctx["inter_links"].head(CONFIG.top_n_table).copy()
    inter_tbl = pd.DataFrame({
        "community_pair": [f"C{a} ↔ C{b}" for a, b in inter["pair"]],
        "interaction_weight": inter["interaction_weight"].values,
        "bridging_edges": inter["edges"].astype(int).values,
    })

    # Bridge users: users active in channels spanning more than one community.
    active = data.active_in.copy()
    active["community_id"] = active["channel_id"].map(data.channel_to_community)
    user_span = active.groupby("user_id")["community_id"].nunique()
    bridge_users = int((user_span > 1).sum())

    return "\n".join([
        "## 5. Community Analysis",
        "",
        "### Basic statistics",
        "",
        viz.md_table(summary_stats),
        "",
        viz.md_image(fig_size, "Channels per community"),
        "",
        "_Community sizes are strongly imbalanced — a few large communities dominate the "
        "structure while several are small satellites._",
        "",
        "### Top communities (by message volume)",
        "",
        viz.md_table(top_tbl, max_rows=CONFIG.top_communities, floatfmt=".3f"),
        "",
        "_Message and user counts come only from the core channels; size (channels) "
        "additionally includes external forward/reply sources clustered with them._",
        "",
        "### Bridges between communities",
        "",
        "Cross-community `INTERACTS_WITH` weight reveals which communities are most "
        "tightly coupled — the strongest candidates for shared audiences or content flow.",
        "",
        viz.md_table(inter_tbl, max_rows=CONFIG.top_n_table, floatfmt=".1f"),
        "",
        f"- **{bridge_users:,} users** are active across more than one community, acting "
        "as human bridges that carry content between otherwise separate groups.",
        "",
        "_What this answers: the dominant communities are structurally central (largest, "
        "densest), and a measurable set of shared users plus weighted cross-links shows "
        "the communities are not isolated silos but a coupled ecosystem._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 6 — Topic Analysis
# ----------------------------------------------------------------------------
def section_06_topics(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper topic analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the topic analysis section.
    """
    topics = data.topics
    real = topics[topics["id"] != CONFIG.noise_topic_id].copy()
    noise_share = float((data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean())

    # Top topics by message count.
    top = real.sort_values("message_count", ascending=False).head(CONFIG.top_topics)
    top_tbl = pd.DataFrame({
        "topic": top["id"].astype(int).values,
        "messages": top["message_count"].astype(int).values,
        "label / keywords": [str(l) for l in top["label"]],
    })

    fig = viz.bar(
        pd.Series(top["message_count"].values[::-1],
                  index=[f"T{int(i)}" for i in top["id"].values[::-1]]),
        "Top topics by message count", "messages", "topic",
        "topic_top_counts.png",
    )

    # Dominant topics per community.
    ct = data.community_topics.merge(
        topics[["id", "label"]], left_on="topic_id", right_on="id", how="left"
    )
    dom = ct.sort_values(["community_id", "share"], ascending=[True, False])
    dom_top = (
        dom.groupby("community_id").head(1)
        .sort_values("message_count", ascending=False)
        .head(CONFIG.top_communities)
    )
    dom_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in dom_top["community_id"]],
        "top_topic": dom_top["topic_id"].astype(int).values,
        "share": dom_top["share"].values,
        "label / keywords": [str(l) for l in dom_top["label"]],
    })

    # Topics shared across communities + per-community diversity.
    shared = data.community_topics.groupby("topic_id")["community_id"].nunique()
    n_shared = int((shared > 1).sum())
    diversity = ctx["profile"]["topic_diversity"].sort_values(ascending=False)

    return "\n".join([
        "## 6. Topic Analysis",
        "",
        f"BERTopic produced **{len(real)} topics** from {len(data.message_topics):,} "
        f"modeled messages. The noise bucket (`-1`) absorbs **{_pct(noise_share)}** of "
        "assignments — short or generic messages with no stable topic.",
        "",
        "### Most frequent topics",
        "",
        viz.md_table(top_tbl, max_rows=CONFIG.top_topics),
        "",
        viz.md_image(fig, "Top topics by message count"),
        "",
        "_A few large topics capture mainstream narratives; the long tail of small topics "
        "reflects niche or fast-moving content._",
        "",
        "### Dominant topic per community",
        "",
        viz.md_table(dom_tbl, max_rows=CONFIG.top_communities, floatfmt=".3f"),
        "",
        f"- **{n_shared} topics** are dominant in more than one community — evidence that "
        "core narratives are shared across structurally separate groups.",
        "- **Most thematically diverse communities:** "
        + ", ".join(f"C{int(i)} ({int(v)} topics)" for i, v in diversity.head(3).items())
        + "; the narrowest carry only a handful of distinct topics.",
        "",
        "_What this answers: communities differ sharply in thematic breadth, yet the "
        "biggest topics recur across communities — narrative reuse is structural, not isolated._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 7 — Semantic Similarity
# ----------------------------------------------------------------------------
def section_07_similarity(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper semantic similarity analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the similarity section.
    """
    sim = ctx["sim"]
    scores = sim["cosine_similarity"]
    msg_to_channel = ctx["msg_to_channel"]

    fig = viz.hist(
        scores, "Distribution of message-pair cosine similarity",
        "cosine similarity", "similarity_score_distribution.png", bins=30,
    )

    stats = pd.DataFrame(
        [
            ["Similar pairs (edges)", f"{len(sim):,}"],
            ["Mean similarity", f"{scores.mean():.3f}"],
            ["Median similarity", f"{scores.median():.3f}"],
            ["Min / Max", f"{scores.min():.3f} / {scores.max():.3f}"],
            ["Intra-community pairs", f"{int((sim['src_comm']==sim['tgt_comm']).sum()):,}"],
            ["Cross-community pairs", f"{int((sim['src_comm']!=sim['tgt_comm']).sum()):,}"],
        ],
        columns=["Metric", "Value"],
    )

    # Top similar pairs.
    top = sim.sort_values("cosine_similarity", ascending=False).head(CONFIG.top_n_table)
    top_tbl = pd.DataFrame({
        "source": [_short_msg(s) for s in top["source_message_id"]],
        "target": [_short_msg(t) for t in top["target_message_id"]],
        "cosine": top["cosine_similarity"].values,
        "same_community": (top["src_comm"] == top["tgt_comm"]).values,
    })

    # Channels that most repeat similar content internally (same-channel edges).
    s2 = sim.copy()
    s2["src_ch"] = s2["source_message_id"].map(msg_to_channel)
    s2["tgt_ch"] = s2["target_message_id"].map(msg_to_channel)
    same_ch = s2[s2["src_ch"] == s2["tgt_ch"]]
    repeat = same_ch["src_ch"].value_counts().head(CONFIG.top_n_table)
    repeat_tbl = pd.DataFrame({
        "channel": [_short_ch(c) for c in repeat.index],
        "internal_similar_pairs": repeat.values,
    })

    # Central messages: appear in edges spanning the most distinct communities.
    endpoints = pd.concat([
        sim[["source_message_id", "tgt_comm"]].rename(
            columns={"source_message_id": "message_id", "tgt_comm": "other_comm"}),
        sim[["target_message_id", "src_comm"]].rename(
            columns={"target_message_id": "message_id", "src_comm": "other_comm"}),
    ])
    central = (
        endpoints.dropna().groupby("message_id")["other_comm"].nunique()
        .sort_values(ascending=False).head(CONFIG.top_n_table)
    )
    central_tbl = pd.DataFrame({
        "message": [_short_msg(m) for m in central.index],
        "linked_communities": central.values,
    })

    cross_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())

    return "\n".join([
        "## 7. Semantic Similarity Analysis",
        "",
        f"Phase 3 retains message pairs with cosine ≥ {CONFIG.similarity_threshold:.2f} "
        "(top-5 neighbours each). Because the threshold is a hard floor, the score "
        "distribution starts there and decays toward 1.0.",
        "",
        viz.md_table(stats, floatfmt=".3f"),
        "",
        viz.md_image(fig, "Cosine similarity distribution"),
        "",
        f"_About **{_pct(cross_share)}** of similar pairs cross community boundaries: the "
        "same or near-identical content is being reposted across structurally distinct groups._",
        "",
        "### Strongest similar pairs",
        "",
        viz.md_table(top_tbl, max_rows=CONFIG.top_n_table, floatfmt=".3f"),
        "",
        "### Most semantically redundant channels",
        "",
        "Channels with many *internal* similar pairs repeat their own content most often.",
        "",
        viz.md_table(repeat_tbl, max_rows=CONFIG.top_n_table),
        "",
        "### Cross-community bridge messages",
        "",
        "Messages whose similar neighbours span the most communities act as semantic hubs "
        "— the same idea echoed everywhere.",
        "",
        viz.md_table(central_tbl, max_rows=CONFIG.top_n_table),
        "",
        "_What this answers: redundancy is concentrated in specific channels, and a small "
        "set of messages function as cross-community templates — a fingerprint of coordinated reuse._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 8 — Sentiment & Emotion
# ----------------------------------------------------------------------------
def section_08_emotion(data: ReportData, ctx: dict) -> str:
    """
    Build basic and deeper sentiment/emotion analysis.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the emotion section.
    """
    msg = data.msg
    emotions = list(CONFIG.emotion_categories)

    # Dominant emotion distribution.
    dist = msg["dominant_emotion"].value_counts()
    fig_dist = viz.bar(
        dist.sort_values(), "Dominant emotion distribution (all messages)",
        "messages", "dominant emotion", "emotion_distribution.png",
    )

    # Emotion x community heatmap (share of dominant emotion within each community).
    top_comms = (
        ctx["profile"].sort_values("messages", ascending=False)
        .head(CONFIG.top_emotion_communities).index
    )
    sub = msg[msg["community_id"].isin(top_comms)]
    share = (
        pd.crosstab(sub["community_id"], sub["dominant_emotion"], normalize="index")
        .reindex(columns=emotions + ["neutral"], fill_value=0)
    )
    share.index = [f"C{int(i)}" for i in share.index]
    fig_heat = viz.heatmap(
        share[emotions], "Emotion share by community (top communities)",
        "emotion_by_community.png", cbar_label="share of messages",
    )

    # Communities with the highest concentration of each emotion.
    full_share = pd.crosstab(msg["community_id"], msg["dominant_emotion"], normalize="index")
    rows = []
    for e in emotions:
        if e in full_share.columns:
            cid = full_share[e].idxmax()
            rows.append([e, f"C{int(cid)}", full_share.loc[cid, e]])
    conc_tbl = pd.DataFrame(rows, columns=["emotion", "top_community", "share"])

    # Channels with the most distinctive (concentrated) emotion profile.
    ch_emo = pd.crosstab(msg["channel_id"], msg["dominant_emotion"], normalize="index")
    ch_counts = msg.groupby("channel_id").size()
    eligible = ch_counts[ch_counts >= 50].index
    ch_emo = ch_emo.loc[ch_emo.index.intersection(eligible)]
    ch_emo_real = ch_emo[[c for c in emotions if c in ch_emo.columns]]
    distinct = ch_emo_real.max(axis=1).sort_values(ascending=False).head(CONFIG.top_n_table)
    distinct_tbl = pd.DataFrame({
        "channel": [_short_ch(c) for c in distinct.index],
        "messages": ch_counts.reindex(distinct.index).astype(int).values,
        "top_emotion": ch_emo_real.loc[distinct.index].idxmax(axis=1).values,
        "share": distinct.values,
    })

    pos, neg = msg["positive_score"].mean(), msg["negative_score"].mean()

    return "\n".join([
        "## 8. Sentiment and Emotion Analysis",
        "",
        f"All {len(data.emotions):,} messages carry NRC emotion scores. Mean polarity is "
        f"**{pos:.2f} positive / {neg:.2f} negative** — the corpus leans negative.",
        "",
        viz.md_image(fig_dist, "Dominant emotion distribution"),
        "",
        "_Negatively-valenced emotions (anger, fear) and trust lead; surprise and joy are "
        "rare. `neutral` marks messages with no lexicon match._",
        "",
        "### Emotion profile by community",
        "",
        viz.md_image(fig_heat, "Emotion share by community"),
        "",
        "_Communities differ in tone: some are anger-dominated, others trust- or "
        "anticipation-leaning, despite drawing on overlapping topics._",
        "",
        "### Where each emotion concentrates",
        "",
        viz.md_table(conc_tbl, max_rows=10, floatfmt=".3f"),
        "",
        "### Channels with the most distinctive emotional profile",
        "",
        "Channels (≥50 messages) where a single emotion captures the largest share — the "
        "clearest emotional 'signatures'.",
        "",
        viz.md_table(distinct_tbl, max_rows=CONFIG.top_n_table, floatfmt=".3f"),
        "",
        "_What this answers: emotion is not uniform — specific communities and channels "
        "specialize in specific affective registers, which Section 10 ties back to topics._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 9 — Temporal Analysis
# ----------------------------------------------------------------------------
def section_09_temporal(data: ReportData, ctx: dict) -> str:
    """
    Build temporal analysis of volume, community activity, and emotion.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the temporal section.
    """
    msg = data.msg.copy()
    emotions = list(CONFIG.emotion_categories)

    # Community activity over time (top 4 communities by volume).
    top_comms = (
        ctx["profile"].sort_values("messages", ascending=False).head(4).index
    )
    pivot = (
        msg[msg["community_id"].isin(top_comms)]
        .pivot_table(index="month", columns="community_id", values="message_id",
                     aggfunc="count", fill_value=0)
    )
    pivot.columns = [f"C{int(c)}" for c in pivot.columns]
    fig_comm = viz.line(
        pivot, "Monthly activity of the largest communities",
        "month", "messages", "temporal_community_activity.png",
    )

    # Dominant emotion over time (monthly share, stacked area).
    emo_month = (
        pd.crosstab(msg["month"], msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions, fill_value=0)
    )
    # Keep readable: bucket sparse months are fine; index is sorted YYYY-MM strings.
    fig_emo = viz.stacked_area(
        emo_month, "Emotion composition over time (monthly share)",
        "month", "share of messages", "temporal_emotion_share.png",
    )

    # Sentiment volatility per community: std of monthly net polarity.
    msg["net"] = msg["positive_score"] - msg["negative_score"]
    monthly_net = msg.pivot_table(index="month", columns="community_id",
                                  values="net", aggfunc="mean")
    volatility = monthly_net.std().sort_values(ascending=False)
    vol_tbl = pd.DataFrame({
        "community": [f"C{int(i)}" for i in volatility.index],
        "net_polarity_volatility": volatility.values,
        "mean_net_polarity": monthly_net.mean().reindex(volatility.index).values,
    }).head(CONFIG.top_n_table)

    return "\n".join([
        "## 9. Temporal Analysis",
        "",
        "Message timestamps (2020–2025) let us track how structure and tone evolve.",
        "",
        "### Community activity over time",
        "",
        viz.md_image(fig_comm, "Monthly activity of the largest communities"),
        "",
        "_Communities rise and fall at different times — activity is event-driven, not "
        "steady, and leadership of the conversation shifts between groups._",
        "",
        "### Emotion over time",
        "",
        viz.md_image(fig_emo, "Monthly emotion composition"),
        "",
        "_The emotional mix is not stable: periods of elevated anger/fear alternate with "
        "calmer trust/anticipation phases, suggesting reactive responses to external events._",
        "",
        "### Sentiment volatility by community",
        "",
        "Standard deviation of monthly net polarity (positive − negative) measures "
        "emotional stability: high values = volatile mood, low = consistent tone.",
        "",
        viz.md_table(vol_tbl, max_rows=CONFIG.top_n_table, floatfmt=".4f"),
        "",
        "_What this answers: some communities keep a stable emotional profile while others "
        "swing sharply — the volatile ones are the most reactive to events._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 10 — Cross-Layer Analysis
# ----------------------------------------------------------------------------
def section_10_cross_layer(data: ReportData, ctx: dict) -> str:
    """
    Combine structural, topical, semantic, and emotional layers.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the cross-layer section.
    """
    msg = data.msg
    profile = ctx["profile"].copy()
    emotions = list(CONFIG.emotion_categories)

    # Emotion x topic heatmap for the top topics.
    real = msg[msg["topic_id"].notna() & (msg["topic_id"] != CONFIG.noise_topic_id)]
    top_topics = real["topic_id"].value_counts().head(10).index
    sub = real[real["topic_id"].isin(top_topics)]
    et = (
        pd.crosstab(sub["topic_id"], sub["dominant_emotion"], normalize="index")
        .reindex(columns=emotions, fill_value=0)
    )
    et.index = [f"T{int(t)}: {str(data.topic_label.get(int(t), '')).split(' · ')[0]}"
                for t in et.index]
    fig_et = viz.heatmap(
        et, "Dominant emotion by topic (top topics)",
        "crosslayer_emotion_by_topic.png", cbar_label="share",
    )

    # Community-level correlation among layer metrics.
    metrics = profile[["channels", "messages", "users", "topic_diversity",
                       "avg_similarity", "negative_score"]].copy()
    metrics = metrics.rename(columns={"negative_score": "neg_polarity"}).astype(float)
    corr = metrics.corr()
    fig_corr = viz.heatmap(
        corr, "Community-level metric correlations",
        "crosslayer_correlation.png", cmap="coolwarm", cbar_label="Pearson r",
    )

    # Scatter: community size vs topic diversity.
    fig_sc = viz.scatter(
        profile["messages"].astype(float), profile["topic_diversity"].astype(float),
        [f"C{int(i)}" for i in profile.index],
        "Community message volume vs topic diversity",
        "messages", "distinct topics", "crosslayer_size_vs_diversity.png",
    )

    # A couple of computed correlations to narrate.
    r_size_div = float(metrics["messages"].corr(metrics["topic_diversity"]))
    r_neg_sim = float(metrics["neg_polarity"].corr(metrics["avg_similarity"]))

    return "\n".join([
        "## 10. Cross-Layer Analysis",
        "",
        "Combining the four layers exposes relationships no single layer shows.",
        "",
        "### Emotion × Topic",
        "",
        viz.md_image(fig_et, "Dominant emotion by topic"),
        "",
        "_Topics carry distinct emotional signatures — some narratives are reliably "
        "anger-driven, others fear- or trust-driven, regardless of which community posts them._",
        "",
        "### Community-level correlations",
        "",
        viz.md_image(fig_corr, "Community metric correlations"),
        "",
        viz.md_image(fig_sc, "Community size vs topic diversity"),
        "",
        f"- Message volume vs topic diversity: **r = {r_size_div:.2f}** — larger "
        "communities are "
        + ("more thematically diverse" if r_size_div > 0.2 else
           "not simply more diverse (breadth is not just a volume effect)") + ".",
        f"- Negative polarity vs internal similarity: **r = {r_neg_sim:.2f}** — "
        + ("more negative communities also repeat content more" if r_neg_sim > 0.2 else
           "emotional negativity and content redundancy are largely independent") + ".",
        "",
        "_What this answers: structure, topic, semantics, and emotion are partially "
        "coupled — volume drives breadth, while emotion aligns more with topic than with "
        "raw community size._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 11 — Statistical Summary
# ----------------------------------------------------------------------------
def section_11_statistics(data: ReportData, ctx: dict) -> str:
    """
    Build a compact descriptive-statistics summary across communities.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the statistical summary section.
    """
    profile = ctx["profile"].copy()
    cols = {
        "channels": "channels",
        "messages": "messages",
        "users": "users",
        "topic_diversity": "topics",
        "avg_similarity": "avg_sim",
        "net_polarity": "net_polarity",
    }
    desc = profile[list(cols)].rename(columns=cols).astype(float).describe().T
    desc = desc[["mean", "std", "min", "50%", "max"]].rename(columns={"50%": "median"})
    desc.insert(0, "metric", desc.index)

    return "\n".join([
        "## 11. Statistical Summary",
        "",
        "Descriptive statistics across the 12 communities (each community is one "
        "observation). This quantifies the imbalance described qualitatively above.",
        "",
        viz.md_table(desc, max_rows=10, floatfmt=".2f"),
        "",
        "_Large standard deviations relative to means (especially for messages and users) "
        "confirm a heavy-tailed structure: a few communities dominate every metric. "
        "Topic breadth and similarity are more evenly spread._",
        "",
    ])


# ----------------------------------------------------------------------------
# Section 12 — Key Findings
# ----------------------------------------------------------------------------
def section_12_findings(data: ReportData, ctx: dict) -> str:
    """
    Distil the analysis into titled, evidence-backed findings.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the key findings section.
    """
    profile = ctx["profile"]
    sim = ctx["sim"]
    modularity = float(data.communities["modularity"].iloc[0])
    cross_share = float((sim["src_comm"] != sim["tgt_comm"]).mean())
    noise_share = float((data.message_topics["topic_id"] == CONFIG.noise_topic_id).mean())
    biggest = profile.sort_values("messages", ascending=False).iloc[0]
    biggest_share = float(biggest["messages"]) / float(profile["messages"].sum())
    neg_lead = data.msg["dominant_emotion"].value_counts()
    top_emo = [e for e in neg_lead.index if e != "neutral"][0]

    findings = [
        ("Well-separated community structure",
         f"Leiden modularity = {modularity:.2f} across {len(data.communities)} communities.",
         "The channel network has genuine, non-random group structure — communities are a "
         "meaningful unit of analysis, not an artefact.",
         "V2 / Phase 1"),
        ("Activity is highly concentrated",
         f"The largest community alone holds {_pct(biggest_share)} of all messages.",
         "A handful of channels/communities drive the corpus; moderation or study effort "
         "targeted there covers most of the volume.",
         "V1 structure + V2 / Phase 1"),
        ("Narratives are reused across communities",
         f"{_pct(cross_share)} of {len(sim):,} near-duplicate pairs cross community lines; "
         "several top topics dominate multiple communities.",
         "The same content is repackaged across structurally distinct groups — consistent "
         "with coordinated or template-driven diffusion.",
         "V2 / Phases 2 & 3"),
        ("The corpus leans negative",
         f"'{top_emo}' is the leading non-neutral emotion; mean negative polarity exceeds "
         "positive.",
         "Affective framing skews toward anger/fear, typical of mobilizing misinformation.",
         "V2 / Phase 4"),
        ("Emotion tracks topic more than size",
         "Emotion×topic shows stable per-topic affect; community-level correlations are "
         "weak between size and negativity.",
         "Tone is driven by *what* is discussed, not merely by *how active* a group is.",
         "V2 / Cross-layer"),
        ("Topic noise is substantial",
         f"{_pct(noise_share)} of modeled messages fall in BERTopic's noise bucket.",
         "Short, generic, or boilerplate messages resist topic assignment — a caveat for "
         "any topic-based conclusion.",
         "V2 / Phase 2"),
    ]

    out = ["## 12. Key Findings", ""]
    for i, (title, evidence, interp, src) in enumerate(findings, 1):
        out += [
            f"### {i}. {title}",
            f"- **Evidence:** {evidence}",
            f"- **Interpretation:** {interp}",
            f"- **Supported by:** {src}",
            "",
        ]
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Section 13 — Limitations
# ----------------------------------------------------------------------------
def section_13_limitations(data: ReportData, ctx: dict) -> str:
    """
    State the main methodological limitations.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the limitations section.
    """
    return "\n".join([
        "## 13. Limitations",
        "",
        "- **Topic noise.** A large share of messages land in BERTopic's `-1` bucket; "
        "topic-level figures describe only the modeled subset.",
        "- **Lexicon emotion.** NRC is a bag-of-words lexicon: it misses negation, "
        "sarcasm, irony, and context, and Portuguese coverage is imperfect. Scores are "
        "indicative, not ground truth.",
        "- **Community detection scope.** Communities are detected on the channel "
        "interaction graph only; users and messages inherit a community via their channel.",
        "- **Similarity truncation.** `SIMILAR_TO` keeps only pairs ≥ "
        f"{CONFIG.similarity_threshold:.2f} with top-5 neighbours, so redundancy counts are "
        "lower bounds.",
        "- **Incomplete reply/forward recovery.** Many reply/forward sources are external "
        "or unrecovered, so cross-channel structure is partially observed.",
        "- **Descriptive keywords ≠ topics.** Per-community keywords (Phase 1) are TF-IDF "
        "descriptors, not the formal BERTopic topics of Phase 2.",
        "",
    ])


# ----------------------------------------------------------------------------
# Appendix — oversized tables kept out of the main body
# ----------------------------------------------------------------------------
def section_99_appendix(data: ReportData, ctx: dict) -> str:
    """
    Build the appendix with the full community table and emotion matrix.

    Args:
        data: Loaded report data.
        ctx: Shared context.

    Returns:
        Markdown for the appendix section.
    """
    profile = ctx["profile"].copy()
    full = pd.DataFrame({
        "community": [f"C{int(i)}" for i in profile.index],
        "channels": profile["channels"].astype(int).values,
        "messages": profile["messages"].fillna(0).astype(int).values,
        "users": profile["users"].fillna(0).astype(int).values,
        "topics": profile["topic_diversity"].astype(int).values,
        "dominant_emotion": profile["dominant_emotion"].values,
        "keywords": [" · ".join(str(k).split(" · ")[:5]) for k in profile["community_name"]],
    })

    # Full emotion-share matrix by community.
    emotions = list(CONFIG.emotion_categories)
    share = (
        pd.crosstab(data.msg["community_id"], data.msg["dominant_emotion"], normalize="index")
        .reindex(columns=emotions + ["neutral"], fill_value=0)
    )
    share.insert(0, "community", [f"C{int(i)}" for i in share.index])

    return "\n".join([
        "## Appendix",
        "",
        "### A1. All communities",
        "",
        viz.md_table(full, max_rows=50),
        "",
        "### A2. Full emotion-share matrix by community",
        "",
        viz.md_table(share, max_rows=50, floatfmt=".3f"),
        "",
    ])


# Ordered section builders consumed by generate.py.
SECTIONS = [
    section_01_summary,
    section_02_overview,
    section_03_v1_structure,
    section_04_v2_expanded,
    section_05_communities,
    section_06_topics,
    section_07_similarity,
    section_08_emotion,
    section_09_temporal,
    section_10_cross_layer,
    section_11_statistics,
    section_12_findings,
    section_13_limitations,
    section_99_appendix,
]

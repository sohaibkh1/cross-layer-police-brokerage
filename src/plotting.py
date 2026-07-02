from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from .config import FIGURES_DIR, FORCE_ORDER, FORCES, REPORT_FIGURES_DIR


PALETTE = {
    "metropolitan": "#4363a3",
    "west-midlands": "#2a9d8f",
    "south-wales": "#d55e00",
}


def _save(fig: plt.Figure, path: Path, tight: bool = True, copy_to_report: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if tight:
        fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    if copy_to_report:
        REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, REPORT_FIGURES_DIR / path.name)
    return path


def plot_data_overview(data: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> Path:
    records = (
        data.groupby(["force_slug", "force"]).size().reset_index(name="records").set_index("force_slug")
    )
    crime_counts = (
        data.groupby(["force_slug", "crime_type"]).size().reset_index(name="count")
    )
    crime_counts["force_total"] = crime_counts.groupby("force_slug")["count"].transform("sum")
    crime_counts["proportion"] = crime_counts["count"] / crime_counts["force_total"]
    pivot = (
        crime_counts.pivot(index="crime_type", columns="force_slug", values="proportion")
        .fillna(0)
        .loc[lambda df: df.sum(axis=1).sort_values(ascending=False).index]
    )

    fig, axes = plt.subplots(
        ncols=2,
        figsize=(13, 7),
        gridspec_kw={"width_ratios": [0.85, 1.4]},
    )
    ordered_records = records.loc[FORCE_ORDER]
    axes[0].barh(
        [FORCES[f] for f in FORCE_ORDER],
        ordered_records["records"],
        color=[PALETTE[f] for f in FORCE_ORDER],
    )
    axes[0].invert_yaxis()
    axes[0].set_title("Records by force")
    axes[0].set_xlabel("Street-level crime records")
    axes[0].tick_params(axis="y", labelsize=9)
    for i, value in enumerate(ordered_records["records"]):
        axes[0].text(value, i, f" {int(value):,}", va="center", fontsize=8)

    image = axes[1].imshow(pivot[FORCE_ORDER], aspect="auto", cmap="YlGnBu")
    axes[1].set_title("Crime type distribution within each force")
    axes[1].set_xticks(range(len(FORCE_ORDER)))
    axes[1].set_xticklabels([FORCES[f].replace(" Police", "\nPolice") for f in FORCE_ORDER], fontsize=8)
    axes[1].set_yticks(range(len(pivot.index)))
    axes[1].set_yticklabels(pivot.index, fontsize=8)
    cbar = fig.colorbar(image, ax=axes[1], fraction=0.046, pad=0.04)
    cbar.set_label("Proportion of force records")
    return _save(fig, output_dir / "fig1_data_overview.png")


def _short_crime_label(label: str, width: int = 18) -> str:
    replacements = {
        "Violence and sexual offences": "Violence & sexual\noffences",
        "Criminal damage and arson": "Criminal damage\n& arson",
        "Possession of weapons": "Possession of\nweapons",
        "Theft from the person": "Theft from\nthe person",
        "Bicycle theft": "Bicycle\ntheft",
        "Vehicle crime": "Vehicle\ncrime",
        "Other theft": "Other\ntheft",
        "Shoplifting": "Shoplifting",
        "Public order": "Public\norder",
        "Burglary": "Burglary",
        "Drugs": "Drugs",
        "Robbery": "Robbery",
        "Other crime": "Other\ncrime",
        "Anti-social behaviour": "Anti-social\nbehaviour",
    }
    return replacements.get(label, textwrap.fill(label, width=width))


def plot_brokerage_heatmap(centrality: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> Path:
    eligible = centrality[centrality["brokerage_eligible"]].copy()
    top_crimes = (
        eligible.sort_values(["force_slug", "brokerage_rank"])
        .groupby("force_slug")
        .head(7)["crime_type"]
        .drop_duplicates()
        .tolist()
    )
    subset = eligible[eligible["crime_type"].isin(top_crimes)].copy()
    pivot = subset.pivot(index="crime_type", columns="force_slug", values="brokerage_score").fillna(0)
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index, FORCE_ORDER]
    ranks = subset.pivot(index="crime_type", columns="force_slug", values="brokerage_rank").reindex(
        index=pivot.index, columns=FORCE_ORDER
    )

    fig, ax = plt.subplots(figsize=(9.5, max(5.0, 0.43 * len(pivot))))
    image = ax.imshow(pivot, aspect="auto", cmap="PuBuGn", vmin=0, vmax=1)
    ax.set_title("Cross-layer brokerage score for outcome-linked crime categories", fontsize=12)
    ax.set_xticks(range(len(FORCE_ORDER)))
    ax.set_xticklabels([FORCES[f].replace(" Police", "\nPolice") for f in FORCE_ORDER], fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([_short_crime_label(label) for label in pivot.index], fontsize=8)
    for y, crime in enumerate(pivot.index):
        for x, force_slug in enumerate(FORCE_ORDER):
            rank = ranks.loc[crime, force_slug]
            score = pivot.loc[crime, force_slug]
            if pd.notna(rank) and score > 0:
                ax.text(x, y, f"#{int(rank)}\n{score:.2f}", ha="center", va="center", fontsize=7, color="#111111")
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Mean percentile score")
    return _save(fig, output_dir / "fig2_brokerage_comparison.png")


def plot_similarity_network(
    similarity_edges: pd.DataFrame,
    similarity_nodes: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Similarity networks with communities mapped to semantic labels.

    Rather than colouring by raw greedy-modularity community IDs (which are
    assigned arbitrarily per force and are not comparable across panels), each
    community is mapped to a semantic label based on the crime types it
    contains, and consistent colours are used across all three panels so the
    reader can visually verify that community structure is broadly stable
    across forces.
    """
    # Semantic community palette (consistent across all panels)
    SEMANTIC_COLOURS = {
        "Property crime": "#5b9bd5",       # blue
        "Violence & disorder": "#ed7d31",   # orange
        "Mixed / other": "#a5a5a5",         # neutral grey fallback
    }
    # Crime-type markers used to classify each community
    PROPERTY_MARKERS = {
        "Burglary", "Vehicle crime", "Bicycle theft",
        "Other theft", "Shoplifting", "Theft from the person",
    }
    VIOLENCE_MARKERS = {
        "Violence and sexual offences", "Drugs", "Public order",
        "Possession of weapons", "Other crime", "Robbery",
    }

    def classify_community(members: set) -> str:
        prop_hits = len(members & PROPERTY_MARKERS)
        viol_hits = len(members & VIOLENCE_MARKERS)
        if prop_hits > viol_hits:
            return "Property crime"
        if viol_hits > prop_hits:
            return "Violence & disorder"
        return "Mixed / other"

    fig, axes = plt.subplots(ncols=3, figsize=(9, 5.4))

    sim_labels = {
        "Violence and sexual offences": "Violence/sexual",
        "Criminal damage and arson": "Criminal damage",
        "Possession of weapons": "Weapons",
        "Theft from the person": "Theft from person",
    }

    used_labels: set = set()

    for ax, force_slug in zip(axes, FORCE_ORDER):
        ax.axis("off")
        force_nodes = similarity_nodes[similarity_nodes["force_slug"] == force_slug]
        force_edges = similarity_edges[similarity_edges["force_slug"] == force_slug]
        graph = nx.Graph()
        for row in force_nodes.itertuples(index=False):
            graph.add_node(row.crime_type, community_id=int(row.community_id))
        for row in force_edges.itertuples(index=False):
            graph.add_edge(row.source_crime_type, row.target_crime_type, weight=float(row.cosine_similarity))

        if graph.number_of_nodes() == 0:
            ax.set_title(FORCES[force_slug].replace(" Police", "\nPolice"), fontsize=10)
            continue

        # Classify each community by its crime-type membership
        community_members: dict = {}
        for node, attrs in graph.nodes(data=True):
            cid = attrs.get("community_id", 1)
            community_members.setdefault(cid, set()).add(node)
        community_label = {
            cid: classify_community(members)
            for cid, members in community_members.items()
        }
        used_labels.update(community_label.values())

        pos = nx.spring_layout(graph, weight="weight", seed=7, k=1.6)
        xs = [xy[0] for xy in pos.values()]
        ys = [xy[1] for xy in pos.values()]
        x_span = max(xs) - min(xs) or 1.0
        y_span = max(ys) - min(ys) or 1.0
        ax.set_xlim(min(xs) - 0.30 * x_span, max(xs) + 0.30 * x_span)
        ax.set_ylim(min(ys) - 0.18 * y_span, max(ys) + 0.18 * y_span)
        widths = [0.6 + 3.0 * graph[u][v].get("weight", 0.0) for u, v in graph.edges]
        node_colors = [
            SEMANTIC_COLOURS[community_label[graph.nodes[node].get("community_id", 1)]]
            for node in graph.nodes
        ]
        node_sizes = [460 + 90 * graph.degree(node, weight="weight") for node in graph.nodes]

        nx.draw_networkx_edges(graph, pos, ax=ax, width=widths, edge_color="#777777", alpha=0.48)
        nx.draw_networkx_nodes(
            graph, pos, ax=ax,
            node_color=node_colors, node_size=node_sizes,
            edgecolors="#222222", linewidths=0.6,
        )
        labels = {node: sim_labels.get(str(node), str(node)) for node in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=7.5)
        ax.set_title(FORCES[force_slug].replace(" Police", "\nPolice"), fontsize=10)

    # Shared legend at the bottom explaining what colours mean
    from matplotlib.lines import Line2D
    legend_order = ["Property crime", "Violence & disorder", "Mixed / other"]
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", label=label,
               markerfacecolor=SEMANTIC_COLOURS[label], markeredgecolor="#222222",
               markersize=11, markeredgewidth=0.6)
        for label in legend_order
        if label in used_labels
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=9,
        bbox_to_anchor=(0.5, -0.02),
    )

    fig.suptitle(
        "Outcome-profile similarity communities across forces",
        fontsize=11, y=0.99,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    return _save(fig, output_dir / "fig3_similarity_networks.png")

def plot_outcome_heatmap(
    outcome_comparison: pd.DataFrame,
    centrality: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    top_crimes = (
        centrality[centrality["brokerage_eligible"]]
        .sort_values(["force_slug", "brokerage_rank"])
        .groupby("force_slug")
        .head(5)["crime_type"]
        .drop_duplicates()
        .tolist()
    )
    top_outcomes = (
        outcome_comparison.groupby("outcome_category")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(6)
        .index.tolist()
    )
    subset = outcome_comparison[
        outcome_comparison["crime_type"].isin(top_crimes)
        & outcome_comparison["outcome_category"].isin(top_outcomes)
    ].copy()

    short_labels = {
        "Investigation complete; no suspect identified": "No suspect identified",
        "Unable to prosecute suspect": "Unable to prosecute",
        "Under investigation": "Under investigation",
        "Awaiting court outcome": "Awaiting court",
        "Local resolution": "Local resolution",
        "Status update unavailable": "Status unavailable",
        "Action to be taken by another organisation": "Another organisation",
    }
    x_labels = [textwrap.fill(short_labels.get(label, label), width=14) for label in top_outcomes]

    fig, axes = plt.subplots(ncols=3, figsize=(17, max(7.2, 0.58 * len(top_crimes))), sharey=True)
    vmax = subset["proportion_within_crime_type"].max() if len(subset) else 1
    for ax, force_slug in zip(axes, FORCE_ORDER):
        force_subset = subset[subset["force_slug"] == force_slug]
        pivot = (
            force_subset.pivot(
                index="crime_type",
                columns="outcome_category",
                values="proportion_within_crime_type",
            )
            .reindex(index=top_crimes, columns=top_outcomes)
            .fillna(0)
        )
        image = ax.imshow(pivot, aspect="auto", cmap="YlOrRd", vmin=0, vmax=vmax)
        ax.set_title(FORCES[force_slug].replace(" Police", "\nPolice"), fontsize=10)
        ax.set_xticks(range(len(top_outcomes)))
        ax.set_xticklabels(x_labels, rotation=35, ha="right", fontsize=7)
        ax.set_yticks(range(len(top_crimes)))
        ax.set_yticklabels(top_crimes, fontsize=8)
    fig.suptitle("Recorded outcome proportions within selected crime types", fontsize=13)
    fig.subplots_adjust(left=0.16, right=0.88, bottom=0.31, top=0.82, wspace=0.25)
    cbar_ax = fig.add_axes([0.90, 0.31, 0.018, 0.49])
    cbar = fig.colorbar(image, cax=cbar_ax)
    cbar.set_label("Proportion within crime type")
    return _save(fig, output_dir / "figS1_outcome_heatmap.png", tight=False, copy_to_report=False)


def plot_centrality_comparison(
    centrality: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Two-panel supporting figure for the centrality-metric comparison (Appendix).

    Left panel: PageRank rank vs betweenness rank per brokerage-eligible crime type
    (one point per (force, crime type)). Points near the diagonal indicate that
    the two centrality metrics agree on that crime type.

    Right panel: rank-size distribution of weighted node degree in the combined
    graph on a log scale, showing the hub-like drop from the top-ranked node.
    """
    eligible = centrality[centrality["brokerage_eligible"] == True].copy()  # noqa: E712
    force_meta = [
        ("metropolitan", "Metropolitan Police Service", PALETTE["metropolitan"]),
        ("west-midlands", "West Midlands Police", PALETTE["west-midlands"]),
        ("south-wales", "South Wales Police", PALETTE["south-wales"]),
    ]

    fig, axes = plt.subplots(ncols=2, figsize=(12, 5.5))

    # Panel A: PageRank rank vs betweenness rank scatter
    ax = axes[0]
    for slug, label, colour in force_meta:
        sub = eligible[eligible["force_slug"] == slug]
        if sub.empty:
            continue
        ax.scatter(
            sub["pagerank_rank"],
            sub["betweenness_rank"],
            s=90, alpha=0.75, edgecolor="black", linewidths=0.4,
            label=label, color=colour,
        )
    ax.plot([1, 13], [1, 13], color="#555555", ls="--", lw=1.2, alpha=0.6)
    ax.set_xlabel("PageRank rank (1 = highest)", fontsize=12)
    ax.set_ylabel("Betweenness rank (1 = highest)", fontsize=12)
    ax.set_title("Centrality-metric agreement per crime type")
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13])
    ax.set_yticks([1, 3, 5, 7, 9, 11, 13])
    ax.tick_params(labelsize=12)
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left", fontsize=8, frameon=False)

    # Panel B: Rank-size distribution of weighted degree in combined graph
    ax = axes[1]
    for slug, label, colour in force_meta:
        sub = eligible[eligible["force_slug"] == slug].sort_values(
            "combined_strength", ascending=False
        )
        if sub.empty:
            continue
        ranks = np.arange(1, len(sub) + 1)
        ax.plot(
            ranks, sub["combined_strength"].values,
            marker="o", ms=5, lw=1.2, alpha=0.9,
            label=label, color=colour,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Crime type rank (by weighted degree)", fontsize=12)
    ax.set_ylabel("Weighted degree in combined graph", fontsize=12)
    ax.set_title("Rank-size distribution (log scale)")
    ax.grid(alpha=0.25, which="both")
    ax.tick_params(labelsize=12)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.tight_layout(pad=0.6)
    return _save(fig, output_dir / "fig4_centrality_comparison.png")

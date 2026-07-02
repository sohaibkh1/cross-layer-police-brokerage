from __future__ import annotations

from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from .config import FORCES, FORCE_ORDER


AUDIT_FIELDS = [
    "crime_id",
    "crime_type",
    "outcome_category",
    "lsoa_code",
    "lsoa_name",
    "month",
]


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub-style Markdown table without tabulate."""
    if df.empty:
        return "_No rows._"
    display = df.copy().fillna("")
    display = display.astype(str)
    for column in display.columns:
        display[column] = display[column].str.replace("|", "\\|", regex=False)
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in display.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def label_sets(data: pd.DataFrame, column: str) -> dict[str, set[str]]:
    labels: dict[str, set[str]] = {}
    for force_slug in FORCE_ORDER:
        values = data.loc[data["force_slug"] == force_slug, column].dropna().astype(str)
        labels[force_slug] = set(values.unique())
    return labels


def labels_are_identical(labels: dict[str, set[str]]) -> bool:
    sets = list(labels.values())
    if not sets:
        return False
    return all(values == sets[0] for values in sets[1:])


def create_data_audit(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for force_slug in FORCE_ORDER:
        force_data = data[data["force_slug"] == force_slug]
        total = len(force_data)
        rows.append(
            {
                "section": "records",
                "force": FORCES[force_slug],
                "force_slug": force_slug,
                "month": "all",
                "field": "records",
                "category": "total",
                "count": total,
                "percent": 100.0 if total else 0.0,
                "note": "",
            }
        )

        for month, count in force_data["month"].value_counts(dropna=False).sort_index().items():
            rows.append(
                {
                    "section": "records_by_month",
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "month": month,
                    "field": "records",
                    "category": "month",
                    "count": int(count),
                    "percent": round((count / total) * 100, 3) if total else 0.0,
                    "note": "",
                }
            )

        for field in AUDIT_FIELDS:
            missing = int(force_data[field].isna().sum()) if field in force_data else total
            rows.append(
                {
                    "section": "missing_values",
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "month": "all",
                    "field": field,
                    "category": "missing",
                    "count": missing,
                    "percent": round((missing / total) * 100, 3) if total else 0.0,
                    "note": "",
                }
            )

        unique_fields = {
            "crime_type": "unique_crime_types",
            "outcome_category": "unique_outcomes",
            "lsoa_code": "unique_lsoas",
        }
        for field, label in unique_fields.items():
            rows.append(
                {
                    "section": "unique_counts",
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "month": "all",
                    "field": field,
                    "category": label,
                    "count": int(force_data[field].nunique(dropna=True)),
                    "percent": np.nan,
                    "note": "",
                }
            )

    for column, section in [
        ("crime_type", "crime_label_comparison"),
        ("outcome_category", "outcome_label_comparison"),
    ]:
        sets = label_sets(data, column)
        shared = set.intersection(*sets.values()) if sets else set()
        union = set.union(*sets.values()) if sets else set()
        identical = labels_are_identical(sets)
        for force_slug, values in sets.items():
            missing_from_force = sorted(union - values)
            extra_vs_shared = sorted(values - shared)
            rows.append(
                {
                    "section": section,
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "month": "all",
                    "field": column,
                    "category": "label_set",
                    "count": len(values),
                    "percent": np.nan,
                    "note": (
                        "identical across forces"
                        if identical
                        else f"missing_vs_union={missing_from_force}; extra_vs_intersection={extra_vs_shared}"
                    ),
                }
            )

    return pd.DataFrame(rows)


def write_data_audit_markdown(data: pd.DataFrame, audit: pd.DataFrame, path: Path) -> None:
    crime_sets = label_sets(data, "crime_type")
    outcome_sets = label_sets(data, "outcome_category")
    crime_identical = labels_are_identical(crime_sets)
    outcome_identical = labels_are_identical(outcome_sets)

    lines = [
        "# Data audit",
        "",
        "Source: UK Police Open Data street-level crime CSV files from data.police.uk.",
        "",
        "## Scope",
        "",
        f"- Forces: {', '.join(FORCES.values())}.",
        f"- Months: {', '.join(sorted(data['month'].dropna().unique()))}.",
        "- Dataset type: street-level crime data; the street CSV `Last outcome category` field is used as the outcome variable.",
        "- Stop-and-search, PSNI, Scotland, and British Transport Police are excluded.",
        "",
        "## Compatibility checks",
        "",
        f"- Crime category labels identical across the three forces: {'yes' if crime_identical else 'no'}.",
        f"- Outcome category labels identical across the three forces: {'yes' if outcome_identical else 'no'}.",
        "- Local area fields checked: `LSOA code` and `LSOA name`.",
        "",
    ]

    if not crime_identical:
        lines += ["### Crime label differences", ""]
        union = set.union(*crime_sets.values())
        for force_slug, values in crime_sets.items():
            lines.append(f"- {FORCES[force_slug]} missing vs union: {sorted(union - values)}")
        lines.append("")

    if not outcome_identical:
        lines += ["### Outcome label differences", ""]
        union = set.union(*outcome_sets.values())
        for force_slug, values in outcome_sets.items():
            lines.append(f"- {FORCES[force_slug]} missing vs union: {sorted(union - values)}")
        lines.append("")

    lines += [
        "## Records and missing values",
        "",
        dataframe_to_markdown(
            audit[audit["section"].isin(["records", "missing_values", "unique_counts"])]
        ),
        "",
        "## Decision",
        "",
        "All three selected forces are retained if the table above shows comparable crime and outcome labels and usable LSOA fields. Missing outcomes and missing LSOAs are counted here; records with missing LSOA are not used for the area-crime layer, and records with missing outcomes are not used for the crime-outcome layer.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def bipartite_density(graph: nx.Graph, left_type: str, right_type: str) -> float:
    left = [n for n, d in graph.nodes(data=True) if d.get("node_type") == left_type]
    right = [n for n, d in graph.nodes(data=True) if d.get("node_type") == right_type]
    possible = len(left) * len(right)
    return graph.number_of_edges() / possible if possible else 0.0


def compute_network_stats(
    data: pd.DataFrame, networks: dict[str, dict[str, nx.Graph]]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for force_slug in FORCE_ORDER:
        force_data = data[data["force_slug"] == force_slug]
        for layer_name, graph in networks[force_slug].items():
            strengths = dict(graph.degree(weight="weight"))
            density = nx.density(graph) if graph.number_of_nodes() > 1 else 0.0
            if layer_name == "area_crime":
                density = bipartite_density(graph, "area", "crime")
            elif layer_name == "crime_outcome":
                density = bipartite_density(graph, "crime", "outcome")

            rows.append(
                {
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "layer": layer_name,
                    "records": len(force_data),
                    "records_with_lsoa": int(force_data["area_id"].notna().sum()),
                    "records_with_outcome": int(force_data["outcome_category"].notna().sum()),
                    "areas": int(force_data["area_id"].nunique(dropna=True)),
                    "crime_types": int(force_data["crime_type"].nunique(dropna=True)),
                    "outcomes": int(force_data["outcome_category"].nunique(dropna=True)),
                    "nodes": graph.number_of_nodes(),
                    "edges": graph.number_of_edges(),
                    "density": density,
                    "total_edge_weight": sum(
                        attrs.get("weight", 0.0) for _, _, attrs in graph.edges(data=True)
                    ),
                    "average_weighted_degree": float(np.mean(list(strengths.values())))
                    if strengths
                    else 0.0,
                }
            )
    return pd.DataFrame(rows)


def _add_distance_attribute(graph: nx.Graph) -> nx.Graph:
    graph = graph.copy()
    for u, v, attrs in graph.edges(data=True):
        weight = float(attrs.get("weight", 1.0))
        graph[u][v]["distance"] = 1.0 / weight if weight > 0 else 1.0
    return graph


def compute_centrality(
    networks: dict[str, dict[str, nx.Graph]],
    max_betweenness_sample: int = 250,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rng_seed = 42

    for force_slug in FORCE_ORDER:
        combined = networks[force_slug]["combined"]
        area_crime = networks[force_slug]["area_crime"]
        crime_outcome = networks[force_slug]["crime_outcome"]
        distance_graph = _add_distance_attribute(combined)
        crime_nodes = [
            node for node, attrs in combined.nodes(data=True) if attrs.get("node_type") == "crime"
        ]

        pagerank = nx.pagerank(combined, weight="weight") if combined.number_of_nodes() else {}
        if combined.number_of_nodes() <= max_betweenness_sample:
            betweenness = nx.betweenness_centrality(distance_graph, weight="distance")
            betweenness_method = "exact_weighted_distance"
        else:
            betweenness = nx.betweenness_centrality(
                distance_graph,
                k=max_betweenness_sample,
                weight="distance",
                seed=rng_seed,
            )
            betweenness_method = f"approx_weighted_distance_k{max_betweenness_sample}"

        combined_strength = dict(combined.degree(weight="weight"))
        area_strength = dict(area_crime.degree(weight="weight"))
        outcome_strength = dict(crime_outcome.degree(weight="weight"))

        for node in crime_nodes:
            label = combined.nodes[node].get("label", node.replace("crime::", ""))
            rows.append(
                {
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "crime_type": label,
                    "combined_strength": combined_strength.get(node, 0.0),
                    "area_crime_strength": area_strength.get(node, 0.0),
                    "crime_outcome_strength": outcome_strength.get(node, 0.0),
                    "pagerank": pagerank.get(node, 0.0),
                    "betweenness": betweenness.get(node, 0.0),
                    "betweenness_method": betweenness_method,
                }
            )

    centrality = pd.DataFrame(rows)
    for metric in [
        "combined_strength",
        "area_crime_strength",
        "crime_outcome_strength",
        "pagerank",
        "betweenness",
    ]:
        rank_col = f"{metric}_rank"
        centrality[rank_col] = centrality.groupby("force_slug")[metric].rank(
            method="min", ascending=False
        )
    centrality["has_outcome_links"] = centrality["crime_outcome_strength"] > 0
    for metric in ["pagerank", "betweenness", "combined_strength"]:
        rank_col = f"mediator_{metric}_rank"
        centrality[rank_col] = np.nan
        linked = centrality["has_outcome_links"]
        centrality.loc[linked, rank_col] = centrality[linked].groupby("force_slug")[metric].rank(
            method="min", ascending=False
        )
    centrality["combined_strength_share"] = centrality["combined_strength"] / centrality.groupby(
        "force_slug"
    )["combined_strength"].transform("sum")
    return centrality.sort_values(["force_slug", "pagerank_rank", "crime_type"])


def compute_outcome_comparison(data: pd.DataFrame) -> pd.DataFrame:
    usable = data.dropna(subset=["crime_type", "outcome_category"]).copy()
    grouped = (
        usable.groupby(["force", "force_slug", "crime_type", "outcome_category"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    grouped["crime_type_total"] = grouped.groupby(["force_slug", "crime_type"])["count"].transform(
        "sum"
    )
    grouped["force_total_with_outcome"] = grouped.groupby("force_slug")["count"].transform("sum")
    grouped["proportion_within_crime_type"] = grouped["count"] / grouped["crime_type_total"]
    grouped["proportion_within_force"] = grouped["count"] / grouped["force_total_with_outcome"]
    return grouped.sort_values(["force_slug", "crime_type", "count"], ascending=[True, True, False])





def _rank_percentile_high_is_good(series: pd.Series) -> pd.Series:
    """Return percentile ranks where larger metric values receive larger percentiles."""
    if series.dropna().empty:
        return pd.Series(np.nan, index=series.index)
    return series.rank(method="average", ascending=True, pct=True)


def compute_brokerage_score(
    data: pd.DataFrame,
    centrality: pd.DataFrame,
    outcome_comparison: pd.DataFrame,
) -> pd.DataFrame:
    """Compute a transparent cross-layer brokerage score for crime categories.

    Crime categories are treated as brokers only if they connect both layers: the
    area-crime layer and the crime-outcome layer. Anti-social behaviour normally
    has area-crime edges but no outcome edges in street-level data, so it remains
    in the area layer but is excluded from this cross-layer score.
    """
    # Drop any brokerage columns already present in the cached centrality CSV.
    # Without this, a second pipeline run re-merges the same columns and creates
    # _x / _y duplicates that silently break the percentile calculation.
    _brokerage_cols = [
        "area_spread", "outcome_connectivity", "area_lsoa_count", "total_lsoas",
        "outcome_category_count", "crime_outcome_records", "total_outcomes",
        "outcome_entropy", "outcome_entropy_norm",
        "area_spread_percentile", "outcome_connectivity_percentile",
        "outcome_entropy_percentile", "betweenness_percentile",
        "brokerage_score", "brokerage_rank", "brokerage_eligible",
    ]
    result = centrality.drop(
        columns=[c for c in _brokerage_cols if c in centrality.columns],
        errors="ignore",
    ).copy()

    total_lsoas = data.dropna(subset=["area_id"]).groupby("force_slug")["area_id"].nunique()
    area_spread = (
        data.dropna(subset=["area_id", "crime_type"])
        .groupby(["force_slug", "crime_type"])["area_id"]
        .nunique()
        .rename("area_lsoa_count")
        .reset_index()
    )
    area_spread["total_lsoas"] = area_spread["force_slug"].map(total_lsoas)
    area_spread["area_spread"] = area_spread["area_lsoa_count"] / area_spread["total_lsoas"]

    total_outcomes = (
        data.dropna(subset=["outcome_category"])
        .groupby("force_slug")["outcome_category"]
        .nunique()
    )
    outcome_counts = (
        outcome_comparison.groupby(["force_slug", "crime_type"], as_index=False)
        .agg(
            outcome_category_count=("outcome_category", "nunique"),
            crime_outcome_records=("count", "sum"),
        )
    )
    outcome_counts["total_outcomes"] = outcome_counts["force_slug"].map(total_outcomes)
    outcome_counts["outcome_connectivity"] = (
        outcome_counts["outcome_category_count"] / outcome_counts["total_outcomes"]
    )

    entropy_rows: list[dict[str, object]] = []
    for (force_slug, crime_type), group in outcome_comparison.groupby(["force_slug", "crime_type"]):
        proportions = group["proportion_within_crime_type"].dropna().to_numpy(dtype=float)
        proportions = proportions[proportions > 0]
        entropy = float(-(proportions * np.log(proportions)).sum()) if len(proportions) else 0.0
        max_entropy = float(np.log(total_outcomes.get(force_slug, 0))) if total_outcomes.get(force_slug, 0) > 1 else 1.0
        entropy_rows.append(
            {
                "force_slug": force_slug,
                "crime_type": crime_type,
                "outcome_entropy": entropy,
                "outcome_entropy_norm": entropy / max_entropy if max_entropy else 0.0,
            }
        )
    entropy_df = pd.DataFrame(entropy_rows)

    result = result.merge(area_spread, on=["force_slug", "crime_type"], how="left")
    result = result.merge(outcome_counts, on=["force_slug", "crime_type"], how="left")
    result = result.merge(entropy_df, on=["force_slug", "crime_type"], how="left")

    fill_zero_cols = [
        "area_lsoa_count",
        "total_lsoas",
        "area_spread",
        "outcome_category_count",
        "crime_outcome_records",
        "total_outcomes",
        "outcome_connectivity",
        "outcome_entropy",
        "outcome_entropy_norm",
    ]
    for col in fill_zero_cols:
        if col in result.columns:
            result[col] = result[col].fillna(0)

    result["brokerage_eligible"] = (
        (result["area_crime_strength"] > 0) & (result["crime_outcome_strength"] > 0)
    )

    components = {
        "area_spread": "area_spread_percentile",
        "outcome_connectivity": "outcome_connectivity_percentile",
        "outcome_entropy_norm": "outcome_entropy_percentile",
        "betweenness": "betweenness_percentile",
    }
    for metric, out_col in components.items():
        result[out_col] = np.nan
        eligible = result["brokerage_eligible"]
        result.loc[eligible, out_col] = result[eligible].groupby("force_slug")[metric].transform(
            _rank_percentile_high_is_good
        )

    percentile_cols = list(components.values())
    result["brokerage_score"] = result[percentile_cols].mean(axis=1, skipna=False)
    result["brokerage_rank"] = np.nan
    eligible = result["brokerage_eligible"]
    result.loc[eligible, "brokerage_rank"] = result[eligible].groupby("force_slug")[
        "brokerage_score"
    ].rank(method="min", ascending=False)

    return result.sort_values(["force_slug", "brokerage_rank", "crime_type"], na_position="last")


def _spearman_rho(x: pd.Series, y: pd.Series) -> float:
    """Compute Spearman rank correlation without adding a scipy dependency."""
    ranked_x = x.rank(method="average")
    ranked_y = y.rank(method="average")
    return float(ranked_x.corr(ranked_y))


def compute_brokerage_validation(centrality: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive validation checks for brokerage results.

    This produces two checks:
    1. Within-force association between brokerage score and raw crime volume.
    2. Cross-force consistency of brokerage scores across shared crime types.

    These are descriptive checks because there are only around 13 brokerage-eligible
    crime categories per force.
    """
    if "brokerage_eligible" not in centrality.columns:
        raise KeyError("Expected centrality table to contain 'brokerage_eligible'.")

    eligible = centrality[centrality["brokerage_eligible"]].copy()

    volume_col = None
    for candidate in ["crime_area_strength", "area_crime_strength"]:
        if candidate in eligible.columns:
            volume_col = candidate
            break

    if volume_col is None:
        raise KeyError(
            "Expected a volume column named 'crime_area_strength' or "
            "'area_crime_strength'."
        )

    rows: list[dict[str, object]] = []

    # Check 1: does brokerage simply reproduce raw volume?
    for force_slug, group in eligible.groupby("force_slug"):
        group = group.dropna(subset=["brokerage_score", volume_col])
        rows.append(
            {
                "check_type": "brokerage_vs_volume",
                "force_1": force_slug,
                "force_2": "",
                "n_crime_types": len(group),
                "spearman_rho": _spearman_rho(
                    group["brokerage_score"],
                    group[volume_col],
                ),
            }
        )

    # Check 2: are brokerage roles consistent across forces?
    wide = eligible.pivot_table(
        index="crime_type",
        columns="force_slug",
        values="brokerage_score",
        aggfunc="first",
    )

    forces = list(wide.columns)
    for i in range(len(forces)):
        for j in range(i + 1, len(forces)):
            pair = wide[[forces[i], forces[j]]].dropna()
            rows.append(
                {
                    "check_type": "cross_force_brokerage_consistency",
                    "force_1": forces[i],
                    "force_2": forces[j],
                    "n_crime_types": len(pair),
                    "spearman_rho": _spearman_rho(
                        pair[forces[i]],
                        pair[forces[j]],
                    ),
                }
            )

    return pd.DataFrame(rows)


def compute_similarity_network(
    outcome_comparison: pd.DataFrame,
    top_k: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build crime-type outcome-profile similarity networks for each force.

    Nodes are outcome-linked crime categories. Edges connect each crime type to
    its top-k most similar crime types using cosine similarity over recorded
    outcome proportions. Greedy modularity communities are computed on the small
    weighted similarity graph.
    """
    edge_rows: list[dict[str, object]] = []
    node_rows: list[dict[str, object]] = []

    for force_slug in FORCE_ORDER:
        force_outcomes = outcome_comparison[outcome_comparison["force_slug"] == force_slug]
        if force_outcomes.empty:
            continue

        matrix = (
            force_outcomes.pivot_table(
                index="crime_type",
                columns="outcome_category",
                values="proportion_within_crime_type",
                fill_value=0.0,
                aggfunc="sum",
            )
            .sort_index()
        )
        crime_types = list(matrix.index)
        if len(crime_types) < 2:
            continue

        values = matrix.to_numpy(dtype=float)
        norms = np.linalg.norm(values, axis=1)
        similarity = np.zeros((len(crime_types), len(crime_types)), dtype=float)
        for i, j in combinations(range(len(crime_types)), 2):
            if norms[i] == 0 or norms[j] == 0:
                score = 0.0
            else:
                score = float(np.dot(values[i], values[j]) / (norms[i] * norms[j]))
            similarity[i, j] = score
            similarity[j, i] = score

        selected_edges: dict[tuple[str, str], float] = {}
        for i, source in enumerate(crime_types):
            candidates = [
                (j, similarity[i, j]) for j in range(len(crime_types)) if j != i and similarity[i, j] > 0
            ]
            candidates.sort(key=lambda item: item[1], reverse=True)
            for j, score in candidates[:top_k]:
                target = crime_types[j]
                u, v = sorted([source, target])
                selected_edges[(u, v)] = max(selected_edges.get((u, v), 0.0), float(score))

        graph = nx.Graph(force=force_slug, layer="crime_outcome_similarity", top_k=top_k)
        graph.add_nodes_from(crime_types)
        for (source, target), score in selected_edges.items():
            graph.add_edge(source, target, weight=score, cosine_similarity=score)

        if graph.number_of_edges() > 0:
            communities = nx.community.greedy_modularity_communities(graph, weight="weight")
        else:
            communities = [frozenset([node]) for node in graph.nodes]
        community_lookup: dict[str, int] = {}
        for community_id, community in enumerate(communities, start=1):
            for node in community:
                community_lookup[node] = community_id

        for node in graph.nodes:
            node_rows.append(
                {
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "crime_type": node,
                    "community_id": community_lookup.get(node, 0),
                    "similarity_degree": graph.degree(node),
                    "similarity_strength": graph.degree(node, weight="weight"),
                    "method": f"cosine_outcome_profile_top_{top_k}_edges_per_node_greedy_modularity",
                }
            )
        for source, target, attrs in graph.edges(data=True):
            edge_rows.append(
                {
                    "force": FORCES[force_slug],
                    "force_slug": force_slug,
                    "source_crime_type": source,
                    "target_crime_type": target,
                    "cosine_similarity": attrs.get("cosine_similarity", attrs.get("weight", 0.0)),
                    "source_community_id": community_lookup.get(source, 0),
                    "target_community_id": community_lookup.get(target, 0),
                    "method": f"cosine_outcome_profile_top_{top_k}_edges_per_node_greedy_modularity",
                }
            )

    return pd.DataFrame(edge_rows), pd.DataFrame(node_rows)


def write_results_summary(
    data: pd.DataFrame,
    network_summary: pd.DataFrame,
    centrality: pd.DataFrame,
    outcome_comparison: pd.DataFrame,
    path: Path,
) -> None:
    lines = [
        "# Results summary",
        "",
        f"Months analysed: {', '.join(sorted(data['month'].dropna().unique()))}.",
        f"Total records after basic cleaning: {len(data):,}.",
        "",
        "## Records by force",
        "",
        dataframe_to_markdown(
            data.groupby(["force", "force_slug"]).size().reset_index(name="records")
        ),
        "",
        "## Network summary",
        "",
        dataframe_to_markdown(network_summary),
        "",
        "## Top cross-layer broker crime types",
        "",
        dataframe_to_markdown(
            centrality[centrality["brokerage_rank"] <= 5][
                [
                    "force",
                    "crime_type",
                    "brokerage_rank",
                    "brokerage_score",
                    "area_spread",
                    "outcome_connectivity",
                    "outcome_entropy_norm",
                    "betweenness",
                    "betweenness_method",
                ]
            ]
        ),
        "",
        "## Largest outcome categories by force",
        "",
        dataframe_to_markdown(
            outcome_comparison.groupby(["force", "force_slug", "outcome_category"], as_index=False)[
                "count"
            ]
            .sum()
            .sort_values(["force_slug", "count"], ascending=[True, False])
            .groupby("force_slug")
            .head(6)
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

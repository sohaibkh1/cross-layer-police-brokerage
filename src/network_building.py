from __future__ import annotations

import networkx as nx
import pandas as pd


def _add_node_once(graph: nx.Graph, node: str, **attrs) -> None:
    if node not in graph:
        graph.add_node(node, **attrs)
    else:
        graph.nodes[node].update({k: v for k, v in attrs.items() if v is not None})


def build_area_crime_network(force_data: pd.DataFrame, force_slug: str) -> nx.Graph:
    graph = nx.Graph(force=force_slug, layer="area_crime")
    usable = force_data.dropna(subset=["area_id", "crime_type"]).copy()
    grouped = (
        usable.groupby(["area_id", "area_label", "crime_type"], dropna=False)
        .size()
        .reset_index(name="weight")
    )

    for row in grouped.itertuples(index=False):
        area_node = f"area::{force_slug}::{row.area_id}"
        crime_node = f"crime::{row.crime_type}"
        _add_node_once(
            graph,
            area_node,
            node_type="area",
            force=force_slug,
            label=str(row.area_label),
            area_id=str(row.area_id),
            layer="area_crime",
        )
        _add_node_once(
            graph,
            crime_node,
            node_type="crime",
            force=force_slug,
            label=str(row.crime_type),
            layer="shared_crime",
        )
        graph.add_edge(
            area_node,
            crime_node,
            weight=float(row.weight),
            count=int(row.weight),
            edge_type="area_crime",
            force=force_slug,
        )
    return graph


def build_crime_outcome_network(force_data: pd.DataFrame, force_slug: str) -> nx.Graph:
    graph = nx.Graph(force=force_slug, layer="crime_outcome")
    usable = force_data.dropna(subset=["crime_type", "outcome_category"]).copy()
    grouped = (
        usable.groupby(["crime_type", "outcome_category"], dropna=False)
        .size()
        .reset_index(name="weight")
    )

    for row in grouped.itertuples(index=False):
        crime_node = f"crime::{row.crime_type}"
        outcome_node = f"outcome::{row.outcome_category}"
        _add_node_once(
            graph,
            crime_node,
            node_type="crime",
            force=force_slug,
            label=str(row.crime_type),
            layer="shared_crime",
        )
        _add_node_once(
            graph,
            outcome_node,
            node_type="outcome",
            force=force_slug,
            label=str(row.outcome_category),
            layer="crime_outcome",
        )
        graph.add_edge(
            crime_node,
            outcome_node,
            weight=float(row.weight),
            count=int(row.weight),
            edge_type="crime_outcome",
            force=force_slug,
        )
    return graph


def build_multilayer_network(force_data: pd.DataFrame, force_slug: str) -> nx.Graph:
    area_crime = build_area_crime_network(force_data, force_slug)
    crime_outcome = build_crime_outcome_network(force_data, force_slug)
    graph = nx.compose(area_crime, crime_outcome)
    graph.graph.update(force=force_slug, layer="combined_multilayer")
    return graph


def build_all_networks(data: pd.DataFrame, force_order: list[str]) -> dict[str, dict[str, nx.Graph]]:
    networks: dict[str, dict[str, nx.Graph]] = {}
    for force_slug in force_order:
        force_data = data[data["force_slug"] == force_slug].copy()
        networks[force_slug] = {
            "area_crime": build_area_crime_network(force_data, force_slug),
            "crime_outcome": build_crime_outcome_network(force_data, force_slug),
            "combined": build_multilayer_network(force_data, force_slug),
        }
    return networks


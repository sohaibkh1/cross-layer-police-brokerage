from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analysis import (
    compute_brokerage_score,
    compute_brokerage_validation,
    compute_centrality,
    compute_network_stats,
    compute_outcome_comparison,
    compute_similarity_network,
    create_data_audit,
    write_data_audit_markdown,
    write_results_summary,
)
from .config import (
    FIGURES_DIR,
    FORCE_ORDER,
    FORCES,
    MONTHS,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    TABLES_DIR,
    ensure_directories,
)
from .data_loading import clean_police_data, download_police_data, load_force_data
from .network_building import build_all_networks
from .plotting import (
    plot_brokerage_heatmap,
    plot_centrality_comparison,
    plot_data_overview,
    plot_outcome_heatmap,
    plot_similarity_network,
)


def run_pipeline(
    download: bool = True,
    force_download: bool = False,
    max_wait_seconds: int = 1800,
) -> dict[str, Path]:
    ensure_directories()

    if download:
        zip_path = download_police_data(
            raw_dir=RAW_DIR,
            months=MONTHS,
            forces=FORCES,
            force_download=force_download,
            max_wait_seconds=max_wait_seconds,
        )
    else:
        zip_path = None

    raw = load_force_data(RAW_DIR, months=MONTHS, forces=FORCE_ORDER)
    if raw.empty:
        raise RuntimeError(
            "No street-level CSV data was found. Run with download=True or place police CSV/ZIP files in data/raw."
        )

    cleaned = clean_police_data(raw)
    processed_path = PROCESSED_DIR / "processed_crime_outcomes.csv"
    cleaned.to_csv(processed_path, index=False)

    audit = create_data_audit(cleaned)
    audit_csv_path = OUTPUTS_DIR / "data_audit.csv"
    audit_md_path = OUTPUTS_DIR / "data_audit.md"
    audit.to_csv(audit_csv_path, index=False)
    write_data_audit_markdown(cleaned, audit, audit_md_path)

    networks = build_all_networks(cleaned, FORCE_ORDER)
    network_summary_path = TABLES_DIR / "network_summary.csv"
    centrality_path = TABLES_DIR / "top_crime_centrality.csv"
    outcome_path = TABLES_DIR / "outcome_comparison.csv"
    brokerage_validation_path = TABLES_DIR / "brokerage_validation.csv"
    similarity_edges_path = TABLES_DIR / "crime_similarity_edges.csv"
    similarity_nodes_path = TABLES_DIR / "crime_similarity_nodes.csv"

    network_summary = compute_network_stats(cleaned, networks)
    outcome_comparison = compute_outcome_comparison(cleaned)

    # Betweenness centrality is the expensive step. Cache the table so the notebook
    # can run reproducibly without recomputing it every time. Delete the CSV to force
    # a fresh centrality run after changing the graph construction.
    if centrality_path.exists():
        centrality = pd.read_csv(centrality_path)
        required_cols = {
            "force_slug",
            "crime_type",
            "betweenness",
            "betweenness_rank",
            "pagerank",
            "pagerank_rank",
            "combined_strength",
            "crime_outcome_strength",
            "brokerage_eligible",
        }
        if not required_cols.issubset(set(centrality.columns)):
            centrality = compute_centrality(networks)
    else:
        centrality = compute_centrality(networks)

    centrality = compute_brokerage_score(cleaned, centrality, outcome_comparison)
    brokerage_validation = compute_brokerage_validation(centrality)
    similarity_edges, similarity_nodes = compute_similarity_network(outcome_comparison, top_k=3)

    network_summary.to_csv(network_summary_path, index=False)
    centrality.to_csv(centrality_path, index=False)
    outcome_comparison.to_csv(outcome_path, index=False)
    brokerage_validation.to_csv(brokerage_validation_path, index=False)
    similarity_edges.to_csv(similarity_edges_path, index=False)
    similarity_nodes.to_csv(similarity_nodes_path, index=False)

    plot_paths = [
        plot_data_overview(cleaned, FIGURES_DIR),
        plot_brokerage_heatmap(centrality, FIGURES_DIR),
        plot_similarity_network(similarity_edges, similarity_nodes, FIGURES_DIR),
        plot_centrality_comparison(centrality, FIGURES_DIR),
        plot_outcome_heatmap(outcome_comparison, centrality, FIGURES_DIR),
    ]

    results_summary_path = OUTPUTS_DIR / "results_summary.md"
    write_results_summary(
        cleaned,
        network_summary,
        centrality,
        outcome_comparison,
        results_summary_path,
    )

    return {
        "zip_path": zip_path,
        "processed_data": processed_path,
        "data_audit_csv": audit_csv_path,
        "data_audit_md": audit_md_path,
        "network_summary": network_summary_path,
        "top_crime_centrality": centrality_path,
        "outcome_comparison": outcome_path,
        "brokerage_validation": brokerage_validation_path,
        "crime_similarity_edges": similarity_edges_path,
        "crime_similarity_nodes": similarity_nodes_path,
        "results_summary": results_summary_path,
        **{f"figure_{idx}": path for idx, path in enumerate(plot_paths, start=1)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ECMM447 CW2 police network analysis.")
    parser.add_argument("--skip-download", action="store_true", help="Use files already in data/raw.")
    parser.add_argument("--force-download", action="store_true", help="Regenerate and redownload the data ZIP.")
    parser.add_argument(
        "--max-wait-seconds",
        type=int,
        default=1800,
        help="Maximum time to wait for the custom data download to be generated.",
    )
    args = parser.parse_args()

    outputs = run_pipeline(
        download=not args.skip_download,
        force_download=args.force_download,
        max_wait_seconds=args.max_wait_seconds,
    )
    print("Analysis complete. Outputs:")
    for name, path in outputs.items():
        if path:
            print(f"- {name}: {path}")


if __name__ == "__main__":
    main()


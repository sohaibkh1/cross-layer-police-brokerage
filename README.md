# Cross-layer Brokerage in Police Recorded Crime Networks

This project analyses how recorded crime categories connect local areas with police outcome categories across three English and Welsh police forces. It uses a weighted multilayer network structure where crime type acts as the shared bridge between area nodes and outcome nodes.

## Core Question

Which recorded crime categories act as cross-layer brokers between Lower Layer Super Output Areas (LSOAs) and recorded police outcomes, and how consistent are these brokerage roles across Metropolitan Police Service, West Midlands Police and South Wales Police?

## Data

Source: UK Police Open Data, <https://data.police.uk/data/>.

Scope:

- Metropolitan Police Service
- West Midlands Police
- South Wales Police
- November 2025 to April 2026
- Street-level crime CSV files only
- `Last outcome category` is used as the recorded outcome variable

Excluded: stop-and-search, British Transport Police, PSNI, Scotland, and whole-UK aggregation.

The raw custom ZIP is expected at `data/raw/`. The processed CSV is regenerated locally by the analysis pipeline and is not shipped.

Before running for the first time, confirm that this file exists:

```text
data/raw/police_custom_2025-11_2026-04_metropolitan_south-wales_west-midlands_street.zip
```

## How to Run

From the project root:

```bash
pip install -r requirements.txt
python -m src.run_analysis --skip-download
```

Tested with Python 3.10 and 3.11.

To regenerate the custom data download from data.police.uk:

```bash
python -m src.run_analysis
```

Set `RUN_DOWNLOAD = False` in the analysis notebook if the ZIP is already present in `data/raw`.

## Reproducibility

Approximate weighted-distance betweenness on the Metropolitan graph is the slowest step in the pipeline. To make repeated notebook runs fast, `run_analysis.py` caches `outputs/tables/top_crime_centrality.csv` and reuses it on subsequent runs if the required columns are present. All other tables and figures are regenerated on every run.

For a fully fresh end-to-end recomputation of centrality, delete the cached table first:

```bash
rm -f outputs/tables/top_crime_centrality.csv
python -m src.run_analysis --skip-download
```

The betweenness computation uses a fixed random seed and `k=250` sampled source nodes on the two larger graphs, so a fresh run reproduces the same values.

## Main Outputs

- `outputs/data_audit.md`
- `outputs/data_audit.csv`
- `outputs/tables/network_summary.csv`
- `outputs/tables/top_crime_centrality.csv`
- `outputs/tables/brokerage_validation.csv`
- `outputs/tables/outcome_comparison.csv`
- `outputs/tables/crime_similarity_edges.csv`
- `outputs/tables/crime_similarity_nodes.csv`
- `outputs/figures/fig1_data_overview.png`
- `outputs/figures/fig2_brokerage_comparison.png`
- `outputs/figures/fig3_similarity_networks.png`
- `outputs/figures/fig4_centrality_comparison.png`
- `outputs/figures/figS1_outcome_heatmap.png`
- `outputs/results_summary.md`

## Methods

For each force, the code builds:

- an area-crime weighted bipartite layer
- a crime-outcome weighted bipartite layer
- a combined typed multilayer graph where crime type is the shared mediator

The main analysis uses a four-component cross-layer brokerage score: area spread, outcome connectivity, outcome entropy, and weighted-distance betweenness. A crime-type outcome-profile similarity network is then built as a one-mode projection of the crime-outcome bipartite layer using cosine similarity and greedy modularity community detection.

Descriptive validation uses Spearman rank correlation to compare brokerage with raw crime volume and to compare brokerage score consistency across forces. As a robustness check, PageRank centrality is computed on the combined graph and its ranking compared with betweenness ranking.

## Key Limitations

- The data is police-recorded crime, not all actual crime.
- Published locations are approximate and anonymised.
- Outcome categories may be missing or delayed.
- Forces differ in population, geography, and recording context.
- The analysis is descriptive and does not claim causality, police bias, or police effectiveness/failure.

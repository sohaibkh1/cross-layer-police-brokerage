# Data notes

This project uses UK Police Open Data from <https://data.police.uk/data/>.

Target scope:

- Metropolitan Police Service (`metropolitan`)
- West Midlands Police (`west-midlands`)
- South Wales Police (`south-wales`)
- Latest six months listed on the site when built: November 2025 to April 2026
- Street-level crime CSV files only

The analysis uses the street-level CSV field `Last outcome category` as the recorded outcome category. Stop-and-search data, British Transport Police, PSNI, Scotland, and whole-UK downloads are deliberately excluded.

To regenerate the raw data, run:

```bash
python -m src.run_analysis
```

If the custom data download fails, manually use <https://data.police.uk/data/> to generate a file with:

- date range: November 2025 to April 2026
- forces: Metropolitan Police Service, West Midlands Police, South Wales Police
- data sets: include crime data only

Place the resulting ZIP in `data/raw/` and then run:

```bash
python -m src.run_analysis --skip-download
```


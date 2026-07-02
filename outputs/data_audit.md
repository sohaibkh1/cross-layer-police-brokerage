# Data audit

Source: UK Police Open Data street-level crime CSV files from data.police.uk.

## Scope

- Forces: Metropolitan Police Service, West Midlands Police, South Wales Police.
- Months: 2025-11, 2025-12, 2026-01, 2026-02, 2026-03, 2026-04.
- Dataset type: street-level crime data; the street CSV `Last outcome category` field is used as the outcome variable.
- Stop-and-search, PSNI, Scotland, and British Transport Police are excluded.

## Compatibility checks

- Crime category labels identical across the three forces: yes.
- Outcome category labels identical across the three forces: no.
- Local area fields checked: `LSOA code` and `LSOA name`.

### Outcome label differences

- Metropolitan Police Service missing vs union: []
- West Midlands Police missing vs union: ['Offender given penalty notice']
- South Wales Police missing vs union: ['Further action is not in the public interest', 'Offender given penalty notice']

## Records and missing values

| section | force | force_slug | month | field | category | count | percent | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| records | Metropolitan Police Service | metropolitan | all | records | total | 540963 | 100.0 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | crime_id | missing | 105626 | 19.526 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | crime_type | missing | 0 | 0.0 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | outcome_category | missing | 105626 | 19.526 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | lsoa_code | missing | 0 | 0.0 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | lsoa_name | missing | 0 | 0.0 |  |
| missing_values | Metropolitan Police Service | metropolitan | all | month | missing | 0 | 0.0 |  |
| unique_counts | Metropolitan Police Service | metropolitan | all | crime_type | unique_crime_types | 14 |  |  |
| unique_counts | Metropolitan Police Service | metropolitan | all | outcome_category | unique_outcomes | 13 |  |  |
| unique_counts | Metropolitan Police Service | metropolitan | all | lsoa_code | unique_lsoas | 7115 |  |  |
| records | West Midlands Police | west-midlands | all | records | total | 152098 | 100.0 |  |
| missing_values | West Midlands Police | west-midlands | all | crime_id | missing | 4982 | 3.276 |  |
| missing_values | West Midlands Police | west-midlands | all | crime_type | missing | 0 | 0.0 |  |
| missing_values | West Midlands Police | west-midlands | all | outcome_category | missing | 4982 | 3.276 |  |
| missing_values | West Midlands Police | west-midlands | all | lsoa_code | missing | 0 | 0.0 |  |
| missing_values | West Midlands Police | west-midlands | all | lsoa_name | missing | 0 | 0.0 |  |
| missing_values | West Midlands Police | west-midlands | all | month | missing | 0 | 0.0 |  |
| unique_counts | West Midlands Police | west-midlands | all | crime_type | unique_crime_types | 14 |  |  |
| unique_counts | West Midlands Police | west-midlands | all | outcome_category | unique_outcomes | 12 |  |  |
| unique_counts | West Midlands Police | west-midlands | all | lsoa_code | unique_lsoas | 1750 |  |  |
| records | South Wales Police | south-wales | all | records | total | 59031 | 100.0 |  |
| missing_values | South Wales Police | south-wales | all | crime_id | missing | 6414 | 10.865 |  |
| missing_values | South Wales Police | south-wales | all | crime_type | missing | 0 | 0.0 |  |
| missing_values | South Wales Police | south-wales | all | outcome_category | missing | 6414 | 10.865 |  |
| missing_values | South Wales Police | south-wales | all | lsoa_code | missing | 1365 | 2.312 |  |
| missing_values | South Wales Police | south-wales | all | lsoa_name | missing | 1365 | 2.312 |  |
| missing_values | South Wales Police | south-wales | all | month | missing | 0 | 0.0 |  |
| unique_counts | South Wales Police | south-wales | all | crime_type | unique_crime_types | 14 |  |  |
| unique_counts | South Wales Police | south-wales | all | outcome_category | unique_outcomes | 11 |  |  |
| unique_counts | South Wales Police | south-wales | all | lsoa_code | unique_lsoas | 927 |  |  |

## Decision

All three selected forces are retained if the table above shows comparable crime and outcome labels and usable LSOA fields. Missing outcomes and missing LSOAs are counted here; records with missing LSOA are not used for the area-crime layer, and records with missing outcomes are not used for the crime-outcome layer.

# Results summary

Months analysed: 2025-11, 2025-12, 2026-01, 2026-02, 2026-03, 2026-04.
Total records after basic cleaning: 752,092.

## Records by force

| force | force_slug | records |
| --- | --- | --- |
| Metropolitan Police Service | metropolitan | 540963 |
| South Wales Police | south-wales | 59031 |
| West Midlands Police | west-midlands | 152098 |

## Network summary

| force | force_slug | layer | records | records_with_lsoa | records_with_outcome | areas | crime_types | outcomes | nodes | edges | density | total_edge_weight | average_weighted_degree |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Metropolitan Police Service | metropolitan | area_crime | 540963 | 540963 | 435337 | 7115 | 14 | 13 | 7129 | 56195 | 0.5641501857243248 | 540963.0 | 151.7640622808248 |
| Metropolitan Police Service | metropolitan | crime_outcome | 540963 | 540963 | 435337 | 7115 | 14 | 13 | 26 | 148 | 0.8757396449704142 | 435337.0 | 33487.46153846154 |
| Metropolitan Police Service | metropolitan | combined | 540963 | 540963 | 435337 | 7115 | 14 | 13 | 7142 | 56343 | 0.002209485135415522 | 976300.0 | 273.39680761691403 |
| West Midlands Police | west-midlands | area_crime | 152098 | 152098 | 147116 | 1750 | 14 | 12 | 1764 | 17281 | 0.7053469387755102 | 152098.0 | 172.4467120181406 |
| West Midlands Police | west-midlands | crime_outcome | 152098 | 152098 | 147116 | 1750 | 14 | 12 | 25 | 117 | 0.75 | 147116.0 | 11769.28 |
| West Midlands Police | west-midlands | combined | 152098 | 152098 | 147116 | 1750 | 14 | 12 | 1776 | 17398 | 0.011037939347798502 | 299214.0 | 336.9527027027027 |
| South Wales Police | south-wales | area_crime | 59031 | 57666 | 52617 | 927 | 14 | 11 | 941 | 7573 | 0.5835259670211127 | 57666.0 | 122.56323060573858 |
| South Wales Police | south-wales | crime_outcome | 59031 | 57666 | 52617 | 927 | 14 | 11 | 24 | 112 | 0.7832167832167832 | 52617.0 | 4384.75 |
| South Wales Police | south-wales | combined | 59031 | 57666 | 52617 | 927 | 14 | 11 | 952 | 7685 | 0.016976822274651186 | 110283.0 | 231.68697478991598 |

## Top cross-layer broker crime types

| force | crime_type | brokerage_rank | brokerage_score | area_spread | outcome_connectivity | outcome_entropy_norm | betweenness | betweenness_method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Metropolitan Police Service | Violence and sexual offences | 1.0 | 0.9230769230769231 | 0.9045678144764582 | 1.0 | 0.5366629924785444 | 0.8667098039215687 | approx_weighted_distance_k250 |
| Metropolitan Police Service | Drugs | 2.0 | 0.6634615384615384 | 0.6068868587491216 | 0.9230769230769231 | 0.650349134855397 | 0.0218725490196078 | approx_weighted_distance_k250 |
| Metropolitan Police Service | Other crime | 3.0 | 0.6442307692307693 | 0.4247364722417428 | 0.9230769230769231 | 0.6843660213549169 | 0.0309182072829131 | approx_weighted_distance_k250 |
| Metropolitan Police Service | Other theft | 3.0 | 0.6442307692307693 | 0.7072382290934646 | 0.9230769230769231 | 0.31383567989138794 | 0.0709844982169574 | approx_weighted_distance_k250 |
| Metropolitan Police Service | Public order | 5.0 | 0.625 | 0.6366830639494027 | 0.9230769230769231 | 0.5553324484132955 | 0.0118862745098039 | approx_weighted_distance_k250 |
| Metropolitan Police Service | Vehicle crime | 5.0 | 0.625 | 0.7149683766690091 | 0.9230769230769231 | 0.20038287552587017 | 0.0878585434173669 | approx_weighted_distance_k250 |
| South Wales Police | Violence and sexual offences | 1.0 | 0.8557692307692308 | 0.9590075512405609 | 0.9090909090909091 | 0.5802630726359558 | 0.9855640104276756 | approx_weighted_distance_k250 |
| South Wales Police | Drugs | 2.0 | 0.7403846153846154 | 0.593311758360302 | 0.9090909090909091 | 0.7134344146877681 | 0.0373621052631578 | approx_weighted_distance_k250 |
| South Wales Police | Public order | 2.0 | 0.7403846153846154 | 0.8554476806903991 | 0.9090909090909091 | 0.5749127469457493 | 0.0112661170999788 | approx_weighted_distance_k250 |
| South Wales Police | Shoplifting | 4.0 | 0.7115384615384615 | 0.4023732470334412 | 1.0 | 0.556771875051026 | 0.0756484210526315 | approx_weighted_distance_k250 |
| South Wales Police | Other crime | 5.0 | 0.6826923076923077 | 0.6709816612729234 | 0.9090909090909091 | 0.7079803622756223 | 0.0084287719298245 | approx_weighted_distance_k250 |
| West Midlands Police | Violence and sexual offences | 1.0 | 0.875 | 0.9942857142857143 | 0.9166666666666666 | 0.5298960263685539 | 0.9896021515600169 | approx_weighted_distance_k250 |
| West Midlands Police | Drugs | 2.0 | 0.673076923076923 | 0.6851428571428572 | 0.9166666666666666 | 0.5872881189823176 | 0.0005636978579481 | approx_weighted_distance_k250 |
| West Midlands Police | Criminal damage and arson | 3.0 | 0.6634615384615384 | 0.9434285714285714 | 0.8333333333333334 | 0.5101919547885677 | 0.0039492671927846 | approx_weighted_distance_k250 |
| West Midlands Police | Public order | 3.0 | 0.6634615384615384 | 0.8645714285714285 | 0.8333333333333334 | 0.5741044482105171 | 0.0011285231116121 | approx_weighted_distance_k250 |
| West Midlands Police | Other crime | 5.0 | 0.6538461538461539 | 0.7062857142857143 | 0.8333333333333334 | 0.6256211083614932 | 0.0005636978579481 | approx_weighted_distance_k250 |

## Largest outcome categories by force

| force | force_slug | outcome_category | count |
| --- | --- | --- | --- |
| Metropolitan Police Service | metropolitan | Investigation complete; no suspect identified | 202056 |
| Metropolitan Police Service | metropolitan | Under investigation | 97949 |
| Metropolitan Police Service | metropolitan | Unable to prosecute suspect | 93648 |
| Metropolitan Police Service | metropolitan | Awaiting court outcome | 20554 |
| Metropolitan Police Service | metropolitan | Status update unavailable | 8764 |
| Metropolitan Police Service | metropolitan | Local resolution | 7033 |
| South Wales Police | south-wales | Unable to prosecute suspect | 16878 |
| South Wales Police | south-wales | Investigation complete; no suspect identified | 14921 |
| South Wales Police | south-wales | Under investigation | 12822 |
| South Wales Police | south-wales | Awaiting court outcome | 5059 |
| South Wales Police | south-wales | Status update unavailable | 951 |
| South Wales Police | south-wales | Local resolution | 912 |
| West Midlands Police | west-midlands | Unable to prosecute suspect | 52789 |
| West Midlands Police | west-midlands | Investigation complete; no suspect identified | 49694 |
| West Midlands Police | west-midlands | Under investigation | 24533 |
| West Midlands Police | west-midlands | Awaiting court outcome | 11756 |
| West Midlands Police | west-midlands | Local resolution | 5033 |
| West Midlands Police | west-midlands | Action to be taken by another organisation | 1266 |

# Screenshots

Images referenced by the main README. Naming pattern: `tool-NN-slug.png` — the
number controls the order in the README. To add one, drop it here and add a
matching row to the Screenshots section of the root `README.md`.

| File | What it shows |
|---|---|
| `airflow-01-dags-daily.png` | Airflow DAG list — daily listings/quotes fetch → parse → load |
| `airflow-02-dags-weekly-monthly.png` | Weekly categories and monthly map-info chains |
| `airflow-03-dags-dbt-dq.png` | dbt transformation DAGs and the Soda data-quality check |
| `superset-01-market-overview.png` | Market cap, 24h volume, BTC dominance, top-10 share |
| `superset-02-sectors.png` | Sector treemap and per-sector performance change |
| `superset-03-momentum.png` | Rank gainers & losers, volatility top-20 |
| `superset-04-coin-explorer.png` | Top-100 table with 1h/24h/7d/30d change |
| `superset-05-coin-explorer-detail.png` | MC vs. volume scatter, FDV/MC, supply utilisation |
| `grafana-01-freshness-quality.png` | Table freshness, duplicate check, row count per day |
| `grafana-02-completeness-volume.png` | Missing %, row count expected vs. inserted, freshness SLA |
| `grafana-03-dag-status.png` | Per-DAG max run duration |
| `ci-01-github-actions-ci.png` | Green CI workflow runs |
| `ci-02-github-actions-cd.png` | Green CD (deploy to server) workflow runs |

Architecture diagrams (not screenshots, but referenced from the same folder):

| File | What it shows |
|---|---|
| `cmc_overall_architecture.png` | End-to-end system architecture |
| `cmc_elt_architecture_diagram.png` | ELT flow: API → JSON → CSV → staging → dbt marts |
| `cmc_dwh_modeling_diagram.png` | Warehouse star-schema model |

Take these **while the VPS is still running** — once it is decommissioned the
live UIs are gone, but the screenshots keep the project presentable.

Tips:

- Capture at a wide window size (1600px or more) so text stays readable.
- Crop out the browser chrome and anything containing tokens or hostnames.
- Dismiss OS notifications (the Windows Snipping Tool toast especially) before capturing — it lands in the bottom-right corner and covers a panel.
- PNG for UI screenshots; keep each file under ~500KB.

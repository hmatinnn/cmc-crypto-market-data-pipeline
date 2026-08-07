"""Airflow DAG import check (for CI).

This script runs inside the real airflow image. DagBag parses the whole dags/
folder; if any DAG file has a syntax error, a broken import or a bad argument,
it is caught here and CI turns red.

Usage:
    python /opt/ci/check_dags.py
"""

from __future__ import annotations

import sys

DAGS_FOLDER = "/opt/airflow/dags"


def main() -> int:
    try:
        from airflow.models.dagbag import DagBag
    except ImportError:  # Airflow 2.x backwards compatibility
        from airflow.models import DagBag  # type: ignore[no-redef]

    dagbag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)

    if dagbag.import_errors:
        print("\nDAG IMPORT ERRORS:\n" + "=" * 60)
        for filename, error in dagbag.import_errors.items():
            print(f"\n--- {filename} ---\n{error}")
        print("=" * 60)
        print(f"\n{len(dagbag.import_errors)} file(s) failed to parse.")
        return 1

    dag_ids = sorted(dagbag.dag_ids)
    if not dag_ids:
        print("ERROR: no DAGs found - is the dags/ folder empty or not mounted?")
        return 1

    print(f"{len(dag_ids)} DAG(s) parsed successfully:")
    for dag_id in dag_ids:
        print(f"  - {dag_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

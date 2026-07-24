"""Runs `dbt run --select <models>` against the cmc_pipeline dbt project.

Uses dbt-core's official in-process API (dbtRunner) instead of shelling out
to the `dbt` console-script via subprocess. subprocess.run(["dbt", ...])
failed in this project's Airflow containers with
`PermissionError: [Errno 13] Permission denied: 'dbt'` (the installed
console-script wasn't executable/resolvable for the airflow runtime user).
dbtRunner sidesteps that entirely -- it's a plain Python call within the
same interpreter, no external process, no PATH/exec-bit involved. See
https://docs.getdbt.com/reference/programmatic-invocations.

The `dbt` import is done lazily, inside run_dbt() rather than at module
level: this module gets imported whenever *any* process parses
dags/dbt_gsheet_pipeline_dag.py (scheduler, dag-processor, webserver -- not
just the worker that actually executes the task). If dbt isn't installed
in whichever process is doing the parsing, a module-level import turns into
a DAG Import Error that blocks the whole file from loading. Importing
inside the function means parsing only needs `run_dbt` to exist as a
callable; `dbt` only needs to be importable on the worker that runs it.
"""
import os


def run_dbt(select: str, target_path: str = "target") -> str:
    """target_path: distinct per calling DAG (e.g. 'target_daily') so that
    concurrent runs (daily/weekly/monthly can land in the same minute --
    e.g. the 1st of a month that's also a Sunday) don't race on the same
    target/ dir's manifest.json / partial-parse cache.
    """
    from dbt.cli.main import dbtRunner

    project_dir = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt_project")
    profiles_dir = os.getenv("DBT_PROFILES_DIR", project_dir)

    args = [
        "run",
        "--project-dir", project_dir,
        "--profiles-dir", profiles_dir,
        "--target-path", target_path,
        "--select", *select.split(),
    ]
    print(f"Running: dbt {' '.join(args)}")

    result = dbtRunner().invoke(args)

    if not result.success:
        raise RuntimeError(
            f"dbt run failed for select={select!r}: {result.exception!r}"
        )

    return f"dbt run succeeded for select={select!r}"


if __name__ == "__main__":
    import sys
    run_dbt(" ".join(sys.argv[1:]) or "cmc_pipeline")

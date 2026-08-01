
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

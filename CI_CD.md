# CI/CD — setup and usage

This document describes the project's CI/CD setup: what is checked, where it runs, and how to configure it.

---

## 1. Overall flow

```
feature/* ──PR──> dev ──PR──> main ──> production server
              │           │        │
              │           │        └── CD: deploy over SSH
              │           └── CI: all checks
              └── CI: all checks
```

- **CI** (`.github/workflows/ci.yml`) — runs on every push and PR to `dev` and `main`.
- **CD** (`.github/workflows/cd.yml`) — triggered by the `workflow_run` event: it
  starts automatically once the **CI workflow finishes successfully on `main`**,
  and can also be started by hand via *Run workflow*.

> `workflow_run` only fires for the copy of `cd.yml` that lives on the **default
> branch**. Changes to CD therefore take effect only after they are merged into
> `main`.

---

## 2. What CI checks

| Job | What it does | What a failure means |
|---|---|---|
| **Lint (ruff)** | Checks `dags/`, `jobs/`, `pytest/` for syntax errors, undefined names, unused imports | Dead imports or a typo in the code |
| **Unit tests** | `pytest/` — 39 tests against a mocked CoinMarketCap API client | Business logic is broken |
| **dbt parse & compile** | Spins up an empty Postgres, parses and compiles every SQL model | Wrong `ref()`/`source()`, broken YAML, or a Jinja error |
| **Docker build & DAG import** | Builds 3 images (airflow, dbt, soda), then parses all DAGs inside the real airflow image | A Dockerfile is broken or a DAG has an import error |
| **Secret scan** | `gitleaks` scans the full git history and verifies `.env` is not tracked | An API key or password was committed |
| **CI OK** | Aggregates the results of all jobs above | — |

**Important:** in branch protection select only the **`CI OK`** job as a required check — the others feed into it.

---

## 3. Files added

```
.github/workflows/ci.yml          CI pipeline
.github/workflows/cd.yml          CD pipeline
ci/check_dags.py                  Airflow DAG import checker
deploy/deploy.sh                  Deploy script that runs on the server
ruff.toml                         Lint rules
pytest.ini                        Test configuration (+ 60s timeout)
requirements-dev.txt              CI/dev dependencies
.gitleaks.toml                    Secret scan rules and allowlist
.gitattributes                    Line ending normalization (LF)
.dockerignore                     Shrinks the Docker build context
dbt/cmc_pipeline/profiles.ci.yml  dbt profile for CI
```

---

## 4. Setup steps

### 4.1 Push the code

```bash
git add .github ci deploy ruff.toml pytest.ini requirements-dev.txt \
        .gitleaks.toml .gitattributes .dockerignore \
        dbt/cmc_pipeline/profiles.ci.yml CI_CD.md
git commit -m "ci: add GitHub Actions CI/CD pipeline"
git push origin dev
```

The first run will appear under the **Actions** tab on GitHub.

### 4.2 GitHub Secrets (CD only)

`Settings → Secrets and variables → Actions → New repository secret`:

| Secret | Example value | Description |
|---|---|---|
| `SSH_HOST` | `65.21.x.x` | Server IP or domain |
| `SSH_USER` | `matin` | SSH user |
| `SSH_PRIVATE_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | The **full** contents of the private key |
| `SSH_PORT` | `22` | Optional |
| `DEPLOY_PATH` | `/opt/coinmarket_pipeline_project` | Path to the repo on the server |

Creating an SSH key:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/gh_deploy -N ""
ssh-copy-id -i ~/.ssh/gh_deploy.pub USER@SERVER    # add the public key to the server
cat ~/.ssh/gh_deploy                                # paste this into SSH_PRIVATE_KEY
```

### 4.3 Prepare the server

```bash
ssh USER@SERVER
sudo mkdir -p /opt/coinmarket_pipeline_project
sudo chown $USER:$USER /opt/coinmarket_pipeline_project
git clone https://github.com/hmatinnn/cmc-crypto-market-data-pipeline.git /opt/coinmarket_pipeline_project
cd /opt/coinmarket_pipeline_project
cp .env.example .env && nano .env      # fill in the real values
chmod +x deploy/deploy.sh
./deploy/deploy.sh main                # verify the first deploy manually
```

### 4.4 Production environment (approval gate)

Create `Settings → Environments → New environment → "production"`.
Optionally add **Required reviewers** — then every deploy will wait for your approval.

### 4.5 Branch protection

`Settings → Branches → Add rule`:

- Branch name pattern: `main`
- ✅ Require a pull request before merging
- ✅ Require status checks to pass → select **`CI OK`**
- ✅ Require branches to be up to date before merging

Repeat the same rule for `dev` (without the approval requirement).

---

## 5. Day-to-day workflow

```bash
git checkout dev && git pull
git checkout -b feature/new-dag

# ... write code ...

# check locally before pushing (same commands as CI):
ruff check dags jobs pytest
pytest

git push origin feature/new-dag
# Open a PR on GitHub: feature/new-dag -> dev
# Merge once CI is green
# When ready: PR dev -> main  =>  automatic deploy
```

---

## 6. Existing issues fixed during this setup

1. **The test suite hung for 4 minutes.** `test_get_returns_none_on_http_error` triggered the retry path, which called the real `time.sleep(65)` five times (~260s). An autouse fixture was added to `pytest/conftest.py` making `time.sleep` a no-op in tests. All 39 tests now run in 1.2 seconds.
2. **6 dead imports** were removed (`jobs/cmc_api_pull.py`, `jobs/cmc_json_parse_to_csv.py`). The `sys` import was restored because tests monkeypatch `mod.sys.argv` (marked with `# noqa: F401`).
3. **The `.dockerignore` file was named `dockerignore`** (no leading dot), so Docker never read it and the build context included `.venv/` (243MB), `logs/` (74MB) and `api_responses_csv/` (115MB). It was recreated with the correct name.
4. **CRLF issue.** Files were stored with CRLF on Windows while the repo used LF, so `git diff` showed 30 files as "modified" even though the content was identical. `.gitattributes` normalizes this.

> After adding `.gitattributes`, run a one-time normalization:
> ```bash
> git add --renormalize .
> git commit -m "chore: normalize line endings to LF"
> ```

---

## 7. Developing on Windows, running on Linux

The project is developed on Windows but CI (`ubuntu-latest`) and the VPS both run Linux.
Four differences matter; all of them are now handled automatically.

| # | Difference | Symptom on the server | Handled by |
|---|---|---|---|
| 1 | **Line endings** — Windows writes CRLF, Linux expects LF | `/usr/bin/env: 'bash\r': No such file or directory` | `.gitattributes` (`eol=lf`) + a blocking CI check |
| 2 | **Executable bit** — Windows cannot store it, so `.sh` files land as mode 644 | `./deploy/deploy.sh: Permission denied` | CD calls `bash deploy/deploy.sh`; CI verifies the git mode is `100755` |
| 3 | **`AIRFLOW_UID`** — ignored on Windows, required on Linux for bind mounts | `logs/` owned by root, scheduler fails with `Permission denied` | `deploy.sh` sets it to `id -u` automatically |
| 4 | **Case sensitivity** — `Dockerfile` and `dockerfile` are one file on Windows, two on Linux | `failed to read dockerfile: no such file` | Checked — no collisions in this repo |

### Current state (verified)

Good news: `HEAD` in the repository **already stores LF**. Only your local working
tree has CRLF, which is why `git diff` showed 30 files as modified while their
content was identical. Nothing is broken on the server today — `.gitattributes`
simply locks this in so CRLF can never enter the repo.

After adding `.gitattributes` the phantom diff disappears on its own:

```
before: 30 files changed, 2374 insertions(+)
after:   9 files changed,  269 insertions(+)   <- only real changes
```

### One-time commands to run

```bash
# 1. Normalize line endings (safe - HEAD is already LF, so this is a no-op here)
git add --renormalize .

# 2. Mark shell scripts executable in the git index (Windows cannot do this itself)
git update-index --chmod=+x deploy/deploy.sh

# 3. The old misnamed file must be deleted
git rm --cached dockerignore   # if it is tracked
del dockerignore               # PowerShell / cmd
```

### Things to keep in mind

- **Never copy `.env` from Windows to the server via scp/WinSCP.** It carries CRLF
  and every value ends up with a trailing `\r` (an API key becomes `abc123\r` → 401).
  Write it directly on the server with `nano`. As a safety net `deploy.sh` strips
  CRLF from `.env` on every run.
- **Use forward slashes in Python code** or `os.path.join` — the existing code
  already does this correctly.
- **Never test only on Windows.** CI runs on `ubuntu-latest`, which is exactly why
  it catches Linux-only problems before they reach the server.

---

## 8. Decommissioning the server

The VPS is temporary. Once it is cancelled, CD can no longer reach it and every
push to `main` would leave a red ✗ on a public repository. Do this before
shutting the server down.

### 8.1 Capture the evidence first

Once the server is gone the live UIs are gone with it. While it is still
running, save the screenshots listed in `docs/screenshots/README.md`, then
un-comment the Screenshots section in the main README.

### 8.2 Stop CD from running automatically

Edit `.github/workflows/cd.yml` and remove the `workflow_run` trigger, keeping
only `workflow_dispatch`:

```yaml
on:
  workflow_dispatch:
    inputs:
      ref:
        description: "Branch/tag to deploy (default: main)"
        required: false
        default: main
```

The workflow stays visible in the repository — it still demonstrates the
deployment design — but it never fires on its own, so CI stays the only thing
gating `main`.

### 8.3 Remove the credentials

- `Settings → Secrets and variables → Actions`: delete `SSH_HOST`, `SSH_USER`,
  `SSH_PRIVATE_KEY`, `DEPLOY_PATH` (and `SSH_PORT` if set).
- `Settings → Deploy keys`: delete the server's key.
- `Settings → Environments`: delete `production`.

### 8.4 What still works afterwards

CI is completely independent of the server: lint, 39 unit tests, dbt
parse/compile, Docker builds, the DAG import check and the secret scan all run
on GitHub-hosted runners. The badge stays green indefinitely.

The stack also remains reproducible locally for anyone who clones the repo —
see [Getting Started](README.md#getting-started).

---

## 9. Next steps (optional)

- **Add `dbt test` to CI** — this needs seed data (`dbt/cmc_pipeline/seeds/` is currently empty).
- **Run Soda data quality checks in CI** against sample data.
- **Image registry** — push images to GHCR and run `docker compose pull` on the server (build in CI instead of on the server; much faster deploys).
- **Staging environment** — deploy the `dev` branch to a separate server.
- **Dependabot** — automatic dependency updates via `.github/dependabot.yml`.

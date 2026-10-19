# GitLab CI/CD

This guide describes the GitLab pipeline of the dagster-dbt project.

- The pipeline checks the code, the dbt project and the Helm chart, and builds the Docker images.
- The images are stored in the GitLab Container Registry of the project.
- There is no deploy step yet (see section 6).

## 1. Files

- `.gitlab-ci.yml` in the repository root. GitLab reads only this file. It has one `include` that loads the real pipeline.
- `ci/gitlab/pipeline.yml` – the pipeline: stages, jobs, rules.
- `ci/gitlab/README.md` – this guide.

Edit `ci/gitlab/pipeline.yml`, not the root file.

## 2. How the pipeline works

A pipeline is one run of all checks for one commit. It has stages, and every stage has jobs.

- Stages run one after another: `lint` → `validate` → `build` → `scan`.
- Jobs in the same stage run at the same time.
- If a job fails, the next stages do not start.
- Every job runs in a new, empty container. GitLab clones the repository into it, runs the commands and deletes the container. Files from one job are not visible in another job, unless they are saved as `artifacts` or `cache`.

```
lint            validate                   build                        scan
────            ────────                   ─────                        ────
┌ ruff ┐        ┌ dbt-parse           ┐    ┌ build-dagster-user-code ┐    ┌ trivy-dagster-user-code
└ helm ┘ ──►    └ dagster-definitions ┘ ──► └ build-dbt-docs          ┘ ──► └ trivy-dbt-docs
```

### lint

- `ruff` – checks `app/` for real errors only: syntax errors, bad comparisons, `return`/`break` in the wrong place, undefined names (rules `E9,F63,F7,F82`). Style is not checked yet. It does not install the project dependencies, so it is fast.
- `helm` – runs `helm lint` for `ci/k8s/dagster-dbt-chart`, with `values.yaml` and with `values-dev.yaml`. It renders the templates and fails on errors in them.

### validate

- `dbt-parse` – runs `dbt parse` in `app/dbt/projects`. It checks the Jinja in models, `ref()`, macros and `dbt_project.yml`. It does not connect to the DWH and does not check the SQL itself. The DWH_* variables have fake values, because `profiles.yml` reads them with `env_var()` in every dbt command.
- `dagster-definitions` – runs `dagster definitions validate`. It loads `app/dagster_easy/definitions.py` like the user code server does: imports, repositories, jobs, assets, resources. It uses an empty `DAGSTER_HOME`, not `app/dagster_home/`, because that one needs the Dagster Postgres.

The Python jobs install `ci/docker/requirements.txt`. The pip downloads are cached. The cache is used again until `requirements.txt` changes.

### build

- `build-dagster-user-code` – builds `ci/docker/Dockerfile`.
- `build-dbt-docs` – builds `ci/docker/Dockerfile.dbt`.

The build runs in docker-in-docker: the job container has the `docker` client, and a second container (the `dind` service) runs the Docker daemon. The build context is the repository root, like in `ci/docker`. The images are pushed to the Container Registry.

### scan

- `trivy-dagster-user-code` – scans the `dagster-user-code` image.
- `trivy-dbt-docs` – scans the `dbt-docs-image` image.

Trivy pulls the image that the build pushed (`<short sha>` on `main`, `vX.Y.Z` on a release) and checks the system packages and the Python libraries for known vulnerabilities (CVE). It also looks for secrets in the image. It reports only `HIGH` and `CRITICAL` vulnerabilities that already have a fix (`--ignore-unfixed`).

The scan is in soft mode (`allow_failure: true`). If Trivy finds something, the job is orange and the pipeline stays green. Open the job log to see the list. Remove `allow_failure` when the images are clean, then new vulnerabilities block the pipeline.

## 3. When the pipeline runs

- Push to any branch – lint and validate.
- Push to `main` – lint, validate, build and scan.
- Tag `vX.Y.Z` (for example `v1.1.0`) – lint, validate, build and scan.
- Other tags – lint and validate.

The build and scan jobs use the most compute minutes, so they run only on `main` and on release tags.

The pipeline has no `workflow` block, so GitLab uses its default rules. They are right for pushing to `main`. If you start to work with merge requests, add the `workflow` rules from the GitLab template `Workflows/MergeRequest-Pipelines`. Without them, a push to a branch with an open merge request does not get a merge request pipeline.

## 4. Images and tags

The images are in Deploy → Container Registry:

```
registry.gitlab.com/personal-group3000342/dagster-dbt-docker/dagster-user-code:<tag>
registry.gitlab.com/personal-group3000342/dagster-dbt-docker/dbt-docs-image:<tag>
```

Tags:

- `main` – the last build of the `main` branch. It moves to the new image after every build.
- `<short sha>` – the build of one commit, for example `f9d5da2`. It never changes.
- `vX.Y.Z` – a release.

The build uses the `main` image as a layer cache (`--cache-from`). If `requirements.txt` did not change, only the `COPY app/` layer is built again. The first build has no cache and is slow.

The pipeline does not change `values.yaml`. The chart still uses the local names (`dagster-user-code:v1.0.0`), which kind takes from `kind load`. To use an image from the registry, set it at install time:

```bash
helm upgrade dagster-dbt ci/k8s/dagster-dbt-chart -n dagster-dbt \
  --set dagster.image=registry.gitlab.com/personal-group3000342/dagster-dbt-docker/dagster-user-code:v1.1.0 \
  --set dbt.image=registry.gitlab.com/personal-group3000342/dagster-dbt-docker/dbt-docs-image:v1.1.0
```

To pull an image to your machine:

```bash
docker login registry.gitlab.com     # user: GitLab login, password: personal access token with read_registry
docker pull registry.gitlab.com/personal-group3000342/dagster-dbt-docker/dagster-user-code:main
```

## 5. Daily work

### Make a release

```bash
git tag v1.1.0
git push origin v1.1.0
```

The tag goes to GitHub and GitLab. GitLab builds the images with the tag `v1.1.0`.

### Change the pipeline

Edit `ci/gitlab/pipeline.yml`. Before you push, check it in Build → Pipeline editor: it shows errors in the config and the full config after `include` (tab **Full configuration**).

### Run a job again

Open the pipeline in Build → Pipelines and click **Retry** on the job.

### Start a pipeline without a push

Build → Pipelines → **Run pipeline**, choose the branch.

## 6. What is not here yet

- **Deploy.** gitlab.com cannot reach the local kind cluster. The plan: a server with k3s, the GitLab Agent for Kubernetes in the cluster (it connects to GitLab by itself, so no ports are open), and a `deploy` stage with `helm upgrade --set ...:<tag>`.
- **Tests.** `dbt build --empty` and dbt unit tests on a temporary Postgres (a `services:` container, like `dind`), and pytest for the Python code. dbt data tests run in production, in Dagster, not in CI.
- **Merge request flow.** The `workflow` rules (section 3) and a protected `main`.

# Kubernetes (local kind cluster)
 
This guide shows how to run the dagster-dbt project in a local Kubernetes cluster.
 
The setup is close to a real production setup, but it runs on one laptop:
 
- The cluster is created with **kind** (Kubernetes inside Docker).
- The application is installed with a **Helm chart**.
- Every Dagster run is a separate Kubernetes Job (**K8sRunLauncher**). The pod is deleted 30 seconds after the run ends.
- Passwords for the cluster are not stored in the repository. This app reads them from **HashiCorp Vault**, and **External Secrets Operator** copies them into the cluster.
- The data warehouse (DWH) and Vault run **outside** the cluster, as separate Docker Compose projects.

Run all commands from the **root of the repository**, not from a subfolder.
 
## 1. What runs in the cluster
 
Inside the cluster (namespace `dagster-dbt`):
 
- Postgres (Dagster metadata database)
- Dagster webserver
- Dagster daemon (takes runs from the queue and creates a Job for each run)
- Dagster user code: one gRPC server (Deployment and Service `dagster-user-code-<name>`) for each code location
- dbt docs (web server) and a Job that builds the docs
- Run pods `dagster-run-<run_id>`. They exist only while a run works, plus 30 seconds.

External Secrets Operator runs in its own namespace, `external-secrets`.

### Code locations

The code locations are listed in `dagster.codeLocations` in `values.yaml`:

```yaml
codeLocations:
  - name: main
    module: dagster_easy.code_locations.main.definitions
  - name: test-examples
    module: dagster_easy.code_locations.test_examples.definitions
```

- `name` is the name of the location in the UI and a part of the Deployment and Service names (`dagster-user-code-main`).
- `module` is the Python module that the gRPC server loads (`dagster api grpc -m <module>`). It is the path of `definitions.py` inside `app/`, with dots instead of slashes.

The chart builds everything from this list: a Deployment and a Service for each location, and `workspace.yaml`, which tells the webserver and the daemon where the servers are. All servers listen on port 4000. They do not conflict, because each pod has its own IP address.

To add a code location:

1. Create `app/dagster_easy/code_locations/<name>/definitions.py`.
2. Add an entry to `dagster.codeLocations`.
3. Run `helm upgrade` and restart the webserver and the daemon (see "Change dagster.yaml or workspace.yaml").

A code location imports only its own package and `dagster_easy.shared`, never another location.

### How a run works

1. You start a job in the UI, or a schedule starts it. The run goes into the queue.
2. The daemon takes the run from the queue. `K8sRunLauncher` creates a Kubernetes Job `dagster-run-<run_id>`.
3. The run pod loads the code and runs all steps inside itself, in parallel processes (`multiprocess_executor`, up to 4 steps at a time).
4. The pod writes the run events to Postgres. You see them in the UI.
5. 30 seconds after the run ends, Kubernetes deletes the Job and its pod (`dagster.runLauncher.ttlSecondsAfterFinished`).

The executor is chosen by the env var `DAGSTER_BUILD_TYPE`. The chart sets it to `k8s`. Docker Compose sets it to `docker` and uses Celery.

The daemon and the webserver use the ServiceAccount `dagster`. Its Role allows only to create, read and delete Jobs and to read pods in the namespace `dagster-dbt` (`templates/dagster/rbac.yaml`).

The step output (stdout/stderr) is stored inside the run pod, so it is lost when the pod is deleted. The Dagster events stay in the UI.
 
## 2. Requirements
 
Install these tools on your machine:

- kind
- kubectl
- helm

Optional: k9s (a terminal UI for Kubernetes).
 
You also need two other Docker Compose projects, outside this repository:
 
- The DWH project. It creates the Docker network `data-platform-net`.
- The Vault project. It uses the Docker network `secrets-net`. Create it once with `docker network create secrets-net`.

## 3. Secrets that must exist
 
The app reads its secrets from Vault. It uses the KV version 2 engine, mounted at `secret/`. This guide does not explain how to install Vault.

The operator logs in to Vault with the AppRole `dagster-dbt`. This role can only read entries under `secret/dagster-dbt/`.
 
Create these two entries. The key names must be exactly the same, because the pods read them as environment variables.
 
- `secret/dagster-dbt/postgres-dagster`
  - `POSTGRES_HOST`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
- `secret/dagster-dbt/postgres-dwh`
  - `DWH_HOST`
  - `DWH_PORT`
  - `DWH_USER`
  - `DWH_PASSWORD`
  - `DWH_DB`

Important rules:
 
- `POSTGRES_HOST` is `postgres`. It is the name of the Postgres Service in the cluster.
- `DWH_HOST` must be the same as `dagster.dwh.host` in `values.yaml` (for example `dwh-postgres`).
- Every value must be a string. Write the port as `"5432"`.

Check the entries. The root token is in the Vault project folder (here `../vault`):
 
```bash
docker exec -e VAULT_TOKEN="$(cat ../vault/.vault/root.token)" vault vault kv list secret/dagster-dbt
```
 
You should see `postgres-dagster` and `postgres-dwh`.
 
## 4. First start from zero
 
Follow these steps in this order.
 
### Step 1. Start the external services
 
Start the DWH project and the Vault project. In each project folder:
 
```bash
docker compose up -d
```
 
Then check that the two secret entries exist (see section 3).
 
### Step 2. Check the paths
 
Needed only for dev.

Open `ci/k8s/kind/dev-1.yaml`. It has a `hostPath` that points to your projects folder on your computer. Set it to an absolute path on your machine:
 
```yaml
extraMounts:
  - hostPath: /home/<user>/projects
    containerPath: /mnt/projects
```
 
Then open `ci/k8s/dagster-dbt-chart/values-dev.yaml`. The value `dagster.hostPath.appPath` must be the path of the `app/` folder as the cluster node sees it. It starts with `/mnt/projects/`:
 
```yaml
dagster:
  hostPath:
    enabled: true
    appPath: /mnt/projects/dagster-dbt-docker/app
```
 
The whole projects folder is mounted. So if you move folders inside the repository, you only change `appPath`. You do not need a new cluster.
 
### Step 3. Create the cluster
 
```bash
kind create cluster --name dev-1 --config ci/k8s/kind/dev-1.yaml
```
 
Connect the cluster node to the two Docker networks. This lets the pods reach the DWH and Vault by name:
 
```bash
docker network connect data-platform-net dev-1-control-plane
docker network connect secrets-net dev-1-control-plane
```
 
The helper script `ci/k8s/kind/create_cluster.sh` can do these steps for you. If a connect command says "endpoint already exists", the node is already connected. This is not a problem.
 
If a cluster named `dev-1` already exists, `kind create cluster` fails and changes nothing. To create it again, delete it first with `kind delete cluster --name dev-1`.
 
Check the result:
 
```bash
kubectl get nodes
docker exec dev-1-control-plane getent hosts vault
```
 
The node must be `Ready`, and the second command must print an IP address.
 
### Step 4. Install External Secrets Operator
 
```bash
# If external-secrets is not added
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace --version 2.11.0
kubectl wait --for=condition=Available deployment --all \
  -n external-secrets --timeout=180s
```
 
Wait until all three pods are running before you go on. The operator has a webhook. If it is not ready, the next steps can fail.
 
Check:
 
```bash
kubectl get pods -n external-secrets
kubectl get crd | grep external-secrets.io
```
 
### Step 5. Create the namespace and the Vault AppRole Secret
 
The operator logs in to Vault with the AppRole `dagster-dbt`. The Vault project creates this role and saves its `role_id` and `secret_id` in `.vault/approle/dagster-dbt/`. Put them in a normal Kubernetes Secret. Do not save this Secret in git or in the Helm chart.
 
```bash
kubectl create namespace dagster-dbt
kubectl create secret generic vault-approle -n dagster-dbt \
  --from-file=role-id=../vault/.vault/approle/dagster-dbt/role_id \
  --from-file=secret-id=../vault/.vault/approle/dagster-dbt/secret_id
```
 
The paths expect the Vault project in `../vault`. Change them if it is in another folder.

If the Vault data is created again from zero, the role gets a new `role_id` and `secret_id`. Delete this Secret and create it again.
 
This one secret is the only thing you create by hand. It lets the operator read all the others.
 
### Step 6. Build and install

Run the commands from the repository root. The build context is the root (the `.` at the end of `docker build`).

#### Dev

The code is mounted from your disk, so code changes work without a new build.

```bash
docker build -t dagster-user-code:latest -f ci/docker/Dockerfile .
docker build -t dbt-docs-image:latest -f ci/docker/Dockerfile.dbt .
kind load docker-image dagster-user-code:latest dbt-docs-image:latest --name dev-1

helm install dagster-dbt ci/k8s/dagster-dbt-chart \
  -n dagster-dbt -f ci/k8s/dagster-dbt-chart/values-dev.yaml
```

Always add `-f ci/k8s/dagster-dbt-chart/values-dev.yaml`. Without it, you install prod.

Build again only when the Dockerfiles or the dependencies change.

#### Prod

The code is inside the images. After a code change, build the images with a new tag.

```bash
docker build -t dagster-user-code:v1.0.0 -f ci/docker/Dockerfile .
docker build -t dbt-docs-image:v1.0.0 -f ci/docker/Dockerfile.dbt .
kind load docker-image dagster-user-code:v1.0.0 dbt-docs-image:v1.0.0 --name dev-1

helm install dagster-dbt ci/k8s/dagster-dbt-chart -n dagster-dbt
```

The tag `v1.0.0` comes from `values.yaml`.

Check that the code comes from the image:

```bash
kubectl get deploy -n dagster-dbt -o yaml | grep -c hostPath    # 0
kubectl exec -n dagster-dbt deploy/dagster-user-code-main -- sh -c 'grep " /opt/dagster/app " /proc/mounts || echo "not mounted, code from image"'
```

Each run pod asks for 500m CPU and 1Gi memory. On a laptop, start the jobs one by one.

To switch between dev and prod, run `helm uninstall dagster-dbt -n dagster-dbt` and install again.

### Step 7. Check that everything works
 
```bash
kubectl get secretstore -n dagster-dbt
kubectl get externalsecret -n dagster-dbt
kubectl get pods -n dagster-dbt
kubectl get job -n dagster-dbt
```
 
What you should see:
 
- The SecretStore has status `Valid` and `READY True`.
- Both ExternalSecrets have status `SecretSynced`.
- All pods are `Running`.
- The Job `dbt-prepare` is `Complete`.

To check the run pods, start any job in the UI and watch:

```bash
kubectl get jobs,pods -n dagster-dbt
```

A Job `dagster-run-<run_id>` and its pod appear, and disappear 30 seconds after the run ends.

It is normal to see short errors in the first minutes:
 
- Some pods wait in `CreateContainerConfigError` until the Secrets are created. They start by themselves after a few seconds.
- The `dbt-docs` pod restarts until the Job `dbt-prepare` finishes.

### Step 8. Open the web interfaces
 
Run each command in a separate terminal:
 
```bash
kubectl port-forward -n dagster-dbt svc/dagster-webserver 3000:3000
kubectl port-forward -n dagster-dbt svc/dbt-docs 8001:8001
```
 
## 5. Values: base and dev
 
The chart has two values files.
 
- `values.yaml` is the base. It holds the production defaults: tagged image versions with the code inside, no code mounted from disk, bigger resources for run pods.
- `values-dev.yaml` holds only the differences for local work: `latest` image tags, the code mounted from your disk, smaller resources for run pods.

Helm puts `values-dev.yaml` on top of `values.yaml`. Dictionaries are merged key by key. Lists are replaced as a whole.
 
Useful commands:
 
```bash
helm get values dagster-dbt -n dagster-dbt          # values given by you
helm get values dagster-dbt -n dagster-dbt --all    # final values
helm get manifest dagster-dbt -n dagster-dbt        # what is installed now
```

See Step 6 for how to install dev and prod.

## 6. Daily work
 
### Change the chart or the values
 
Compare first, then upgrade:
 
```bash
helm get manifest dagster-dbt -n dagster-dbt > /tmp/current.yaml
helm template dagster-dbt ci/k8s/dagster-dbt-chart \
  -f ci/k8s/dagster-dbt-chart/values-dev.yaml > /tmp/new.yaml
diff /tmp/current.yaml /tmp/new.yaml
 
helm upgrade dagster-dbt ci/k8s/dagster-dbt-chart \
  -n dagster-dbt -f ci/k8s/dagster-dbt-chart/values-dev.yaml
```
 
The `diff` shows the Job `dbt-prepare` only in the new file. This is normal, because `helm get manifest` does not show hooks.
 
Every upgrade makes a new revision. You can go back:
 
```bash
helm history dagster-dbt -n dagster-dbt
helm rollback dagster-dbt <revision> -n dagster-dbt
```
 
### Change the Python code
 
The code is mounted from your disk, so you do not need to build the image. Every new run pod loads the code again, so you only need to restart the code servers. All of them have the label `component=dagster-user-code`:
 
```bash
kubectl rollout restart deployment -l component=dagster-user-code -n dagster-dbt
```

To restart only one code location, use its Deployment name, for example `deployment/dagster-user-code-test-examples`.

If the UI still shows an error for the code location after the restart, click **Reload** in **Deployment → Code locations**.
 
You must build and load the image again only when the dependencies change.

In production mode the code is in the image. After a code change, build the images with a new tag, load or push them, and set the new tag in `dagster.image` and `dbt.image`.
 
### Change dagster.yaml or workspace.yaml
 
For the cluster, these files live in `ci/k8s/dagster-dbt-chart/files/`. After you edit them, run `helm upgrade`. Then restart the pods that use them. The files are mounted with `subPath`, and Kubernetes does not update such files in running pods.
 
```bash
kubectl rollout restart deployment/dagster-webserver -n dagster-dbt
kubectl rollout restart deployment/dagster-daemon -n dagster-dbt
```

New run pods read `dagster.yaml` from the ConfigMap when they start, so they need no restart.
 
`files/dagster.yaml` is rendered by Helm (`tpl`), so it can use `{{ .Values... }}`. Docker Compose uses its own copy in `app/dagster_home/`. The two files are different on purpose: Compose uses `DefaultRunLauncher`, the cluster uses `K8sRunLauncher`. Keep the storage sections the same.
 
### Change a secret
 
External Secrets Operator reads Vault again after the refresh time (1 minute in dev, 1 hour in the base values). The Kubernetes Secret is updated. The running pods still use the old values, because environment variables are read only when a pod starts. Restart every pod that uses the secret:
 
```bash
kubectl rollout restart deployment -n dagster-dbt
kubectl rollout restart statefulset -n dagster-dbt
```
 
A new password for Postgres does not change the password inside the existing database. Postgres reads the user and password only when the disk is first created. Change the password inside the service too, or delete the disk.
 
### Look at logs and state
 
```bash
kubectl get pods -n dagster-dbt
kubectl logs -n dagster-dbt deploy/dagster-daemon --tail=50
kubectl get jobs -n dagster-dbt                       # run Jobs dagster-run-<run_id>
kubectl logs -n dagster-dbt job/dagster-run-<run_id>  # works only while the pod exists (30 s after the end)
kubectl describe pod <pod-name> -n dagster-dbt
kubectl get events -n dagster-dbt --sort-by=.lastTimestamp
```
 
### Stop and start the cluster
 
To pause the cluster and keep all data:
 
```bash
docker stop dev-1-control-plane
```
 
To continue:
 
```bash
docker start dev-1-control-plane
```
 
After you wake up your laptop, check these things before you work:
 
```bash
docker network inspect data-platform-net --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}'
docker network inspect secrets-net --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}'
kubectl get pods -n dagster-dbt
```
 
The DWH container, the Vault container and the cluster node must all be present in the networks. All pods must be `Running`.
 
## 7. Clean up
 
Remove the application, but keep the cluster:
 
```bash
helm uninstall dagster-dbt -n dagster-dbt
```
 
The Postgres disk stays after this command. To start with an empty database, delete it too:
 
```bash
kubectl delete pvc --all -n dagster-dbt
```
 
The Job `dbt-prepare` is a Helm hook. Helm does not remove hook resources on uninstall. Delete it by hand if you need to:
 
```bash
kubectl delete job dbt-prepare -n dagster-dbt --ignore-not-found
```
 
Remove the whole cluster (this deletes all data inside it, but not Vault and not the DWH):
 
```bash
kind delete cluster --name dev-1
```
 
After you create a new cluster, repeat the steps from section 4, starting with Step 3. You must connect the networks, load the images, install the operator, and create the Secret `vault-approle` again.
 
## 8. Troubleshooting
 
### A pod shows ErrImagePull or ImagePullBackOff for dagster-user-code, dagster-run-... or dbt-docs-image
 
The image is not in the node. Load it again (Step 6). This is common after you create a new cluster.
 
### The DWH name does not resolve, or `pg_isready` says "no response"
 
Check these things in order:
 
- The DWH Compose project is running (`docker ps`).
- The DWH container is in the network `data-platform-net`. If you recreated the DWH project, connect it again with `docker network connect data-platform-net <dwh-container>`.
- The cluster node is in the same network.
- `dagster.dwh.externalName` in `values.yaml` is the real name of the DWH container.
### The SecretStore is not Valid
 
Run `kubectl describe secretstore vault -n dagster-dbt`. Common reasons:
 
- The Secret `vault-approle` does not exist in the namespace `dagster-dbt`, or its `role-id` and `secret-id` are old. Create it again (Step 5).
- The Vault container is not running, or the node is not in the network `secrets-net`.
- The KV engine is not mounted at `secret/`.
### An ExternalSecret has an error
 
Run `kubectl describe externalsecret <name> -n dagster-dbt`. Common reasons:
 
- The entry or a key does not exist in Vault. Compare the paths in `externalSecrets.secrets` in `values.yaml` with section 3.
- A Secret with the same name already exists and belongs to something else.
To ask the operator to try again now:
 
```bash
kubectl annotate externalsecret <name> -n dagster-dbt force-sync=$(date +%s) --overwrite
```
 
### A pod shows CreateContainerConfigError
 
A Secret or a key is missing. Run `kubectl describe pod <pod-name> -n dagster-dbt` to see which one.
 
### Applying the chart fails with a webhook error
 
The External Secrets pods are not ready yet. Wait for them (Step 4) and try again.
 
### Dagster says an environment variable is not set
 
The pod does not have the Secret in its `envFrom` list, or it has not been restarted after the Secret changed. Check with:
 
```bash
kubectl exec -n dagster-dbt deploy/<name> -- env | grep -E "POSTGRES|DWH|DAGSTER"
```
 
### A run stays in STARTING or fails before the first step

- Check the daemon logs: `kubectl logs -n dagster-dbt deploy/dagster-daemon --tail=100`. The error `Forbidden` means that the RBAC from `templates/dagster/rbac.yaml` is missing, or the daemon does not use the ServiceAccount `dagster`.
- Check the run pod: `kubectl describe pod -n dagster-dbt -l job-name=dagster-run-<run_id>`. Common reasons are a missing image (Step 6) or a missing Secret.
- If the run pod does not start in 5 minutes, run monitoring marks the run as failed (`run_monitoring.start_timeout_seconds` in `files/dagster.yaml`).
 
### A pod stays in Terminating for a long time
 
The node is probably overloaded, for example after all pods restarted at the same time. Wait a little. If it does not finish, force the delete:
 
```bash
kubectl delete pod <pod-name> -n dagster-dbt --grace-period=0 --force
```
 
If the laptop is slow, lower `max_concurrent_runs` in `files/dagster.yaml` (how many run pods work at the same time) or `dagster.runLauncher.resources` in `values-dev.yaml`.

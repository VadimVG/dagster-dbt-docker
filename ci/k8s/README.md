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
- Dagster user code (gRPC server with the pipelines)
- dbt docs (web server) and a Job that builds the docs
- Run pods `dagster-run-<run_id>`. They exist only while a run works, plus 30 seconds.

External Secrets Operator runs in its own namespace, `external-secrets`.

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
- The Vault project. It creates the Docker network `secrets-net`.

## 3. Secrets that must exist
 
The app reads its secrets from Vault. It uses the KV version 2 engine, mounted at `secret/`. This guide does not explain how to install Vault.
 
Create these two entries. The key names must be exactly the same, because the pods read them as environment variables.
 
- `secret/dagster-dbt/postgres`
  - `POSTGRES_HOST`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DB`
- `secret/dagster-dbt/dwh`
  - `DWH_HOST`
  - `DWH_PORT`
  - `DWH_USER`
  - `DWH_PASSWORD`
  - `DWH_DB`

Important rules:
 
- `POSTGRES_HOST` is `postgres`. It is the name of the Postgres Service in the cluster.
- `DWH_HOST` must be the same as `dagster.dwh.host` in `values.yaml` (for example `dwh-postgres`).
- Every value must be a string. Write the port as `"5432"`.

If Vault runs in dev mode, it keeps data only in memory. After a restart of the Vault container, load the secrets again.
 
Check the entries:
 
```bash
docker exec vault vault kv list secret/dagster-dbt
```
 
You should see `dwh` and `postgres`.
 
## 4. First start from zero
 
Follow these steps in this order.
 
### Step 1. Start the external services
 
Start the DWH project and the Vault project. In each project folder:
 
```bash
docker compose up -d
```
 
Then check that the two secret entries exist (see section 3).
 
### Step 2. Check the paths
 
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
 
### Step 4. Build the images and load them into the cluster
 
The cluster cannot see images from your local Docker. You must load them into the node:
 
```bash
docker build -t dagster-user-code:latest -f ci/docker/Dockerfile ci/docker
docker build -t dbt-docs-image:latest -f ci/docker/Dockerfile.dbt ci/docker
kind load docker-image dagster-user-code:latest dbt-docs-image:latest --name dev-1
```
 
The build context is `ci/docker`, because `requirements.txt` is there. The app code is not copied into the images. In development it is mounted from your disk.
 
Do this again every time you create a new cluster. The images live inside the node, so they are lost when the cluster is deleted. Build again only if the Dockerfiles or the dependencies changed.
 
### Step 5. Install External Secrets Operator
 
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
 
### Step 6. Create the namespace and the Vault token
 
The operator needs a Vault token to read the secrets. Put it in a normal Kubernetes Secret. Do not save this Secret in git or in the Helm chart.
 
```bash
kubectl create namespace dagster-dbt
kubectl create secret generic vault-token -n dagster-dbt \
  --from-literal=token=<your-vault-token>
```
 
In Vault dev mode, the token is the value of `VAULT_DEV_ROOT_TOKEN_ID` from the Vault compose file.
 
This one secret is the only thing you create by hand. It opens the door to all the others.
 
### Step 7. Install the application
 
Check the chart first (optional but useful):
 
```bash
helm lint ci/k8s/dagster-dbt-chart -f ci/k8s/dagster-dbt-chart/values-dev.yaml
helm template dagster-dbt ci/k8s/dagster-dbt-chart \
  -f ci/k8s/dagster-dbt-chart/values-dev.yaml | less
```
 
Install:
 
```bash
helm install dagster-dbt ci/k8s/dagster-dbt-chart \
  -n dagster-dbt -f ci/k8s/dagster-dbt-chart/values-dev.yaml
```
 
Always add `-f ci/k8s/dagster-dbt-chart/values-dev.yaml` for local work. Without it, you get the base (production) values. In the base values the code is not mounted from your disk, so the pods have no code.
 
If you run these commands in a folder that does not contain `ci/`, Helm can say `repo ci not found`. It thinks that `ci/k8s/...` is the name of a chart repository. Go to the repository root and try again.
 
### Step 8. Check that everything works
 
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

### Step 9. Open the web interfaces
 
Run each command in a separate terminal:
 
```bash
kubectl port-forward -n dagster-dbt svc/dagster-webserver 3000:3000
kubectl port-forward -n dagster-dbt svc/dbt-docs 8001:8001
```
 
## 5. Values: base and dev
 
The chart has two values files.
 
- `values.yaml` is the base. It holds the production defaults: tagged image versions, no code mounted from disk, bigger resources for run pods.
- `values-dev.yaml` holds only the differences for local work: `latest` image tags, the code mounted from your disk, smaller resources for run pods.

Helm puts `values-dev.yaml` on top of `values.yaml`. Dictionaries are merged key by key. Lists are replaced as a whole.
 
Useful commands:
 
```bash
helm get values dagster-dbt -n dagster-dbt          # values given by you
helm get values dagster-dbt -n dagster-dbt --all    # final values
helm get manifest dagster-dbt -n dagster-dbt        # what is installed now
```
 
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
 
The code is mounted from your disk, so you do not need to build the image. Every new run pod loads the code again, so you only need to restart the code server:
 
```bash
kubectl rollout restart deployment/dagster-user-code -n dagster-dbt
```

If the UI still shows an error for the code location after the restart, click **Reload** in **Deployment → Code locations**.
 
You must build and load the image again only when the dependencies change.
 
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
 
After you create a new cluster, repeat the steps from section 4, starting with Step 3. You must connect the networks, load the images, install the operator, and create the token secret again.
 
## 8. Troubleshooting
 
### A pod shows ErrImagePull or ImagePullBackOff for dagster-user-code, dagster-run-... or dbt-docs-image
 
The image is not in the node. Load it again (Step 4). This is common after you create a new cluster.
 
### The DWH name does not resolve, or `pg_isready` says "no response"
 
Check these things in order:
 
- The DWH Compose project is running (`docker ps`).
- The DWH container is in the network `data-platform-net`. If you recreated the DWH project, connect it again with `docker network connect data-platform-net <dwh-container>`.
- The cluster node is in the same network.
- `dagster.dwh.externalName` in `values.yaml` is the real name of the DWH container.
### The SecretStore is not Valid
 
Run `kubectl describe secretstore vault -n dagster-dbt`. Common reasons:
 
- The Secret `vault-token` does not exist in the namespace `dagster-dbt`.
- The Vault container is not running, or the node is not in the network `secrets-net`.
- The KV engine is not mounted at `secret/`.
### An ExternalSecret has an error
 
Run `kubectl describe externalsecret <name> -n dagster-dbt`. Common reasons:
 
- The entry or a key does not exist in the secret store. Dev Vault loses its data after a restart, so load the secrets again.
- A Secret with the same name already exists and belongs to something else.
To ask the operator to try again now:
 
```bash
kubectl annotate externalsecret <name> -n dagster-dbt force-sync=$(date +%s) --overwrite
```
 
### A pod shows CreateContainerConfigError
 
A Secret or a key is missing. Run `kubectl describe pod <pod-name> -n dagster-dbt` to see which one.
 
### Applying the chart fails with a webhook error
 
The External Secrets pods are not ready yet. Wait for them (Step 5) and try again.
 
### Dagster says an environment variable is not set
 
The pod does not have the Secret in its `envFrom` list, or it has not been restarted after the Secret changed. Check with:
 
```bash
kubectl exec -n dagster-dbt deploy/<name> -- env | grep -E "POSTGRES|DWH|DAGSTER"
```
 
### A run stays in STARTING or fails before the first step

- Check the daemon logs: `kubectl logs -n dagster-dbt deploy/dagster-daemon --tail=100`. The error `Forbidden` means that the RBAC from `templates/dagster/rbac.yaml` is missing, or the daemon does not use the ServiceAccount `dagster`.
- Check the run pod: `kubectl describe pod -n dagster-dbt -l job-name=dagster-run-<run_id>`. Common reasons are a missing image (Step 4) or a missing Secret.
- If the run pod does not start in 5 minutes, run monitoring marks the run as failed (`run_monitoring.start_timeout_seconds` in `files/dagster.yaml`).
 
### A pod stays in Terminating for a long time
 
The node is probably overloaded, for example after all pods restarted at the same time. Wait a little. If it does not finish, force the delete:
 
```bash
kubectl delete pod <pod-name> -n dagster-dbt --grace-period=0 --force
```
 
If the laptop is slow, lower `max_concurrent_runs` in `files/dagster.yaml` (how many run pods work at the same time) or `dagster.runLauncher.resources` in `values-dev.yaml`.
